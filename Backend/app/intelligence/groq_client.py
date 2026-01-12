"""
Groq LLM client wrapper.

Provides a unified interface similar to gemini_client.py but uses Groq's API.
Groq offers much faster inference and better free tier limits.
"""

from __future__ import annotations

import json
from typing import Any

from groq import Groq

from app.core.config import get_settings


def get_groq_client() -> Groq:
    """Get configured Groq client."""
    settings = get_settings()
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY not configured")
    return Groq(api_key=settings.groq_api_key)


def groq_generate_json(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """
    Generate JSON response from Groq.
    
    Args:
        prompt: The prompt to send to the model
        model: Model name (defaults to settings.groq_model)
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Parsed JSON response
        
    Raises:
        ValueError: If response is not valid JSON
        Exception: If API call fails
    """
    settings = get_settings()
    client = get_groq_client()
    
    if model is None:
        model = settings.groq_model
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that generates valid JSON responses. Always respond with valid, parseable JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}  # Enforce JSON output
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Groq")
        
        # Parse and return JSON
        return json.loads(content)
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Groq response: {e}")
    except Exception as e:
        raise Exception(f"Groq API call failed: {e}")


def groq_generate_text(
    prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    system_prompt: str | None = None,
) -> str:
    """
    Generate text response from Groq.
    
    Args:
        prompt: The prompt to send to the model
        model: Model name (defaults to settings.groq_model)
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        system_prompt: Optional system prompt
        
    Returns:
        Generated text
        
    Raises:
        Exception: If API call fails
    """
    settings = get_settings()
    client = get_groq_client()
    
    if model is None:
        model = settings.groq_model
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Groq")
        
        return content
        
    except Exception as e:
        raise Exception(f"Groq API call failed: {e}")


def groq_chat(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Chat with Groq using conversation history.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name (defaults to settings.groq_model)
        temperature: Sampling temperature (0-2)
        max_tokens: Maximum tokens to generate
        
    Returns:
        Generated response text
        
    Raises:
        Exception: If API call fails
    """
    settings = get_settings()
    client = get_groq_client()
    
    if model is None:
        model = settings.groq_model
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from Groq")
        
        return content
        
    except Exception as e:
        raise Exception(f"Groq API call failed: {e}")
