"""
LLM API interface for making calls to various language models.

This module provides a unified interface for making API calls to different LLM providers
(OpenAI, Anthropic, Groq, xAI, etc.) using LiteLLM. It includes support for:
- Streaming responses
- Tool calls and function calling
- Retry logic with exponential backoff
- Model-specific configurations
- Comprehensive error handling and logging
"""

from typing import Union, Dict, Any, Optional, AsyncGenerator, List
import os
import json
import asyncio
import contextvars
from openai import AsyncOpenAI, OpenAIError
import litellm
from litellm.files.main import ModelResponse
from utils.logger import logger
from utils.config import config
from utils.constants import MODEL_NAME_ALIASES

# 馃敆 Context variables for ADK callback
manual_message_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('manual_message_id', default=None)
current_session_id_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('current_session_id', default=None)

# litellm.set_verbose=True
# Let LiteLLM auto-adjust params and drop unsupported ones (e.g., GPT-5 temperature!=1)
litellm.modify_params = True
litellm.drop_params = True

def set_manual_message_id(message_id: Optional[str]):
    """璁剧疆鎵嬪姩鎻掑叆娑堟伅鐨処D鍒颁笂涓嬫枃涓紝鐢ㄤ簬鍥炶皟鍚屾invocation_id"""
    manual_message_id_context.set(message_id)
    if message_id:
        logger.debug(f"馃敆 Set manual_message_id context: {message_id}")

async def _sync_manual_message_invocation_id(session_id: str, adk_invocation_id: str):
    """鏍规嵁session_id鎵惧埌鏈€鏂扮殑鐢ㄦ埛娑堟伅锛屽悓姝ュ叾invocation_id涓篈DK鐢熸垚鐨処D"""
    try:
        logger.info(f"Before _sync_manual_message_invocation_id: session_id={session_id}, adk_invocation_id={adk_invocation_id}")
        
        # 鑾峰彇鏁版嵁搴撳鎴风
        from services.postgresql import DBConnection
        db = DBConnection()
        client = await db.client
        
        # 鏌ユ壘璇?session_id 涓嬫渶鏂扮殑 author='user' 鐨勬秷鎭?
        user_message_result = await client.table('events')\
            .select('id, invocation_id, timestamp')\
            .eq('session_id', session_id)\
            .eq('author', 'user')\
            .order('timestamp', desc=True)\
            .limit(1)\
            .execute()
        
        if not user_message_result.data:
            logger.warning(f"Not found user message in session {session_id}")
            return
        
        user_message = user_message_result.data[0]
        message_id = user_message.get('id')
        old_invocation_id = user_message.get('invocation_id')
        
        # 鏇存柊璇ョ敤鎴锋秷鎭殑invocation_id涓篈DK鐢熸垚鐨処D  
        update_result = await client.table('events')\
            .eq('id', message_id)\
            .update({'invocation_id': adk_invocation_id})
        
        if update_result.data:
            logger.info(f"Successfully synchronized invocation_id: {message_id} ({old_invocation_id} -> {adk_invocation_id})")
   
        else:
            logger.warning(f"Failed to update user message: {message_id}")
            
    except Exception as e:
        logger.warning(f"Failed to synchronize invocation_id (not affecting main flow): {e}")

    

from google.genai import types # type: ignore
from google.adk.agents.run_config import RunConfig, StreamingMode # type: ignore
from google.adk.models.lite_llm import LiteLlm # type: ignore
from google.adk.agents import LlmAgent # type: ignore
from google.adk.sessions import DatabaseSessionService # type: ignore
from services.model_only_session_service import ModelOnlyDBSessionService
from google.adk import Runner # type: ignore
from google.adk.agents.callback_context import CallbackContext # type: ignore
from google.adk.models import LlmRequest, LlmResponse # type: ignore



# 甯搁噺
MAX_RETRIES = 2
RATE_LIMIT_DELAY = 30
RETRY_DELAY = 0.1

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMRetryError(LLMError):
    """Exception raised when retries are exhausted."""
    pass


def normalize_model_name(model_name: str) -> str:
    """Normalize model aliases to a provider-acceptable model name."""
    resolved_model = MODEL_NAME_ALIASES.get(model_name, model_name)

    if "deepseek" in model_name.lower():
        legacy_deepseek_names = {
            "deepseek",
            "deepseek-chat",
            "deepseek/deepseek-chat",
            "deepseek/deepseek-chat-v3.1",
            "deepseek/deepseek-chat-v3",
            "deepseek/deepseek-reasoner",
            "deepseek/deepseek-r1",
            "deepseek/deepseek-v3",
            "deepseek/deepseek-v3.1",
        }
        if resolved_model.lower() in legacy_deepseek_names:
            preferred_deepseek_model = getattr(config, "MODEL_TO_USE", None) or "deepseek-v4-flash"
            return (
                preferred_deepseek_model
                if isinstance(preferred_deepseek_model, str) and preferred_deepseek_model.lower().startswith("deepseek-v4")
                else "deepseek-v4-flash"
            )

    return resolved_model

