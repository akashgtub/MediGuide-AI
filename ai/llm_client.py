"""
LLM Provider Integration Client for MediGuide-AI.
Supports Groq API (default, fast free-tier inference) and OpenAI as fallback provider.

Safety & Operational Guarantees:
- Secrets loaded exclusively from environment variables / backend .env.
- Zero plaintext API keys in logs, chat messages, or client-facing responses.
- Explicit connection & read timeouts (8.0s max) to prevent blocking.
- Resilient error handling for HTTP 429 (rate limit), 401 (auth failure), network outages.
- Graceful offline fallback: runnable without an API key.
- Explicitly flags whether a response was genuinely LLM-generated or produced by safe fallback.
- Test mock handler allows 100% offline automated test execution.
"""

import os
import re
import logging
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger("mediguide_llm_client")

# Load environment variables from .env if present
try:
    from dotenv import load_dotenv, find_dotenv
    # Search root and backend directories
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
    else:
        # Check backend/.env explicitly
        backend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", ".env")
        if os.path.exists(backend_env):
            load_dotenv(backend_env)
except ImportError:
    pass

# Provider & Model Defaults
DEFAULT_GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TIMEOUT_SECONDS = float(os.environ.get("LLM_TIMEOUT_SECONDS", "8.0"))

# Mock handler hook for automated unit/integration tests
_MOCK_LLM_HANDLER: Optional[Callable[[List[Dict[str, str]], Optional[str]], Dict[str, Any]]] = None


def set_mock_llm_handler(handler: Optional[Callable[..., Dict[str, Any]]]) -> None:
    """Set a mock handler for offline automated tests."""
    global _MOCK_LLM_HANDLER
    _MOCK_LLM_HANDLER = handler


def clear_mock_llm_handler() -> None:
    """Clear mock handler to restore real LLM client calls."""
    global _MOCK_LLM_HANDLER
    _MOCK_LLM_HANDLER = None


def get_active_provider() -> Optional[str]:
    """
    Detect configured provider based on environment variables.
    Returns: 'groq', 'openai', or None.
    """
    if os.environ.get("GROQ_API_KEY", "").strip():
        return "groq"
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return "openai"
    return None


def is_llm_available() -> bool:
    """Check if a genuine LLM provider API key or mock handler is configured."""
    if _MOCK_LLM_HANDLER is not None:
        return True
    return get_active_provider() is not None


def sanitize_llm_output(text: str) -> str:
    """Remove any accidental API key leaks or markdown code fence artifacts."""
    if not text:
        return ""
    # Mask any string resembling gsk_ or sk- API keys
    text = re.sub(r'\b(gsk_[a-zA-Z0-9]{20,})\b', '[REDACTED_API_KEY]', text)
    text = re.sub(r'\b(sk-[a-zA-Z0-9]{20,})\b', '[REDACTED_API_KEY]', text)
    return text.strip()


