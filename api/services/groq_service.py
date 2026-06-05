from __future__ import annotations

import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a SAP Procure-to-Pay (P2P) Data Assistant for an intelligent risk monitoring platform.

STRICT RULES — YOU MUST FOLLOW ALL OF THEM:
1. Answer ONLY using facts explicitly present in the retrieved context provided below.
2. NEVER invent, assume, or extrapolate values, names, scores, or identifiers not found in the context.
3. If the context does not contain enough information, respond EXACTLY with this sentence:
   "I do not have enough information in the available datasets to answer that question."
4. Write professional, business-oriented English. Be concise and factual.
5. Format numerical values clearly: risk scores to 2 decimal places, amounts with currency when available.
6. When referencing specific records, always include the record identifier (e.g. Supplier ID, Transaction ID).
7. Use professional phrasing for risk classifications: LOW, MEDIUM, HIGH, CRITICAL.
8. Never add commentary outside what the data supports."""


def generate_answer(context: str, question: str) -> str:
    """Call Groq API to generate a grounded answer from retrieved context."""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        logger.warning("GROQ_API_KEY not configured — LLM answer unavailable")
        return ""

    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    url = "https://api.groq.com/openai/v1/chat/completions"

    user_content = (
        "The following data has been retrieved from the P2P monitoring datasets:\n\n"
        "---\n"
        f"{context}\n"
        "---\n\n"
        f"Question: {question}\n\n"
        "Provide a professional, concise answer strictly based on the retrieved data above. "
        "Do not use information outside the provided context."
    )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.0,
        "max_tokens": 900,
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
            return (content or "").strip()
        logger.warning("Groq returned no choices: %s", data)
        return ""
    except requests.exceptions.HTTPError as e:
        logger.error("Groq HTTP error %s: %s", e.response.status_code, e.response.text[:300])
        return ""
    except Exception:
        logger.exception("Groq API call failed")
        return ""
