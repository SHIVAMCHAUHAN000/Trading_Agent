"""
LLM Client and Fallback Engine for Live Quant Brain.
Integrates with OpenAI, Google Gemini, or falls back to the deterministic Quant Reasoner.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional
from config.quant_brain_config import settings
from brain.reasoning import synthesize_quant_response
from brain.intent_classifier import QueryIntent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are the Live Quant Brain — a senior quant analyst and market intelligence engine.
Your purpose is decision support and objective market analysis, NOT blind trade recommendations or financial advice.

CRITICAL RULES:
1. NEVER hallucinate prices, volume, support/resistance, or market events. Only use numbers provided in the tool results.
2. If data is delayed or marked unavailable, explicitly state: "Data is delayed" or "Market data unavailable from the connected source."
3. Distinguish clearly between:
   - OBSERVED: Verifiable factual numbers.
   - INFERRED: Probabilistic transmission mechanisms.
   - UNKNOWN: Unconfirmed catalysts or missing information.
4. For broad queries, format response strictly using:
   📊 MARKET
   📈 TREND
   🏗 STRUCTURE
   💧 LIQUIDITY
   📦 VOLUME / MOMENTUM
   📰 DRIVERS
   🎯 SCENARIOS
   👀 WATCH
5. For short specific questions (e.g. price, simple trend, liquidity), give direct, concise answers with evidence.
"""


class QuantLLMClient:
    """Manages AI reasoning via OpenAI, Gemini LLM, or deterministic rule-based engine."""

    def __init__(self) -> None:
        self.openai_client = None
        self.gemini_client = None

        # 1. Initialize OpenAI client if configured
        if settings.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("Initialized OpenAI client with model %s", settings.OPENAI_MODEL)
            except Exception as e:
                logger.warning("Could not initialize OpenAI client: %s", e)

        # 2. Initialize Gemini client if configured
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Initialized Google Gemini client with model %s", settings.GEMINI_MODEL)
            except Exception as e:
                logger.warning("Could not initialize Gemini client: %s", e)

    async def generate_response(
        self,
        user_query: str,
        intent: QueryIntent,
        symbol: str,
        timeframe: str,
        tool_results: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generates analysis response using OpenAI or Gemini LLM if available,
        otherwise falls back to deterministic quant synthesizer.
        """
        import asyncio

        prompt_content = (
            f"User Query: {user_query}\n"
            f"Active Symbol: {symbol}\n"
            f"Active Timeframe: {timeframe}\n"
            f"Intent: {intent.value}\n\n"
            f"VERIFIED TOOL RESULTS (Use ONLY this data):\n"
            f"{json.dumps(tool_results, default=str, indent=2)}\n\n"
            "Synthesize a professional, quantitative, evidence-based response following the required format."
        )

        # 1. Try OpenAI if API key available and provider is 'openai' or 'auto'
        if self.openai_client and settings.AI_PROVIDER in ("openai", "auto"):
            try:
                def _call_openai():
                    completion = self.openai_client.chat.completions.create(
                        model=settings.OPENAI_MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt_content},
                        ],
                        temperature=0.2,
                        max_tokens=1200,
                    )
                    return completion.choices[0].message.content

                response_text = await asyncio.to_thread(_call_openai)
                if response_text and len(response_text.strip()) > 20:
                    return response_text.strip()
            except Exception as e:
                logger.error("OpenAI API generation error: %s, checking alternatives", e)

        # 2. Try Gemini if API key available and provider is 'gemini' or 'auto'
        if self.gemini_client and settings.AI_PROVIDER in ("gemini", "auto"):
            try:
                def _call_gemini():
                    response = self.gemini_client.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=[prompt_content],
                        config={"system_instruction": SYSTEM_PROMPT},
                    )
                    return response.text

                response_text = await asyncio.to_thread(_call_gemini)
                if response_text and len(response_text.strip()) > 20:
                    return response_text.strip()
            except Exception as e:
                logger.error("Gemini API generation error: %s, falling back to deterministic synthesizer", e)

        # 3. Deterministic high-precision quant fallback
        return synthesize_quant_response(
            intent=intent,
            user_query=user_query,
            symbol=symbol,
            timeframe=timeframe,
            tool_results=tool_results,
        )


# Global singleton LLM client
quant_llm_client = QuantLLMClient()
