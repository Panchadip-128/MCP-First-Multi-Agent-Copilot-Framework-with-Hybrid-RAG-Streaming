"""
Model Context Protocol (MCP) implementation.

The MCP layer coordinates communication between:
- LLM models
- Tool agents
- RAG memory
- External plugins

It provides a standardized message format and routing mechanism.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from jsonschema import validate as jsonschema_validate, ValidationError
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from loguru import logger


class MessageType(str, Enum):
    """Types of messages in the MCP protocol."""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY_QUERY = "memory_query"
    MEMORY_RESULT = "memory_result"
    AGENT_MESSAGE = "agent_message"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MCPMessage(BaseModel):
    """Standard message format for MCP protocol."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    priority: MessagePriority = MessagePriority.NORMAL
    
    sender: str  # Agent/service that sent the message
    receiver: Optional[str] = None  # Target agent/service (None = broadcast)
    
    content: Dict[str, Any]  # Message payload
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Conversation context
    conversation_id: Optional[str] = None
    parent_message_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ToolCallRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    parameters: Dict[str, Any]
    timeout: Optional[float] = 30.0


class ToolCallResult(BaseModel):
    """Result from tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    handler: Any

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters_schema": self.parameters_schema,
        }


class MemoryQuery(BaseModel):
    """Query to the RAG memory system."""
    query_text: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None
    include_metadata: bool = True


class MemoryResult(BaseModel):
    """Result from memory query."""
    results: List[Dict[str, Any]]
    query_embedding: Optional[List[float]] = None
    total_found: int


class MCPProtocol:
    """
    Main MCP Protocol coordinator.
    
    Handles message routing, tool registration, and state management.
    """
    
    def __init__(self):
        self.registered_tools: Dict[str, "ToolSpec"] = {}
        self.registered_agents: Dict[str, Any] = {}
        self.message_history: List[MCPMessage] = []
        self.active_conversations: Dict[str, List[str]] = {}
        
        logger.info("MCP Protocol initialized")
    
    def create_message(
        self,
        message_type: MessageType,
        sender: str,
        content: Dict[str, Any],
        receiver: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        conversation_id: Optional[str] = None,
        parent_message_id: Optional[str] = None,
    ) -> MCPMessage:
        """Create a new MCP message."""
        message = MCPMessage(
            type=message_type,
            sender=sender,
            receiver=receiver,
            content=content,
            priority=priority,
            conversation_id=conversation_id,
            parent_message_id=parent_message_id,
        )
        
        # Track message in history
        self.message_history.append(message)
        
        # Track conversation
        if conversation_id:
            if conversation_id not in self.active_conversations:
                self.active_conversations[conversation_id] = []
            self.active_conversations[conversation_id].append(message.id)
        
        logger.debug(f"Created message {message.id} of type {message_type}")
        return message
    
    def register_tool(self, tool_name: str, tool_handler: Any, description: str, parameters_schema: Dict[str, Any]) -> None:
        """Register a tool that can be called via MCP."""
        spec = ToolSpec(
            name=tool_name,
            description=description,
            parameters_schema=parameters_schema,
            handler=tool_handler,
        )
        self.registered_tools[tool_name] = spec
        logger.info(f"Registered tool: {tool_name}")
    
    def register_agent(self, agent_name: str, agent_handler: Any) -> None:
        """Register an agent that can receive messages."""
        self.registered_agents[agent_name] = agent_handler
        logger.info(f"Registered agent: {agent_name}")
    
    async def route_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """
        Route a message to the appropriate handler.
        
        Returns a response message if applicable.
        """
        logger.debug(f"Routing message {message.id} from {message.sender} to {message.receiver}")
        
        # Handle different message types
        if message.type == MessageType.TOOL_CALL:
            return await self._handle_tool_call(message)
        
        elif message.type == MessageType.AGENT_MESSAGE:
            return await self._handle_agent_message(message)
        
        elif message.receiver and message.receiver in self.registered_agents:
            # Direct message to specific agent
            agent = self.registered_agents[message.receiver]
            return await agent.handle_message(message)
        
        else:
            logger.warning(f"No handler found for message {message.id}")
            return None
    
    async def _handle_tool_call(self, message: MCPMessage) -> MCPMessage:
        """Handle tool execution requests."""
        tool_request = ToolCallRequest(**message.content)
        
        if tool_request.tool_name not in self.registered_tools:
            return self.create_message(
                MessageType.ERROR,
                sender="mcp_protocol",
                content={"error": f"Tool not found: {tool_request.tool_name}"},
                receiver=message.sender,
                conversation_id=message.conversation_id,
                parent_message_id=message.id,
            )
        
        # Execute tool
        tool_spec = self.registered_tools[tool_request.tool_name]
        
        try:
            import time
            start_time = time.time()
            
            # Validate parameters against schema
            try:
                jsonschema_validate(instance=tool_request.parameters, schema=tool_spec.parameters_schema)
            except ValidationError as ve:
                raise ValueError(f"Invalid parameters: {ve.message}")

            result = await tool_spec.handler.execute(**tool_request.parameters)
            execution_time = time.time() - start_time
            
            tool_result = ToolCallResult(
                success=True,
                result=result,
                execution_time=execution_time,
            )
            
            return self.create_message(
                MessageType.TOOL_RESULT,
                sender="mcp_protocol",
                content=tool_result.model_dump(),
                receiver=message.sender,
                conversation_id=message.conversation_id,
                parent_message_id=message.id,
            )
        
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            tool_result = ToolCallResult(
                success=False,
                error=str(e),
                execution_time=0.0,
            )
            
            return self.create_message(
                MessageType.ERROR,
                sender="mcp_protocol",
                content=tool_result.model_dump(),
                receiver=message.sender,
                conversation_id=message.conversation_id,
                parent_message_id=message.id,
            )
    
    async def _handle_agent_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle inter-agent communication."""
        if not message.receiver or message.receiver not in self.registered_agents:
            logger.warning(f"Agent not found: {message.receiver}")
            return None
        
        agent = self.registered_agents[message.receiver]
        return await agent.handle_message(message)
    
    def get_conversation_history(self, conversation_id: str) -> List[MCPMessage]:
        """Retrieve all messages in a conversation."""
        if conversation_id not in self.active_conversations:
            return []
        
        message_ids = self.active_conversations[conversation_id]
        return [msg for msg in self.message_history if msg.id in message_ids]
    
    def get_tool_list(self) -> List[str]:
        """Get list of registered tools."""
        return list(self.registered_tools.keys())

    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """Get full tool specifications."""
        return [spec.to_dict() for spec in self.registered_tools.values()]
    
    def get_agent_list(self) -> List[str]:
        """Get list of registered agents."""
        return list(self.registered_agents.keys())
