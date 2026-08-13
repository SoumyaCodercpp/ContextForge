import os
import time
from dataclasses import dataclass, field
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "deepseek-chat")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")

MAX_RETRIES = 2
RETRY_DELAY = 1.0

SYSTEM_PROMPT = """You are a helpful, accurate assistant. Answer the user's question
based ONLY on the provided context. If the context doesn't contain enough
information to answer the question, say so clearly. Do not make up information.

Follow these guidelines:
- Be concise and direct.
- Cite specific details from the context when relevant.
- If the context is insufficient, say: "The provided context does not contain enough information to answer this question."
- Do not mention that you are using "context" or "provided text" in your answer unless necessary."""


@dataclass
class LLMResponse:
    answer: str
    model: str = ""
    token_usage: dict = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    })
    latency_ms: int = 0
    finish_reason: str = ""

    #response.total_tokens
    @property
    def total_tokens(self):
        return self.token_usage.get("total_tokens", 0)


def build_prompt(context, question):
    """Combine optimized context with the user's question."""
    return f"""Context:
---
{context}
---

Question: {question}

Answer:"""


def generate_answer(context, question, model_name=None, system_prompt=None,
                    temperature=0.3, max_output_tokens=2048):
    """
    Send optimized context + question to the LLM and get the answer.
    Works with any OpenAI-compatible API (DeepSeek, Groq, ChatGPT, etc.)
    """
    if not context or not context.strip():
        raise ValueError("Context cannot be empty.")
    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")
    
    url = f"{OPENAI_BASE_URL}/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model_name or OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt or SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(context, question)},
        ],
        "temperature": temperature,
        "max_tokens": max_output_tokens,
    }
    
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start = time.perf_counter()
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}: {response.text}"
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                continue
            
            data = response.json()
            elapsed = int((time.perf_counter() - start) * 1000)
            
            choice = data["choices"][0]
            answer = choice["message"]["content"]
            finish_reason = choice.get("finish_reason", "")
            
            usage_data = data.get("usage", {})
            usage = {
                "prompt_tokens": usage_data.get("prompt_tokens", 0),
                "completion_tokens": usage_data.get("completion_tokens", 0),
                "total_tokens": usage_data.get("total_tokens", 0),
            }
            
            return LLMResponse(
                answer=answer,
                model=model_name or OPENAI_MODEL,
                token_usage=usage,
                latency_ms=elapsed,
                finish_reason=finish_reason,
            )
            
        except requests.RequestException as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
    
    raise RuntimeError(f"LLM API failed after {MAX_RETRIES} retries. Last error: {last_error}")