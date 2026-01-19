"""Chat endpoints for conversational interface."""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid

from app.core.mcp_protocol import MessageType
from app.core.config import settings
from app.core.llm_router import TaskType

router = APIRouter()


class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # 'user', 'assistant', or 'system'
    content: str


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage]
    project_id: Optional[str] = None
    use_memory: bool = True
    task_type: TaskType = TaskType.GENERAL_CHAT
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    """Response from chat completion."""
    message: ChatMessage
    conversation_id: str
    model_used: str
    usage: Dict[str, int]
    sources: Optional[List[Dict[str, Any]]] = None


@router.post("/", response_model=ChatResponse)
async def chat_completion(request: Request, chat_req: ChatRequest) -> ChatResponse:
    """
    Handle chat completion with optional RAG context.
    
    If use_memory is True and project_id is provided, will retrieve
    relevant code context from RAG memory before generating response.
    """
    mcp = request.app.state.mcp_protocol
    rag = request.app.state.rag_memory
    llm = request.app.state.llm_router
    
    conversation_id = str(uuid.uuid4())
    sources = []
    
    # Convert messages to format expected by LLM
    llm_messages = [{"role": msg.role, "content": msg.content} for msg in chat_req.messages]
    
    # Retrieve relevant context from memory if requested
    if chat_req.use_memory and chat_req.project_id and len(chat_req.messages) > 0:
        last_user_message = next(
            (msg for msg in reversed(chat_req.messages) if msg.role == "user"),
            None
        )
        
        if last_user_message:
            # Search memory
            memory_results = await rag.search(
                query=last_user_message.content,
                project_id=chat_req.project_id,
                top_k=3,
                mode=settings.RAG_SEARCH_MODE,
            )
            
            sources = memory_results
            
            # Add context to messages
            if memory_results:
                context_parts = []
                for idx, result in enumerate(memory_results, 1):
                    context_parts.append(
                        f"[Context {idx} from {result['file_path']}]\n{result['content']}\n"
                    )
                
                context_message = {
                    "role": "system",
                    "content": (
                        "Here is relevant code context from the project:\n\n"
                        + "\n".join(context_parts)
                    ),
                }
                
                # Insert context before last user message
                llm_messages.insert(-1, context_message)
    
    # Generate response using LLM Router
    try:
        response = await llm.generate(
            messages=llm_messages,
            task_type=chat_req.task_type,
            model_name=chat_req.model,
            temperature=chat_req.temperature,
            max_tokens=chat_req.max_tokens,
        )
        
        return ChatResponse(
            message=ChatMessage(role="assistant", content=response["content"]),
            conversation_id=conversation_id,
            model_used=response["model"],
            usage=response["usage"],
            sources=sources if sources else None,
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_completion_stream(request: Request, chat_req: ChatRequest):
    """
    Stream chat completion via Server-Sent Events (SSE).
    """
    mcp = request.app.state.mcp_protocol
    rag = request.app.state.rag_memory
    llm = request.app.state.llm_router

    conversation_id = str(uuid.uuid4())

    llm_messages = [{"role": msg.role, "content": msg.content} for msg in chat_req.messages]

    # Retrieve context if requested
    if chat_req.use_memory and chat_req.project_id and len(chat_req.messages) > 0:
        last_user_message = next(
            (msg for msg in reversed(chat_req.messages) if msg.role == "user"),
            None
        )

        if last_user_message:
            memory_results = await rag.search(
                query=last_user_message.content,
                project_id=chat_req.project_id,
                top_k=3,
            )

            if memory_results:
                context_parts = []
                for idx, result in enumerate(memory_results, 1):
                    context_parts.append(
                        f"[Context {idx} from {result['file_path']}]\n{result['content']}\n"
                    )

                context_message = {
                    "role": "system",
                    "content": (
                        "Here is relevant code context from the project:\n\n"
                        + "\n".join(context_parts)
                    ),
                }
                llm_messages.insert(-1, context_message)

    async def event_generator():
        try:
            response = await llm.generate(
                messages=llm_messages,
                task_type=chat_req.task_type,
                model_name=chat_req.model,
                temperature=chat_req.temperature,
                max_tokens=chat_req.max_tokens,
                stream=True,
            )

            # If fallback response, stream as one chunk
            if "content" in response:
                yield f"data: {response['content']}\n\n"
                yield "data: [DONE]\n\n"
                return

            stream = response.get("stream")
            if stream is None:
                yield "data: [DONE]\n\n"
                return

            async for chunk in stream:
                delta = chunk.choices[0].delta
                token = getattr(delta, "content", None)
                if token:
                    yield f"data: {token}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history/{conversation_id}")
async def get_conversation_history(
    request: Request,
    conversation_id: str,
) -> Dict[str, Any]:
    """Retrieve conversation history."""
    mcp = request.app.state.mcp_protocol
    
    messages = mcp.get_conversation_history(conversation_id)
    
    return {
        "conversation_id": conversation_id,
        "message_count": len(messages),
        "messages": [
            {
                "id": msg.id,
                "type": msg.type,
                "sender": msg.sender,
                "content": msg.content,
                "timestamp": msg.timestamp,
            }
            for msg in messages
        ],
    }