def setup_api_keys() -> None:
    """Set up API keys from environment variables."""
    providers = ['OPENAI', 'ANTHROPIC', 'GROQ', 'OPENROUTER', 'XAI', 'MORPH', 'GEMINI']
    for provider in providers:
        key = getattr(config, f'{provider}_API_KEY')
        if key:
            logger.debug(f"API key set for provider: {provider}")
        else:
            logger.warning(f"No API key found for provider: {provider}")

    # Set up OpenRouter API base if not already set
    if config.OPENROUTER_API_KEY and config.OPENROUTER_API_BASE:
        os.environ['OPENROUTER_API_BASE'] = config.OPENROUTER_API_BASE
        logger.debug(f"Set OPENROUTER_API_BASE to {config.OPENROUTER_API_BASE}")

    # Set up AWS Bedrock credentials
    aws_access_key = config.AWS_ACCESS_KEY_ID
    aws_secret_key = config.AWS_SECRET_ACCESS_KEY
    aws_region = config.AWS_REGION_NAME

    if aws_access_key and aws_secret_key and aws_region:
        logger.debug(f"AWS credentials set for Bedrock in region: {aws_region}")
        # Configure LiteLLM to use AWS credentials
        os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key
        os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_key
        os.environ['AWS_REGION_NAME'] = aws_region
    else:
        logger.warning(f"Missing AWS credentials for Bedrock integration - access_key: {bool(aws_access_key)}, secret_key: {bool(aws_secret_key)}, region: {aws_region}")


def resolve_provider_credentials(model_name: str) -> tuple[str, Optional[str], Optional[str]]:
    """Resolve provider name, API key, and API base for the requested model."""
    resolved_model = normalize_model_name(model_name)

    resolved_api_key: Optional[str] = None
    resolved_api_base: Optional[str] = None
    provider = "Unknown"

    if "openrouter" in resolved_model.lower():
        resolved_api_key = config.OPENROUTER_API_KEY
        resolved_api_base = config.OPENROUTER_API_BASE
        provider = "OpenRouter"
    elif "openai" in resolved_model.lower() or "gpt" in resolved_model.lower():
        resolved_api_key = config.OPENAI_API_KEY
        resolved_api_base = config.OPENAI_API_BASE
        provider = "OpenAI"
    elif "anthropic" in resolved_model.lower() or "claude" in resolved_model.lower():
        resolved_api_key = config.ANTHROPIC_API_KEY
        provider = "Anthropic"
    elif "deepseek" in resolved_model.lower():
        resolved_api_key = getattr(config, 'DEEPSEEK_API_KEY', None) or config.OPENAI_API_KEY
        resolved_api_base = config.DEEPSEEK_API_BASE
        provider = "DeepSeek" if getattr(config, 'DEEPSEEK_API_KEY', None) else "DeepSeek (using OpenAI key)"
    elif "gemini" in resolved_model.lower():
        resolved_api_key = config.GEMINI_API_KEY
        provider = "Gemini"
    elif "groq" in resolved_model.lower():
        resolved_api_key = config.GROQ_API_KEY
        provider = "Groq"
    elif "xai" in resolved_model.lower():
        resolved_api_key = config.XAI_API_KEY
        provider = "xAI"
    else:
        resolved_api_key = config.OPENAI_API_KEY
        provider = "OpenAI (default)"

    return provider, resolved_api_key, resolved_api_base

def get_openrouter_fallback(model_name: str) -> Optional[str]:
    """Get OpenRouter fallback model for a given model name."""
    # Skip if already using OpenRouter
    if model_name.startswith("openrouter/"):
        return None
    
    # Map models to their OpenRouter equivalents
    fallback_mapping = {
        "anthropic/claude-3-7-sonnet-latest": "openrouter/anthropic/claude-3.7-sonnet",
        "anthropic/claude-sonnet-4-20250514": "openrouter/anthropic/claude-sonnet-4",
        "xai/grok-4": "openrouter/x-ai/grok-4",
        "gemini/gemini-2.5-pro": "openrouter/google/gemini-2.5-pro",
    }
    
    # Check for exact match first
    if model_name in fallback_mapping:
        return fallback_mapping[model_name]
    
    # Check for partial matches (e.g., bedrock models)
    for key, value in fallback_mapping.items():
        if key in model_name:
            return value
    
    # Default fallbacks by provider
    if "claude" in model_name.lower() or "anthropic" in model_name.lower():
        return "openrouter/anthropic/claude-sonnet-4"
    elif "xai" in model_name.lower() or "grok" in model_name.lower():
        return "openrouter/x-ai/grok-4"
    
    return None

