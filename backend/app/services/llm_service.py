# backend/app/services/llm_service.py

import json
import logging
import os
from typing import Any, Dict, Optional, AsyncGenerator
from groq import AsyncGroq
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(dotenv_path)
logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = AsyncGroq(
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.model = "llama-3.3-70b-versatile"
        self.max_tokens = 4096
    
    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """Call Groq API as Llama"""
        try:
            message = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=temperature
            )
            
            content = message.choices[0].message.content
            if content:
                return content
            
            raise ValueError("Unexpected empty response from Groq")
        
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    async def call_llm_json(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call Groq and parse JSON response"""
        
        # Add JSON instruction to prompt
        json_instruction = f"""
You MUST respond ONLY with valid JSON that matches this schema:
{json.dumps(response_schema, indent=2) if response_schema else "{}"}

Do NOT include any markdown backticks, code blocks, or text outside the JSON.
Start directly with {{ and end with }}.
        """.strip()
        
        full_prompt = f"{user_prompt}\n\n{json_instruction}"
        
        try:
            # We can use Groq JSON mode
            message = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            response_text = message.choices[0].message.content
            
            if not response_text:
                raise ValueError("Unexpected empty response from Groq")
            
            # Clean up response just in case
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                logger.error(f"Response was: {response_text}")
                raise ValueError(f"Failed to parse Groq response as JSON: {e}")
                
        except Exception as e:
            logger.error(f"Groq API JSON error: {e}")
            raise
    
    async def stream_llm(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> AsyncGenerator[str, None]:
        """Stream Groq response"""
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            stream=True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content