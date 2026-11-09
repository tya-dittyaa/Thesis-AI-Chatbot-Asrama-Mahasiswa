"""
ClarioHub OpenAI-Compatible Client Adapter
=========================================
Menyediakan integrasi ke gateway ClarioHub (https://api.clariohub.id/v1)
dengan library `openai` standar untuk model Gemini dan lainnya.
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Paths
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = BASE_DIR.parent
load_dotenv(WORKSPACE_ROOT / ".env", override=True)


def get_clario_client() -> OpenAI:
    api_key = os.getenv("CLARIO_API_KEY", "").strip()
    if not api_key or api_key == "sk-clario-YOUR_API_KEY_HERE":
        raise ValueError(
            "CLARIO_API_KEY belum disetel di file .env!\n"
            "Format: CLARIO_API_KEY=sk-clario-xxxxxx\n"
            "Dapatkan di: https://clariohub.id/dashboard"
        )
    base_url = os.getenv("CLARIO_BASE_URL", "https://api.clariohub.id/v1").strip()
    return OpenAI(base_url=base_url, api_key=api_key)


def list_clario_models() -> list[str]:
    client = get_clario_client()
    models = client.models.list()
    return [m.id for m in models.data]


def call_clario_completion(
    messages: list[dict],
    model: str = None,
    tools: list[dict] = None,
    temperature: float = 0.1,
    response_format: dict = None,
    max_retries: int = 5
) -> tuple[dict, str, float, int, int]:
    """
    Memanggil ClarioHub API dengan standar OpenAI chat.completions.
    Returns: (parsed_json_or_tool_args, raw_content, latency_sec, prompt_tokens, completion_tokens)
    """
    client = get_clario_client()
    model_name = model or os.getenv("CLARIO_MODEL", "clario/gemini-2.5-flash")

    params = {
        "model": model_name,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        formatted_tools = []
        for t in tools:
            if "function" in t:
                formatted_tools.append(t)
            elif "name" in t and "parameters" in t:
                formatted_tools.append({"type": "function", "function": t})
            else:
                formatted_tools.append(t)
        params["tools"] = formatted_tools
        params["tool_choice"] = "auto"
    if response_format:
        params["response_format"] = response_format

    t0 = time.time()
    response = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**params)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 * (attempt + 1)
                time.sleep(wait)
            else:
                raise e

    latency = time.time() - t0
    choice = response.choices[0]
    usage = response.usage
    p_tokens = getattr(usage, "prompt_tokens", 0) or 0
    c_tokens = getattr(usage, "completion_tokens", 0) or 0

    # 1. Jika ada Tool/Function Calling
    if choice.message.tool_calls:
        tc = choice.message.tool_calls[0]
        fn_args = {}
        try:
            fn_args = json.loads(tc.function.arguments)
        except Exception:
            pass
        return fn_args, tc.function.name, latency, p_tokens, c_tokens

    # 2. Text / JSON content biasa
    raw_text = choice.message.content or ""
    parsed_json = {}
    try:
        parsed_json = json.loads(raw_text.strip())
    except Exception:
        # Fallback regex JSON
        import re
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if match:
            try:
                parsed_json = json.loads(match.group(1))
            except Exception:
                pass
        else:
            s, e = raw_text.find("{"), raw_text.rfind("}")
            if s != -1 and e != -1 and e > s:
                try:
                    parsed_json = json.loads(raw_text[s:e+1])
                except Exception:
                    pass

    return parsed_json, raw_text, latency, p_tokens, c_tokens