async def handle_error(error: Exception, attempt: int, max_attempts: int) -> None:
    """Handle API errors with appropriate delays and logging."""
    delay = RATE_LIMIT_DELAY if isinstance(error, litellm.exceptions.RateLimitError) else RETRY_DELAY
    logger.warning(f"Error on attempt {attempt + 1}/{max_attempts}: {str(error)}")
    logger.debug(f"Waiting {delay} seconds before retry...")
    await asyncio.sleep(delay)

def prepare_params(
    messages: List[Dict[str, Any]],
    model_name: str,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    response_format: Optional[Any] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low'
) -> Dict[str, Any]:
    """Prepare parameters for the API call."""
    params = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
        "response_format": response_format,
        "top_p": top_p,
        "stream": stream,
    }

    if api_key:
        params["api_key"] = api_key
    if api_base:
        params["api_base"] = api_base
    if model_id:
        params["model_id"] = model_id

    # Handle token limits
    if max_tokens is not None:
        # For Claude 3.7 in Bedrock, do not set max_tokens or max_tokens_to_sample
        # as it causes errors with inference profiles
        if model_name.startswith("bedrock/") and "claude-3-7" in model_name:
            logger.debug(f"Skipping max_tokens for Claude 3.7 model: {model_name}")
            # Do not add any max_tokens parameter for Claude 3.7
        else:
            is_openai_o_series = 'o1' in model_name
            is_openai_gpt5 = 'gpt-5' in model_name
            param_name = "max_completion_tokens" if (is_openai_o_series or is_openai_gpt5) else "max_tokens"
            params[param_name] = max_tokens

    # Add tools if provided
    if tools:
        params.update({
            "tools": tools,
            "tool_choice": tool_choice
        })
        logger.debug(f"Added {len(tools)} tools to API parameters")

    # # Add Claude-specific headers
    if "claude" in model_name.lower() or "anthropic" in model_name.lower():
        params["extra_headers"] = {
            # "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
            "anthropic-beta": "output-128k-2025-02-19"
        }
        # params["mock_testing_fallback"] = True
        logger.debug("Added Claude-specific headers")

    # Add OpenRouter-specific parameters
    if model_name.startswith("openrouter/"):
        logger.debug(f"Preparing OpenRouter parameters for model: {model_name}")

        # Add optional site URL and app name from config
        site_url = config.OR_SITE_URL
        app_name = config.OR_APP_NAME
        if site_url or app_name:
            extra_headers = params.get("extra_headers", {})
            if site_url:
                extra_headers["HTTP-Referer"] = site_url
            if app_name:
                extra_headers["X-Title"] = app_name
            params["extra_headers"] = extra_headers
            logger.debug(f"Added OpenRouter site URL and app name to headers")

    # Add Bedrock-specific parameters
    if model_name.startswith("bedrock/"):
        logger.debug(f"Preparing AWS Bedrock parameters for model: {model_name}")

        if not model_id and "anthropic.claude-3-7-sonnet" in model_name:
            params["model_id"] = "arn:aws:bedrock:us-west-2:935064898258:inference-profile/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
            logger.debug(f"Auto-set model_id for Claude 3.7 Sonnet: {params['model_id']}")

    fallback_model = get_openrouter_fallback(model_name)
    if fallback_model:
        params["fallbacks"] = [{
            "model": fallback_model,
            "messages": messages,
        }]
        logger.debug(f"Added OpenRouter fallback for model: {model_name} to {fallback_model}")

    # Apply Anthropic prompt caching (minimal implementation)
    # Check model name *after* potential modifications (like adding bedrock/ prefix)
    effective_model_name = params.get("model", model_name) # Use model from params if set, else original

    # OpenAI GPT-5: drop unsupported temperature param (only default 1 allowed)
    if "gpt-5" in effective_model_name and "temperature" in params and params["temperature"] != 1:
        params.pop("temperature", None)

    # OpenAI GPT-5: request priority service tier when calling OpenAI directly
    # Pass via both top-level and extra_body for LiteLLM compatibility
    if "gpt-5" in effective_model_name and not effective_model_name.startswith("openrouter/"):
        params["service_tier"] = "priority"
        extra_body = params.get("extra_body", {})
        if "service_tier" not in extra_body:
            extra_body["service_tier"] = "priority"
        params["extra_body"] = extra_body
    if "claude" in effective_model_name.lower() or "anthropic" in effective_model_name.lower():
        messages = params["messages"] # Direct reference, modification affects params

        # Ensure messages is a list
        if not isinstance(messages, list):
            return params # Return early if messages format is unexpected

        # Apply cache control to the first 4 text blocks across all messages
        cache_control_count = 0
        max_cache_control_blocks = 3

        for message in messages:
            if cache_control_count >= max_cache_control_blocks:
                break
                
            content = message.get("content")
            
            if isinstance(content, str):
                message["content"] = [
                    {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                ]
                cache_control_count += 1
            elif isinstance(content, list):
                for item in content:
                    if cache_control_count >= max_cache_control_blocks:
                        break
                    if isinstance(item, dict) and item.get("type") == "text" and "cache_control" not in item:
                        item["cache_control"] = {"type": "ephemeral"}
                        cache_control_count += 1

    # Add reasoning_effort for Anthropic models if enabled
    use_thinking = enable_thinking if enable_thinking is not None else False
    is_anthropic = "anthropic" in effective_model_name.lower() or "claude" in effective_model_name.lower()
    is_xai = "xai" in effective_model_name.lower() or model_name.startswith("xai/")
    is_kimi_k2 = "kimi-k2" in effective_model_name.lower() or model_name.startswith("moonshotai/kimi-k2")

    if is_kimi_k2:
        params["provider"] = {
            "order": ["together/fp8", "novita/fp8", "baseten/fp8", "moonshotai", "groq"]
        }

    if is_anthropic and use_thinking:
        effort_level = reasoning_effort if reasoning_effort else 'low'
        params["reasoning_effort"] = effort_level
        params["temperature"] = 1.0 # Required by Anthropic when reasoning_effort is used
        logger.info(f"Anthropic thinking enabled with reasoning_effort='{effort_level}'")

    # Add reasoning_effort for xAI models if enabled
    if is_xai and use_thinking:
        effort_level = reasoning_effort if reasoning_effort else 'low'
        params["reasoning_effort"] = effort_level
        logger.info(f"xAI thinking enabled with reasoning_effort='{effort_level}'")

    # Add xAI-specific parameters
    if model_name.startswith("xai/"):
        logger.debug(f"Preparing xAI parameters for model: {model_name}")
        # xAI models support standard parameters, no special handling needed beyond reasoning_effort

    return params

async def make_llm_api_call(
    messages: List[Dict[str, Any]],
    model_name: str,
    response_format: Optional[Any] = None,
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    stream: bool = False,
    top_p: Optional[float] = None,
    model_id: Optional[str] = None,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low'
) -> Union[Dict[str, Any], AsyncGenerator, ModelResponse]:
    """
    Make an API call to a language model using LiteLLM or Google ADK.

    Args:
        messages: List of message dictionaries for the conversation
        model_name: Name of the model to use (e.g., "gpt-4", "claude-3", "openrouter/openai/gpt-4", "bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
        response_format: Desired format for the response
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in the response
        tools: List of tool definitions for function calling
        tool_choice: How to select tools ("auto" or "none")
        api_key: Override default API key
        api_base: Override default API base URL
        stream: Whether to stream the response
        top_p: Top-p sampling parameter
        model_id: Optional ARN for Bedrock inference profiles
        enable_thinking: Whether to enable thinking
        reasoning_effort: Level of reasoning effort

    Returns:
        Union[Dict[str, Any], AsyncGenerator]: API response or stream

    Raises:
        LLMRetryError: If API call fails after retries
        LLMError: For other API-related errors
    """
    # debug <timestamp>.json messages
    logger.info(f"Making LLM API call to model: {model_name} (Thinking: {enable_thinking}, Effort: {reasoning_effort})")
    logger.info(f"馃摗 API Call: Using model {model_name}")

    provider, resolved_api_key, resolved_api_base = resolve_provider_credentials(model_name)
    resolved_model_name = normalize_model_name(model_name)
    effective_api_key = api_key or resolved_api_key
    effective_api_base = api_base or resolved_api_base

    if not effective_api_key:
        raise LLMError(
            f"No API key configured for provider {provider} while using model '{model_name}'. "
            "Set the corresponding key in backend/.env and restart the backend."
        )

    # OpenAI-compatible providers can work better through the official SDK than LiteLLM.
    if any(name in provider.lower() for name in ["openai", "deepseek", "openrouter"]):
        sdk_model_name = resolved_model_name
        if sdk_model_name.startswith("openai/"):
            sdk_model_name = sdk_model_name.split("/", 1)[1]
        if sdk_model_name.startswith("openrouter/"):
            sdk_model_name = sdk_model_name.split("/", 1)[1]

        client = AsyncOpenAI(
            api_key=effective_api_key,
            base_url=effective_api_base,
        )

        request_kwargs: Dict[str, Any] = {
            "model": sdk_model_name,
            "messages": messages,
            "stream": stream,
        }

        if max_tokens is not None:
            request_kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            request_kwargs["temperature"] = temperature
        if top_p is not None:
            request_kwargs["top_p"] = top_p
        if tools:
            request_kwargs["tools"] = tools
            request_kwargs["tool_choice"] = tool_choice
        if response_format is not None:
            request_kwargs["response_format"] = response_format

        logger.info(f"Using AsyncOpenAI client for model: {sdk_model_name}")
        try:
            return await client.chat.completions.create(**request_kwargs)
        except Exception as e:
            logger.error(f"AsyncOpenAI API call failed: {str(e)}", exc_info=True)
            raise LLMError(f"API call failed: {str(e)}")

    params = prepare_params(
        messages=messages,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format=response_format,
        tools=tools,
        tool_choice=tool_choice,
        api_key=effective_api_key,
        api_base=effective_api_base,
        stream=stream,
        top_p=top_p,
        model_id=model_id,
        enable_thinking=enable_thinking,
        reasoning_effort=reasoning_effort
    )
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Attempt {attempt + 1}/{MAX_RETRIES}")
            # logger.debug(f"API request parameters: {json.dumps(params, indent=2)}")

            response = await litellm.acompletion(**params)
            logger.debug(f"Successfully received API response from {model_name}")
            # logger.debug(f"Response: {response}")
            return response

        except (litellm.exceptions.RateLimitError, OpenAIError, json.JSONDecodeError) as e:
            last_error = e
            await handle_error(e, attempt, MAX_RETRIES)

        except Exception as e:
            logger.error(f"Unexpected error during API call: {str(e)}", exc_info=True)
            raise LLMError(f"API call failed: {str(e)}")

    error_msg = f"Failed to make API call after {MAX_RETRIES} attempts"
    if last_error:
        error_msg += f". Last error: {str(last_error)}"
    logger.error(error_msg, exc_info=True)
    raise LLMRetryError(error_msg)


async def make_adk_api_call(
    messages: List[Dict[str, Any]],
    model_name: str = "openai/gpt-4o",
    temperature: float = 0,
    max_tokens: Optional[int] = None,
    tools: Optional[Union[List[Dict[str, Any]], Dict[str, callable], List]] = None, 
    tool_choice: str = "auto",
    stream: bool = True,
    enable_thinking: Optional[bool] = False,
    reasoning_effort: Optional[str] = 'low',
) -> Union[AsyncGenerator, Dict[str, Any]]:
    """
    Make an API call using Google ADK (Agent Development Kit).
    
    Uses context variables to access manual_message_id for invocation_id synchronization.
    
    Args:
        messages: List of message dictionaries with metadata (app_name, user_id, session_id, etc.)
        model_name: Name of the model to use
        temperature: Sampling temperature (0-1)
        max_tokens: Maximum tokens in the response
        tools: List of tool schemas OR dict of tool functions (ADK mode)
        tool_choice: How to select tools ("auto" or "none")
        stream: Whether to stream the response
        enable_thinking: Whether to enable thinking
        reasoning_effort: Level of reasoning effort
    
    Returns:
        AsyncGenerator: Streaming response from ADK
    """

    logger.info(f"Preparing to make ADK API call")
    logger.info(f"Input parameters: model_name={model_name}, stream={stream}, temperature={temperature}")
    logger.info(f"Messages length: {len(messages)}")
    


    for i, msg in enumerate(messages):
        logger.info(f"  Message {i}: role={msg.get('role')}, content={msg.get('content')}")
        if msg.get('user_id'):
            logger.info(f"    metadata: user_id={msg.get('user_id')}, session_id={msg.get('session_id')}, thread_id={msg.get('thread_id')}")

    # 鎻愬彇鍏冩暟鎹?
    for message in messages:
        if isinstance(message, dict) and message.get('role') == 'user':
            app_name = message.get('app_name', 'hephaestus')
            user_id = message.get('user_id', 'default_user')
            session_id = message.get('session_id', 'default_session')
            thread_id = message.get('thread_id')  # 鏂板锛氭彁鍙杢hread_id
            logger.info(f"From adk events: app_name={app_name}, user_id={user_id}, session_id={session_id}, thread_id={thread_id}")
                        
            # 璁剧疆session_id鍒颁笂涓嬫枃涓紝渚汚DK鍥炶皟浣跨敤
            current_session_id_context.set(session_id)
            break

    # 鑾峰彇鐢ㄦ埛娑堟伅鍐呭
    user_message = None
    
    for i, msg in enumerate(reversed(messages)):
        
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            
            # 杩欓噷鐨勯€昏緫鐢ㄦ潵閫傞厤澶勭悊澶氭ā鎬佹秷鎭牸寮?
            if isinstance(content, list):
                # 澶氭ā鎬佹秷鎭細浠庡垪琛ㄤ腑鎻愬彇鏂囨湰閮ㄥ垎
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get('type') == 'text':
                        text_parts.append(part.get('text', ''))
                user_message = ' '.join(text_parts).strip()
                
                # 濡傛灉鏈夐潪鏂囨湰鍐呭锛岃褰曡鍛?
                non_text_parts = [p for p in content if isinstance(p, dict) and p.get('type') != 'text']
                if non_text_parts:
                    logger.warning(f"ADK runner only supports text input. Ignoring {len(non_text_parts)} non-text parts.")
                    
            elif isinstance(content, str):
                # 鏅€氭枃鏈秷鎭?
                user_message = content
            else:
                # 鍏朵粬鏍煎紡锛屽皾璇曡浆鎹负瀛楃涓?
                user_message = str(content) if content else ''
                
            break
    
    if not user_message:
        logger.error("鏈壘鍒扮敤鎴锋秷鎭紒")
        raise LLMError("No user message found in messages")

    # 鍒涘缓鐢ㄦ埛鍐呭
    user_content = types.Content(
        role='user', 
        parts=[types.Part(text=user_message)]  # 鐜板湪纭繚 user_message 鏄瓧绗︿覆
    )


    # 璁剧疆娴佸紡妯″紡
    streaming_mode = StreamingMode.SSE if stream else StreamingMode.NONE
    
    run_config = RunConfig(streaming_mode=streaming_mode)

    
    # 浠庢ā鍨嬪悕绉拌В鏋愬疄闄呬娇鐢ㄧ殑妯″瀷鍜孉PI Key
    resolved_model = MODEL_NAME_ALIASES.get(model_name, model_name)
    logger.info(f"Resolved model: {resolved_model}")
    
    # 鐗规畩澶勭悊 DeepSeek 妯″瀷鏍煎紡 (鍚庡鏂规)
    if "DeepSeek" in model_name and "/" in model_name:
        logger.warning(f"Detected uppercase DeepSeek format: {model_name}, converting to standard format")
        resolved_model = "deepseek/deepseek-chat"
        logger.info(f"Converted to: {resolved_model}")
    
    # 娣诲姞璋冭瘯鏃ュ織 - 鏄剧ずMODEL_NAME_ALIASES涓槸鍚︽湁杩欎釜鏄犲皠
    if model_name in MODEL_NAME_ALIASES:
        logger.info(f"Found alias mapping: {model_name} -> {MODEL_NAME_ALIASES[model_name]}")
    else:
        logger.warning(f" No alias mapping found for: {model_name}, available aliases: {list(MODEL_NAME_ALIASES.keys())[:10]}")
    
    provider, resolved_api_key, resolved_api_base = resolve_provider_credentials(resolved_model)
    if provider == "OpenAI (default)" and not ("openai" in resolved_model.lower() or "gpt" in resolved_model.lower()):
        logger.warning(f"Unrecognized model {resolved_model}, using default OpenAI configuration")

    logger.info(f"Using provider: {provider}")
    logger.info(f"API Key configured: {bool(resolved_api_key)}")
    
    if resolved_api_base:
        logger.info(f"Using API Base: {resolved_api_base}")

    if not resolved_api_key:
        raise LLMError(
            f"No API key configured for provider {provider} while using model '{resolved_model}'. "
            "Set the corresponding key in backend/.env and restart the backend."
        )
    
    logger.info(f"Creating LiteLlm model with model={resolved_model}")
    
    # 鍒涘缓LiteLlm妯″瀷锛屾牴鎹槸鍚︽湁api_base鏉ュ喅瀹氬弬鏁?
    model_params = {
        "model": resolved_model,
        "api_key": resolved_api_key
    }
    
    if resolved_api_base:
        model_params["api_base"] = resolved_api_base
    
    model = LiteLlm(**model_params)    
    # model = LiteLlm(
    #     model="deepseek/deepseek-chat",  
    #     api_key="sk-77ef05a6295b44579f7cc72ab4a537dd",
    #     base_url="https://api.deepseek.com"
    # )
    logger.info(f"Model created successfully: model={resolved_model}, provider={provider}")

    # 鎻愬彇 system_prompt
    agent_instruction = "You are a helpful AI assistant. Please answer the user's question."
    for msg in messages:
        if msg.get('role') == 'system':
            agent_instruction = msg.get('content', agent_instruction)
            break
    
    # 瀹氫箟ADK鍥炶皟鍑芥暟锛岀敤浜庡悓姝nvocation_id锛堝洜涓烘煇鏉?User Messages 鏄墜鍔ㄦ彃鍏ワ紝闇€瑕侀€氳繃鍥炶皟淇濇寔鐩稿悓鐨?invocation_id
    def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
        """ADK鍥炶皟锛氬湪LLM璋冪敤鍓嶅悓姝nvocation_id"""
        try:
      
            # 浠庝笂涓嬫枃鍙橀噺鑾峰彇session_id
            session_id = current_session_id_context.get()
            logger.info(f"From before_model_callback: session_id={session_id}")
            
            # 鑾峰彇ADK鐢熸垚鐨刬nvocation_id
            adk_invocation_id = getattr(callback_context, 'invocation_id', None)
            logger.info(f"From before_model_callback: adk_invocation_id={adk_invocation_id}")

            if session_id and adk_invocation_id:
                # 鍚姩鍚屾浠诲姟锛屾牴鎹畇ession_id鍜宎uthor='user'鏌ユ壘鏈€鏂扮敤鎴锋秷鎭繘琛屾洿鏂?
                import asyncio
                asyncio.create_task(_sync_manual_message_invocation_id(session_id, adk_invocation_id))
            else:
                logger.debug(f"Ignore invocation_id synchronization: session_id={session_id}, invocation_id={adk_invocation_id}")

        except Exception as e:
            logger.warning(f"Failed to start invocation_id synchronization (not affecting main flow): {e}")
        
        # 蹇呴』杩斿洖 None 璁〢DK缁х画姝ｅ父鎵ц
        return None

    # 澶勭悊宸ュ叿锛氬皢鍑芥暟瀛楀吀杞崲涓篈DK FunctionTool鍒楄〃
    adk_tools = []
    if tools:
        from google.adk.tools import FunctionTool # type: ignore
        
        if isinstance(tools, dict):            
            for tool_name, tool_func in tools.items():
                try:
                    function_tool = FunctionTool(func=tool_func)
                    adk_tools.append(function_tool)
                except Exception as e:
                    logger.error(f"tool {tool_name} conversion failed: {e}")
                    
        elif isinstance(tools, list):
            # 濡傛灉宸茬粡鏄疐unctionTool鍒楄〃锛岀洿鎺ヤ娇鐢?
            adk_tools = tools
        
        else:
            logger.error(f"Unsupported tools type: {type(tools)}")
    
 
    # 鍒涘缓 Agent 瀵硅薄锛堝甫鍥炶皟鍜屽伐鍏凤級
    agent = LlmAgent(
        name=app_name,
        model=model,
        instruction=agent_instruction,
        tools=adk_tools,  # 浼犻€掕浆鎹㈠悗鐨凙DK宸ュ叿鍒楄〃
        before_model_callback=before_model_callback  # 浣跨敤 before_model_callback
    )

    logger.info(f"Agent created successfully: {agent}")

    logger.info(f"agent_info: {agent}")

    # 璁剧疆鏁版嵁搴撲細璇濇湇鍔?
    try:
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            if hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
                DATABASE_URL = config.DATABASE_URL
            else:
                DATABASE_URL = "postgresql://postgres:password@localhost:5432/hephaestus"
        # 涓轰簡鏃ュ織瀹夊叏锛岄殣钘忓瘑鐮?
        from urllib.parse import urlparse, urlunparse
        parsed_url = urlparse(DATABASE_URL)
        safe_url = DATABASE_URL
        if parsed_url.password:
            safe_url = DATABASE_URL.replace(parsed_url.password, "********")
        
        logger.info(f"Using DATABASE_URL for SessionService: {safe_url}")

        # session_service = DatabaseSessionService(DATABASE_URL)
        session_service = ModelOnlyDBSessionService(DATABASE_URL)
        
        
        # 濡傛灉 ModelOnlyDBSessionService 鍒涘缓鎴愬姛锛岃幏鍙栨垨鍒涘缓浼氳瘽
        try:            
            # 鍏堝皾璇曡幏鍙栫幇鏈変細璇?
            existing_session = await session_service.get_session(
                app_name=app_name, 
                user_id=user_id, 
                session_id=session_id
            )
            
            if existing_session:
                logger.info(f"Found existing session: {existing_session}")
                logger.info(f"Session history record count: {len(existing_session.events) if hasattr(existing_session, 'events') else 'Unknown'}")
            else:
                logger.warning(f"No session found for {session_id}, creating new session")
                
        
                # 杩欓噷鍙互娣诲姞鏁版嵁搴撶洿鎺ユ煡璇㈡潵鎵惧埌鍙兘鐨剆ession涓嶅尮閰嶉棶棰?
                try:
                    import asyncpg # type: ignore
                    conn = await asyncpg.connect(DATABASE_URL)
                    try:
                        # 鏌ユ壘璇ョ敤鎴风殑鎵€鏈変細璇?
                        all_sessions = await conn.fetch(
                            "SELECT id, app_name, user_id, created_at FROM sessions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 5",
                            user_id
                        )
                  
                        for session in all_sessions:
                            logger.info(f"  - session_id: {session['id']}, app_name: {session['app_name']}, created_at: {session['created_at']}")
                            
                        # 鏌ユ壘璇ession_id瀵瑰簲鐨勪簨浠舵暟閲?
                        event_count = await conn.fetchval(
                            "SELECT COUNT(*) FROM events WHERE session_id = $1",
                            session_id
                        )
                        logger.info(f"馃攳 session_id {session_id} 鐨勪簨浠舵暟閲? {event_count}")
                        
                    finally:
                        await conn.close()
                except Exception as db_debug_error:
                    logger.warning(f"璋冭瘯鏌ヨ澶辫触: {db_debug_error}")
                
                # 浼氳瘽涓嶅瓨鍦紝鍒涘缓鏂扮殑
                await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
              
                
        except Exception as session_error:
            logger.error(f"Session operation failed: {session_error}")
            
            # 澶勭悊浼氳瘽閲嶅鍒涘缓閿欒
            if "duplicate key value violates unique constraint" in str(session_error):
                logger.info(f"Session already exists, trying to get existing session...")
                try:
                    existing_session = await session_service.get_session(
                        app_name=app_name, 
                        user_id=user_id, 
                        session_id=session_id
                    )
                    if existing_session:
                        logger.info(f"Successfully got existing session: {existing_session}")
                    else:
                        raise Exception("Session should exist but cannot be retrieved")
                except Exception as get_error:
                    logger.error(f"Failed to get existing session: {get_error}")
                    raise session_error
                    
            # 濡傛灉鏄暟鎹崯鍧忥紝灏濊瘯娓呯悊閲嶅缓
            elif "EOFError" in str(session_error) or "Ran out of input" in str(session_error):
                try:
                    # 娓呯悊鎹熷潖鐨勬暟鎹?
                    import asyncpg # type: ignore
                    conn = await asyncpg.connect(DATABASE_URL)
                    try:
                        await conn.execute("DELETE FROM events WHERE session_id = $1", session_id)
                        await conn.execute("DELETE FROM sessions WHERE id = $1", session_id)
                        logger.info(f"Cleaned up corrupted data: {session_id}")
                    finally:
                        await conn.close()
                    
                    # 閲嶆柊鍒涘缓浼氳瘽
                    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
                    logger.info(f"Recreated session: {session_id}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup and recreate session: {cleanup_error}")
                    raise session_error
            else:
                raise session_error
                
    except Exception as e:
        logger.error(f"DatabaseSessionService failed completely: {e}")
        import traceback
        traceback.print_exc()
        logger.error(f"Failed to use DatabaseSessionService, using InMemorySessionService: {e}", exc_info=True)
        
        # 鍥為€€鍒板唴瀛樹細璇濇湇鍔?
        from google.adk.sessions import InMemorySessionService # type: ignore
        session_service = InMemorySessionService()
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        logger.info(f"InMemorySessionService created successfully: {session_id}")

    # 鏈€鍚庨獙璇侊細纭繚SessionService鍖呭惈鍘嗗彶鏁版嵁
    try:
        final_session_check = await session_service.get_session(
            app_name=app_name, 
            user_id=user_id, 
            session_id=session_id
        )
        if final_session_check:
            event_count = len(final_session_check.events) if hasattr(final_session_check, 'events') else 0
          
            # 濡傛灉鏈夊巻鍙蹭簨浠讹紝鎵撳嵃鏈€杩戝嚑鏉?
            if hasattr(final_session_check, 'events') and final_session_check.events:
                for i, event in enumerate(final_session_check.events[-3:]):  # 鏄剧ず鏈€鍚?鏉?
                    logger.info(f"  {i+1}. author={getattr(event, 'author', 'unknown')}, content={str(getattr(event, 'content', ''))[:50]}...")
        else:
            logger.error(f"Final session validation failed: cannot get session {session_id}")
    except Exception as final_check_error:
        logger.error(f"Final session validation failed: {final_check_error}")

    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service  # 馃攽 鍏抽敭锛氫紶閫掑寘鍚巻鍙叉暟鎹殑session_service
    )


    # 鐩存帴杩斿洖 runner.run_async 鐨勫紓姝ョ敓鎴愬櫒锛屽氨鍍?make_llm_api_call 杩斿洖 litellm.acompletion 涓€鏍?
    adk_generator = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content,
        run_config=run_config
    )
    
    return adk_generator


# Initialize API keys on module import
# setup_api_keys()
