"""
NeuroFlow AI Bot - NLU (Natural Language Understanding)
Routes user messages to appropriate handlers using Ollama + keyword matching
"""

import subprocess
import json
import re


# Quick keyword intent matching (no LLM needed)
INTENT_KEYWORDS = {
    "owner": ["who owns", "who made", "who created", "who built", "your owner", "your creator", "who is behind", "company behind", "who runs", "your boss", "who is your boss"],
    "help": ["what can you do", "help", "how does", "how to use", "what is", "who are you", "about you", "commands", "menu", "what do you", "features", "capable"],
    "price": ["price", "pricing", "cost", "how much", "payment", "pay", "free", "charge", "subscription", "plan"],
    "scrape": ["scrape", "scraping", "extract data", "crawl", "get data from", "pull data"],
    "write": ["write", "content", "blog", "article", "generate text", "create post"],
    "analyze": ["analyze", "analysis", "csv", "excel", "data report", "statistics"],
    "catalog": ["product", "buy", "purchase", "catalog", "store", "shop", "gumroad"],
}


def detect_intent(text: str) -> str:
    """Quick keyword-based intent detection. Returns intent name or 'chat'."""
    text_lower = text.lower().strip()

    # Exact command match
    if text_lower.startswith("/"):
        return "command"

    # Check keywords
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return intent

    # If no keywords match, it's a chat / general question
    return "chat"


async def chat_response(user_input: str, user_name: str = "") -> str:
    """
    Use Ollama to generate a natural, helpful response.
    Falls back to static help text if Ollama unavailable.
    """
    try:
        prompt = f"""You are NeuroFlow AI Bot, a helpful Telegram bot assistant. 
You help users with: web scraping ($3-15), data analysis ($8), content writing ($5-10).
First 3 scrapes are free. Commands: /scrape, /analyze, /write, /price, /catalog, /help.

IMPORTANT FACTS ABOUT YOU:
- You are owned and operated by NeuroFlow AI, founded by CEO Fyruz.
- Your boss/creator/owner is Fyruz, the CEO of NeuroFlow AI.
- You run on Python + Ollama AI, hosted locally.
- If anyone asks who owns you, who made you, or who's behind this — ALWAYS say: "I'm built and operated by NeuroFlow AI, founded by CEO Fyruz."

A user named {user_name} said: "{user_input}"

Respond in 1-3 SHORT sentences. Be friendly and helpful. Guide them to relevant commands.
If you don't understand, direct them to /help. Use Telegram-parseable text (no markdown tables).
NEVER mention being an AI or language model. Speak like a helpful human assistant."""

        result = subprocess.run(
            [
                "curl", "-s", "http://localhost:11434/api/generate",
                "-d", json.dumps({
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 150}
                })
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            response = json.loads(result.stdout)
            text = response.get("response", "").strip()
            if text and len(text) > 5:
                return text

    except Exception:
        pass

    # Fallback
    return (
        "I can help with web scraping, data analysis, and content writing!\n"
        "Try /scrape <url>, /write <topic>, or /help to see all commands."
    )
