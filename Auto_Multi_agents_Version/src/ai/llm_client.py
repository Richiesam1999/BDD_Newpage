"""
LLM Client - Interface to Ollama for AI-powered analysis
"""
import logging
import httpx
import json
from typing import Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM"""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or config.OLLAMA_URL
        self.model = model or config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
    
    async def generate(self, prompt: str, system_prompt: str = None, 
                      temperature: float = None) -> str:
        """
        Generate text completion using Ollama
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0.0-1.0)
            
        Returns:
            Generated text response
        """
        temperature = temperature if temperature is not None else config.TEMPERATURE
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "").strip()
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {str(e)}")
            raise
    
    async def generate_json(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Generate structured JSON response
        
        Args:
            prompt: User prompt (should request JSON output)
            system_prompt: Optional system instructions
            
        Returns:
            Parsed JSON object
        """
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No explanations, no markdown."
        
        response_text = await self.generate(json_prompt, system_prompt, temperature=0.3)
        
        # Clean response (remove markdown if present)
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {cleaned}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    async def check_health(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
    
    async def list_models(self) -> list:
        """List available models"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []