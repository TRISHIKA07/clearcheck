"""
ComplianceCore AI Interface Module.
Handles local Ollama connection, retry logic, timeout configuration, and JSON parsing.
This is the ONLY module containing AI/LLM inference calls.
"""

import json
import logging
import time
from typing import Optional, Dict, Any
from ollama import Client, RequestError, ResponseError
import config
from utils import setup_logging

logger = logging.getLogger("ComplianceCore.AI")

# Configure Ollama Client
client = Client(
    host=config.OLLAMA_BASE_URL,
    timeout=config.OLLAMA_TIMEOUT_SECONDS
)

def verify_ollama_connection() -> bool:
    """
    Verifies that the local Ollama service is running and has the model pulled.
    """
    try:
        models_response = client.list()
        available_models = [m.model for m in models_response.models]
        logger.info(f"Connected to Ollama. Available models: {available_models}")
        
        # Check if the requested model is pulled
        # Standard model check (matches both exact 'gemma4:e4b' and sometimes tag variants)
        if config.GEMMA_MODEL_NAME not in available_models:
            # Check if it has a trailing :latest or similar
            matches = [m for m in available_models if m.startswith(config.GEMMA_MODEL_NAME)]
            if not matches:
                logger.warning(
                    f"Model '{config.GEMMA_MODEL_NAME}' not found in Ollama. "
                    f"Available: {available_models}. Attempting to pull or run directly..."
                )
                return False
        return True
    except Exception as e:
        logger.error(f"Failed to connect to local Ollama service: {e}")
        return False

def clean_and_parse_json(raw_text: str) -> Optional[dict[str, Any]]:
    """
    Robust JSON parser that extracts JSON blocks from LLM output.
    """
    if not raw_text:
        return None
        
    cleaned = raw_text.strip()
    
    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Extract JSON between first '{' and last '}'
    try:
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = cleaned[start_idx:end_idx + 1]
            return json.loads(json_str)
    except Exception as e:
        logger.warning(f"Failed to extract and parse JSON from: {cleaned[:200]}... Error: {e}")
        
    return None

def get_fallback_gemma_response(error_message: str) -> dict[str, Any]:
    """
    Generates a structured dictionary matching the GemmaResponse schema
    when Ollama/Gemma fails.
    """
    return {
        "executive_summary": f"System Warning: Local AI compliance review failed due to system error: {error_message}",
        "compliance_decision": "ESCALATED",
        "evidence": f"Inference pipeline execution error: {error_message}",
        "severity": "High",
        "confidence": 0.0,
        "audit_summary": "Automatic audit incomplete. Local AI reasoning was offline or timed out.",
        "recommendations": [
            "Verify local Ollama service is running.",
            f"Ensure the '{config.GEMMA_MODEL_NAME}' model is pulled (`ollama pull {config.GEMMA_MODEL_NAME}`).",
            "Perform manual transaction review and verification of customer PII."
        ]
    }

def call_gemma(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 2048
) -> dict[str, Any]:
    """
    Calls local Gemma model using Ollama with retry logic, timeout, and JSON validation.
    Returns a dictionary structured as GemmaResponse.
    """
    logger.info(f"Invoking local Gemma ({config.GEMMA_MODEL_NAME}) with temperature={temperature}")
    
    # Construct messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    retries = config.OLLAMA_MAX_RETRIES
    delay = 2.0  # seconds
    
    last_error = "Unknown Error"

    # Pre-flight check
    if not verify_ollama_connection():
        err_msg = "Ollama connection verification failed. Local daemon might be offline."
        logger.error(err_msg)
        return get_fallback_gemma_response(err_msg)

    for attempt in range(1, retries + 1):
        try:
            # Call Ollama
            response = client.chat(
                model=config.GEMMA_MODEL_NAME,
                messages=messages,
                format="json",  # Enforce JSON mode
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            )
            
            content = response.message.content
            logger.info(f"Ollama response received successfully on attempt {attempt}.")
            
            parsed_json = clean_and_parse_json(content)
            if parsed_json is not None:
                # Validate minimal structure keys
                required_keys = ["executive_summary", "compliance_decision", "evidence", "severity", "confidence"]
                # Auto-fill missing keys with default values if some are absent
                for key in required_keys:
                    if key not in parsed_json:
                        if key == "compliance_decision":
                            parsed_json[key] = "ESCALATED"
                        elif key == "confidence":
                            parsed_json[key] = 0.5
                        else:
                            parsed_json[key] = "N/A"
                if "audit_summary" not in parsed_json:
                    parsed_json["audit_summary"] = parsed_json.get("executive_summary", "N/A")
                if "recommendations" not in parsed_json:
                    parsed_json["recommendations"] = []
                    
                return parsed_json
            else:
                last_error = f"Ollama response did not contain parseable JSON: {content[:200]}..."
                logger.warning(f"Attempt {attempt} failed: {last_error}")
                
        except (RequestError, ResponseError) as oe:
            last_error = f"Ollama specific error: {oe}"
            logger.warning(f"Attempt {attempt} failed with Ollama exception: {oe}")
        except Exception as e:
            last_error = f"Unexpected error during inference: {e}"
            logger.warning(f"Attempt {attempt} failed with exception: {e}")
            
        # Wait before retrying (exponential backoff)
        if attempt < retries:
            time.sleep(delay)
            delay *= 2

    logger.error(f"All {retries} attempts failed. Returning structured fallback. Last error: {last_error}")
    return get_fallback_gemma_response(last_error)
