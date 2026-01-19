"""
LLM Router for multi-model support and intelligent routing.

Handles:
- Multiple LLM provider integration (OpenAI, Anthropic, local models)
- Task-based model selection
- Cost optimization
- Fallback handling
"""

from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from loguru import logger
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    LOCAL = "local"


class TaskType(str, Enum):
    """Types of tasks for model selection."""
    CODE_GENERATION = "code_generation"
    CODE_EXPLANATION = "code_explanation"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TEST_GENERATION = "test_generation"
    GENERAL_CHAT = "general_chat"


class LLMConfig:
    """Configuration for an LLM model."""
    
    def __init__(
        self,
        provider: LLMProvider,
        model_name: str,
        max_tokens: int = 4000,
        temperature: float = 0.7,
        supports_streaming: bool = True,
        cost_per_1k_tokens: float = 0.01,
        good_for_tasks: Optional[List[TaskType]] = None,
    ):
        self.provider = provider
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.supports_streaming = supports_streaming
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.good_for_tasks = good_for_tasks or []


class LLMRouter:
    """
    LLM Router for intelligent model selection and orchestration.
    
    Routes requests to the best available model based on:
    - Task type
    - Cost constraints
    - Model availability
    - Performance requirements
    """
    
    def __init__(self):
        self.openai_client: Optional[AsyncOpenAI] = None
        self.anthropic_client: Optional[AsyncAnthropic] = None
        self.groq_client: Optional[AsyncOpenAI] = None
        
        # Model registry
        self.available_models: Dict[str, LLMConfig] = {}
        
        logger.info("LLM Router created")
    
    async def initialize(self) -> None:
        """Initialize LLM provider clients."""
        try:
            # Initialize OpenAI
            if settings.OPENAI_API_KEY:
                self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                self._register_openai_models()
                logger.info("✅ OpenAI client initialized")
            
            # Initialize Anthropic
            if settings.ANTHROPIC_API_KEY:
                self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
                self._register_anthropic_models()
                logger.info("✅ Anthropic client initialized")

            # Initialize Groq (OpenAI-compatible API)
            if settings.GROQ_API_KEY:
                self.groq_client = AsyncOpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1",
                )
                self._register_groq_models()
                logger.info("✅ Groq client initialized")
            
            if not self.openai_client and not self.anthropic_client and not self.groq_client:
                logger.warning("⚠️ No LLM providers configured. Set API keys in environment.")
            
            logger.info(f"LLM Router initialized with {len(self.available_models)} models")
        
        except Exception as e:
            logger.error(f"Failed to initialize LLM Router: {e}")
            raise
    
    def _register_openai_models(self) -> None:
        """Register available OpenAI models."""
        models = [
            LLMConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-4-turbo-preview",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.01,
                good_for_tasks=[
                    TaskType.CODE_GENERATION,
                    TaskType.DEBUGGING,
                    TaskType.REFACTORING,
                ],
            ),
            LLMConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.002,
                good_for_tasks=[
                    TaskType.CODE_EXPLANATION,
                    TaskType.DOCUMENTATION,
                    TaskType.GENERAL_CHAT,
                ],
            ),
        ]
        
        for model in models:
            self.available_models[model.model_name] = model
    
    def _register_anthropic_models(self) -> None:
        """Register available Anthropic models."""
        models = [
            LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model_name="claude-3-opus-20240229",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.015,
                good_for_tasks=[
                    TaskType.CODE_GENERATION,
                    TaskType.DEBUGGING,
                    TaskType.REFACTORING,
                ],
            ),
            LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model_name="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.003,
                good_for_tasks=[
                    TaskType.CODE_EXPLANATION,
                    TaskType.TEST_GENERATION,
                    TaskType.GENERAL_CHAT,
                ],
            ),
        ]
        
        for model in models:
            self.available_models[model.model_name] = model

    def _register_groq_models(self) -> None:
        """Register available Groq models."""
        models = [
            LLMConfig(
                provider=LLMProvider.GROQ,
                model_name="llama-3.1-8b-instant",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.0002,
                good_for_tasks=[
                    TaskType.GENERAL_CHAT,
                    TaskType.CODE_EXPLANATION,
                    TaskType.DOCUMENTATION,
                ],
            ),
            LLMConfig(
                provider=LLMProvider.GROQ,
                model_name="llama-3.3-70b-versatile",
                max_tokens=4096,
                temperature=0.7,
                cost_per_1k_tokens=0.0009,
                good_for_tasks=[
                    TaskType.CODE_GENERATION,
                    TaskType.DEBUGGING,
                    TaskType.REFACTORING,
                    TaskType.GENERAL_CHAT,
                ],
            ),
        ]

        for model in models:
            self.available_models[model.model_name] = model
    
    def select_model(
        self,
        task_type: TaskType,
        prefer_cost_effective: bool = False,
        required_provider: Optional[LLMProvider] = None,
    ) -> Optional[LLMConfig]:
        """
        Select the best model for a given task.
        
        Args:
            task_type: Type of task to perform
            prefer_cost_effective: Prefer cheaper models
            required_provider: Require specific provider
        
        Returns:
            Selected model configuration or None if no suitable model
        """
        # Filter by provider if specified
        candidates = list(self.available_models.values())
        
        if required_provider:
            candidates = [m for m in candidates if m.provider == required_provider]
        
        # Filter by task suitability
        suitable = [m for m in candidates if task_type in m.good_for_tasks]
        
        if not suitable:
            suitable = candidates  # Fall back to any model
        
        if not suitable:
            logger.error("No suitable models available")
            return None
        
        # Sort by cost if preferred
        if prefer_cost_effective:
            suitable.sort(key=lambda m: m.cost_per_1k_tokens)
        else:
            # Sort by inverse cost (more expensive = potentially better)
            suitable.sort(key=lambda m: m.cost_per_1k_tokens, reverse=True)
        
        selected = suitable[0]
        logger.info(f"Selected model: {selected.model_name} for task {task_type}")
        return selected
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        task_type: TaskType = TaskType.GENERAL_CHAT,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a response using the appropriate LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            task_type: Type of task for model selection
            model_name: Specific model to use (overrides selection)
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            stream: Enable streaming response
        
        Returns:
            Response dict with 'content', 'model', 'usage', etc.
        """
        # Select model
        if model_name:
            model_config = self.available_models.get(model_name)
            if not model_config:
                raise ValueError(f"Model not found: {model_name}")
        else:
            default_model = settings.DEFAULT_LLM_MODEL
            if default_model in self.available_models:
                model_config = self.available_models[default_model]
            else:
                model_config = None

            required_provider = None
            try:
                if settings.DEFAULT_LLM_PROVIDER:
                    required_provider = LLMProvider(settings.DEFAULT_LLM_PROVIDER)
            except Exception:
                required_provider = None

            if model_config is None:
                model_config = self.select_model(task_type, required_provider=required_provider)
            if not model_config:
                raise RuntimeError("No suitable model available")
        
        # Override parameters
        temp = temperature if temperature is not None else model_config.temperature
        max_tok = max_tokens if max_tokens is not None else model_config.max_tokens
        
        # Route to provider
        try:
            if model_config.provider == LLMProvider.OPENAI:
                return await self._generate_openai(
                    messages, model_config.model_name, temp, max_tok, stream
                )
            
            elif model_config.provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic(
                    messages, model_config.model_name, temp, max_tok, stream
                )
            
            elif model_config.provider == LLMProvider.GROQ:
                return await self._generate_groq(
                    messages, model_config.model_name, temp, max_tok, stream
                )
            
            else:
                raise NotImplementedError(f"Provider not implemented: {model_config.provider}")
        except Exception as e:
            reason = str(e)
            logger.error(f"LLM provider error: {reason}")
            return self._fallback_response(messages, reason)

    def _fallback_response(self, messages: List[Dict[str, str]], reason: str) -> Dict[str, Any]:
        """Return a safe fallback response when LLM calls fail."""
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        content = (
            "LLM is unavailable right now (quota or provider error). "
            "This is a fallback response.\n\n"
            f"Reason: {reason}\n\n"
            f"Your message: {last_user}"
        )
        return {
            "content": content,
            "model": "fallback",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
            "finish_reason": "fallback",
        }
    
    async def _generate_openai(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> Dict[str, Any]:
        """Generate using OpenAI API."""
        if not self.openai_client:
            raise RuntimeError("OpenAI client not initialized")
        
        response = await self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )
        
        if stream:
            return {"stream": response, "model": model}
        
        return {
            "content": response.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "finish_reason": response.choices[0].finish_reason,
        }
    
    async def _generate_anthropic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> Dict[str, Any]:
        """Generate using Anthropic API."""
        if not self.anthropic_client:
            raise RuntimeError("Anthropic client not initialized")
        
        # Convert messages format
        system_message = None
        converted_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                converted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })
        
        kwargs = {
            "model": model,
            "messages": converted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        response = await self.anthropic_client.messages.create(**kwargs)
        
        return {
            "content": response.content[0].text,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            "finish_reason": response.stop_reason,
        }

    async def _generate_groq(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> Dict[str, Any]:
        """Generate using Groq (OpenAI-compatible) API."""
        if not self.groq_client:
            raise RuntimeError("Groq client not initialized")

        response = await self.groq_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
        )

        if stream:
            return {"stream": response, "model": model}

        return {
            "content": response.choices[0].message.content,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            "finish_reason": response.choices[0].finish_reason,
        }
    
    async def close(self) -> None:
        """Cleanup resources."""
        # Clients handle cleanup automatically
        logger.info("LLM Router closed")
