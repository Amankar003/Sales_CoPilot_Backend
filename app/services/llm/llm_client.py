"""
llm_client.py - Centralized LLM service using Groq.
"""

import json
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.core.settings import settings
from app.utils.logger import get_logger
from app.utils.parser import safe_json_loads

logger = get_logger(__name__)


class LLMClient:
    """
    Centralized client for interacting with the Groq LLM API.
    Supports routing between heavy and light models for cost/performance optimization.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.base_url = settings.GROQ_BASE_URL
        self.heavy_model = settings.GROQ_HEAVY_MODEL
        self.light_model = settings.GROQ_LIGHT_MODEL

    def _get_model(self, task_type: str, json_mode: bool = False, temperature: float = 0.7) -> Optional[ChatOpenAI]:
        """
        Initialize the LangChain ChatOpenAI instance pointing to Groq.
        """
        if not settings.has_groq_key:
            return None

        # Determine the correct model based on task type
        model_name = self.heavy_model if task_type == "heavy" else self.light_model

        kwargs = {}
        if json_mode:
            # Note: Groq supports response_format={"type": "json_object"} on supported models
            kwargs["response_format"] = {"type": "json_object"}

        return ChatOpenAI(
            model=model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=temperature,
            model_kwargs=kwargs,
            max_retries=2,
            request_timeout=30.0,
        )

    def _mock_response(self, fallback: Any) -> Any:
        """Return the mock fallback response."""
        logger.info("Using mock fallback response.")
        return fallback

    def _safe_parse_json(self, content: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Safely parse JSON from the LLM response. 
        If it fails, attempt to extract JSON block or return fallback.
        """
        parsed = safe_json_loads(content, None)
        if parsed is not None:
            return parsed
            
        # Fallback extraction logic (if pure parsing failed, try finding code blocks)
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to extract JSON from LLM response: {e}")
            
        logger.warning("Could not parse LLM response into JSON. Returning fallback.")
        return fallback

    async def _call_groq(
        self, 
        task_type: str, 
        system_prompt: str, 
        user_prompt: str, 
        json_mode: bool,
        temperature: float,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        Make the actual call to the Groq API via LangChain.
        """
        llm = self._get_model(task_type, json_mode, temperature)
        if not llm:
            return None

        try:
            # Combine system and user prompt for LangChain PromptTemplate
            full_template = f"{system_prompt}\n\n{user_prompt}"
            prompt = PromptTemplate(
                input_variables=list(variables.keys()),
                template=full_template,
            )
            
            chain = prompt | llm
            
            logger.info(f"Calling Groq LLM (Model: {llm.model_name}, Task: {task_type})")
            response = await chain.ainvoke(variables)
            
            return response.content
            
        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            # Handle rate limits, timeouts, etc gracefully without crashing
            return None

    async def generate_text(
        self,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
        fallback: str,
        variables: Dict[str, Any] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate plain text using the specified model type.
        """
        vars_dict = variables or {}
        content = await self._call_groq(
            task_type=task_type,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
            temperature=temperature,
            variables=vars_dict
        )
        
        if content is None:
            return self._mock_response(fallback)
            
        return content.strip()

    async def generate_json(
        self,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
        fallback: Dict[str, Any],
        variables: Dict[str, Any] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON using the specified model type.
        """
        vars_dict = variables or {}
        content = await self._call_groq(
            task_type=task_type,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
            temperature=temperature,
            variables=vars_dict
        )
        
        if content is None:
            return self._mock_response(fallback)
            
        return self._safe_parse_json(content, fallback)


# Export singleton instance
llm_client = LLMClient()