def generate_llm_response(
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> Dict[str, Any]:
    """
    Generate a conversational response using the configured LLM provider.
    
    Returns structured dict:
    - success: bool
    - content: str (generated text or empty string on failure)
    - is_llm_generated: bool (True only if an LLM genuinely generated the text)
    - provider: Optional[str] ('groq', 'openai', 'mock', or None)
    - model: Optional[str] (model name used)
    - error: Optional[str]
    - error_type: Optional[str] ('NO_API_KEY', 'RATE_LIMIT', 'AUTH_FAILURE', 'TIMEOUT', 'CONNECTION_ERROR', 'API_ERROR')
    """
    # 1. Test Mock Handler
    if _MOCK_LLM_HANDLER is not None:
        try:
            mock_res = _MOCK_LLM_HANDLER(messages, system_prompt)
            return {
                "success": mock_res.get("success", True),
                "content": sanitize_llm_output(mock_res.get("content", "")),
                "is_llm_generated": mock_res.get("is_llm_generated", True),
                "provider": mock_res.get("provider", "mock-llm"),
                "model": mock_res.get("model", "mock-model"),
                "error": mock_res.get("error", None),
                "error_type": mock_res.get("error_type", None),
            }
        except Exception as e:
            logger.warning("Mock LLM handler raised an error: %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "mock-llm",
                "model": "mock-model",
                "error": str(e),
                "error_type": "MOCK_ERROR",
            }

    # 2. Check Provider Availability
    provider = get_active_provider()
    if not provider:
        return {
            "success": False,
            "content": "",
            "is_llm_generated": False,
            "provider": None,
            "model": None,
            "error": "No LLM API key configured (GROQ_API_KEY or OPENAI_API_KEY). Running in safe offline fallback mode.",
            "error_type": "NO_API_KEY",
        }

    # Prepare chat conversation payload
    formatted_messages: List[Dict[str, str]] = []
    if system_prompt:
        formatted_messages.append({"role": "system", "content": system_prompt})
    formatted_messages.extend(messages)

    # 3. Groq Provider Integration
    if provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        model_name = os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        try:
            from groq import Groq, RateLimitError, AuthenticationError, APIConnectionError, APITimeoutError
            
            client = Groq(api_key=api_key, timeout=DEFAULT_TIMEOUT_SECONDS)
            completion = client.chat.completions.create(
                model=model_name,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            raw_text = completion.choices[0].message.content or ""
            return {
                "success": True,
                "content": sanitize_llm_output(raw_text),
                "is_llm_generated": True,
                "provider": "groq",
                "model": model_name,
                "error": None,
                "error_type": None,
            }
        except RateLimitError as e:
            logger.warning("Groq API rate limit exceeded (HTTP 429): %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "groq",
                "model": model_name,
                "error": "LLM rate limit reached. Safe educational fallback activated.",
                "error_type": "RATE_LIMIT",
            }
        except AuthenticationError as e:
            logger.error("Groq API authentication failure (HTTP 401). Check GROQ_API_KEY.")
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "groq",
                "model": model_name,
                "error": "LLM authentication failed. Safe educational fallback activated.",
                "error_type": "AUTH_FAILURE",
            }
        except APITimeoutError as e:
            logger.warning("Groq API request timed out after %.1fs: %s", DEFAULT_TIMEOUT_SECONDS, e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "groq",
                "model": model_name,
                "error": "LLM connection timed out. Safe educational fallback activated.",
                "error_type": "TIMEOUT",
            }
        except APIConnectionError as e:
            logger.warning("Groq API network connection error: %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "groq",
                "model": model_name,
                "error": "LLM network connection error. Safe educational fallback activated.",
                "error_type": "CONNECTION_ERROR",
            }
        except Exception as e:
            logger.warning("Groq API unexpected failure: %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "groq",
                "model": model_name,
                "error": f"LLM provider error: {str(e)}",
                "error_type": "API_ERROR",
            }

    # 4. OpenAI Provider Fallback Integration
    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        model_name = os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        try:
            from openai import OpenAI, RateLimitError, AuthenticationError, APIConnectionError, APITimeoutError
            
            client = OpenAI(api_key=api_key, timeout=DEFAULT_TIMEOUT_SECONDS)
            completion = client.chat.completions.create(
                model=model_name,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            raw_text = completion.choices[0].message.content or ""
            return {
                "success": True,
                "content": sanitize_llm_output(raw_text),
                "is_llm_generated": True,
                "provider": "openai",
                "model": model_name,
                "error": None,
                "error_type": None,
            }
        except RateLimitError as e:
            logger.warning("OpenAI API rate limit exceeded: %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "openai",
                "model": model_name,
                "error": "OpenAI rate limit reached. Safe educational fallback activated.",
                "error_type": "RATE_LIMIT",
            }
        except AuthenticationError as e:
            logger.error("OpenAI API authentication failure. Check OPENAI_API_KEY.")
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "openai",
                "model": model_name,
                "error": "OpenAI authentication failed. Safe educational fallback activated.",
                "error_type": "AUTH_FAILURE",
            }
        except (APITimeoutError, TimeoutError) as e:
            logger.warning("OpenAI API request timed out: %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "openai",
                "model": model_name,
                "error": "OpenAI request timed out. Safe educational fallback activated.",
                "error_type": "TIMEOUT",
            }
        except APIConnectionError as e:
            logger.warning("OpenAI API connection error: %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "openai",
                "model": model_name,
                "error": "OpenAI network connection error. Safe educational fallback activated.",
                "error_type": "CONNECTION_ERROR",
            }
        except Exception as e:
            logger.warning("OpenAI API unexpected failure: %s", e)
            return {
                "success": False,
                "content": "",
                "is_llm_generated": False,
                "provider": "openai",
                "model": model_name,
                "error": f"OpenAI error: {str(e)}",
                "error_type": "API_ERROR",
            }

    return {
        "success": False,
        "content": "",
        "is_llm_generated": False,
        "provider": None,
        "model": None,
        "error": "Unknown provider state.",
        "error_type": "UNKNOWN_ERROR",
    }
