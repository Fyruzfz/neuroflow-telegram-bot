"""
NeuroFlow AI Bot - NLU (Natural Language Understanding)
Routes user messages to appropriate handlers using Ollama + keyword matching
Supports both English and Tamil (auto-detect + respond in same language)
"""

import subprocess
import json


# Quick keyword intent matching (no LLM needed)
# Supports both English and Tamil
INTENT_KEYWORDS = {
    "owner": [
        "who owns", "who made", "who created", "who built", "your owner", "your creator",
        "who is behind", "company behind", "who runs", "your boss", "who is your boss",
        "yaar owner", "yaar unga owner", "yaar create", "yaar panna", "ungaloda owner",
        "yaru ungaloda", "evan pudu", "evan create", "yaaruka",
    ],
    "help": [
        "what can you do", "help", "how does", "how to use", "what is", "who are you",
        "about you", "commands", "menu", "what do you", "features", "capable",
        "enna panna mudiyum", "eppadi use", "eppadi", "help pannu", "enna commands",
        "nee yaaru", "unnala enna", "enna features",
    ],
    "price": [
        "price", "pricing", "cost", "how much", "payment", "pay", "free", "charge",
        "subscription", "plan",
        "vilai", "evvalavu", "rate", "kattanuma", "free aa", "subscription",
        "evlo", "panam", "kastam",
    ],
    "scrape": [
        "scrape", "scraping", "extract data", "crawl", "get data from", "pull data",
        "data edukka", "website la irundhu", "scrap pannu", "data venum",
    ],
    "write": [
        "write", "content", "blog", "article", "generate text", "create post",
        "eludhu", "blog eludhu", "article venum", "content venum", "kadhai",
    ],
    "analyze": [
        "analyze", "analysis", "csv", "excel", "data report", "statistics",
        "analysis pannu", "report venum", "csv file", "data paaru",
    ],
    "catalog": [
        "product", "buy", "purchase", "catalog", "store", "shop", "gumroad",
        "vaanga", "products", "enna irukku", "catalog kaatu",
    ],
}


# Latin-script Tamil words (commonly typed in English letters)
LATIN_TAMIL_WORDS = [
    "vanakkam", "nan", "enna", "ennada", "ennadi", "evvalavu", "evlo",
    "yaar", "yaaruka", "yaaru", "yaru", "ungaloda", "unnala", "pannu", "pannunga",
    "pannanum", "mudiyum", "irukku", "venum", "kudunga", "edukka",
    "eludhu", "paaru", "paakalam", "kidaikkum", "theriyuma", "puriyutha",
    "illai", "irukka", "varuthu", "pola", "mathiri", "kastam",
    "tamilla", "tamil la", "tamil-la", "tamizh", "pesu", "pesuviya",
    "sollu", "sollunga", "theriyadu", "nee", "neenga", "ungalukku",
    "da", "di", "pa", "ma", "thala", "boss", "anna", "akka",
]


def _is_tamil(text: str) -> bool:
    """Detect if input text is Tamil (Unicode OR Latin-script Tamil words)."""
    # Check Tamil Unicode chars (e.g., வணக்கம்)
    tamil_unicode = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    if tamil_unicode >= 3:
        return True

    # Check Latin-script Tamil words (e.g., vanakkam, enna, evvalavu)
    text_lower = text.lower()
    latin_hits = sum(1 for w in LATIN_TAMIL_WORDS if w in text_lower)
    return latin_hits >= 1


# Hardcoded Tamil responses (more reliable than 7B Ollama for Tamil)
TAMIL_RESPONSES = {
    "owner": (
        "Nan NeuroFlow AI company-oda bot. Enga CEO Fyruz. "
        "Avar Tamilnadu-la irundhu indha company run pannraru."
    ),
    "help": (
        "Nan ungaluku web scraping, data analysis, content writing help pannuven!\n"
        "Commands:\n"
        "/scrape <url> — website data edukkanum\n"
        "/analyze — CSV file analysis\n"
        "/write <topic> — content generate pannanum\n"
        "/price — vilai vivaram\n"
        "/catalog — products paarkanum\n\n"
        "First 3 scrapes free!"
    ),
    "price": (
        "Enga services vilai:\n"
        "• Web Scraping: $3 - $15\n"
        "• Data Analysis: $8\n"
        "• Content Writing: $5 - $10\n\n"
        "First 3 scrapes FREE!\n"
        "Payment: PayPal, Binance, UPI\n"
        "/catalog command la full details paakalam."
    ),
    "scrape": (
        "Website scrape panna /scrape <url> command use pannunga.\n"
        "Example: /scrape https://books.toscrape.com\n"
        "First 3 scrapes free! Data CSV format la kidaikkum."
    ),
    "write": (
        "Content eludha /write <topic> command use pannunga.\n"
        "Example: /write AI technology trends\n"
        "Blog, article, social media post — ellame generate pannuven."
    ),
    "analyze": (
        "Data analysis-ku unga CSV file-ah anuppunga.\n"
        "/analyze command use panni file upload pannunga.\n"
        "Statistics, charts, insights — report-ah kidaikkum."
    ),
    "catalog": (
        "Enga products:\n"
        "• Web Scraper Pack — $15\n"
        "• Data Analysis Suite — $25\n"
        "• Content Generator — $10\n"
        "Gumroad la purchase pannalaam. /price command la vilai vivaram paakalam."
    ),
    "greeting": (
        "Vanakkam! Nan NeuroFlow AI Bot.\n"
        "Web scraping, data analysis, content writing — ellathukkum help pannuven.\n"
        "/help command try pannunga!"
    ),
}


def tamil_intent_response(intent: str) -> str:
    """Return hardcoded Tamil response for known intent."""
    return TAMIL_RESPONSES.get(intent, TAMIL_RESPONSES["help"])


def detect_intent(text: str) -> str:
    """Quick keyword-based intent detection. Returns intent name or 'chat'."""
    text_lower = text.lower().strip()

    # Exact command match
    if text_lower.startswith("/"):
        return "command"

    # Check Tamil greetings first (vanakkam always = Tamil greeting)
    tamil_greetings = ["vanakkam", "ennada", "ennadi", "tamilla"]
    for g in tamil_greetings:
        if text_lower.startswith(g) or g in text_lower:
            return "greeting"

    # Check keywords
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return intent

    # If no keywords match, it's a chat / general question
    return "chat"


ENGLISH_PROMPT = """You are NeuroFlow AI Bot, a helpful Telegram bot assistant. 
You help users with: web scraping ($3-15), data analysis ($8), content writing ($5-10).
First 3 scrapes are free. Commands: /scrape, /analyze, /write, /price, /catalog, /help.

IMPORTANT FACTS ABOUT YOU:
- You are owned and operated by NeuroFlow AI, founded by CEO Fyruz.
- Your boss/creator/owner is Fyruz, the CEO of NeuroFlow AI.
- You run on Python + Ollama AI, hosted locally.
- If anyone asks who owns you, who made you, or who's behind this — ALWAYS say: "I'm built and operated by NeuroFlow AI, founded by CEO Fyruz."

A user said: "{user_input}"

Respond in 1-3 SHORT sentences in ENGLISH. Be friendly and helpful. Guide them to relevant commands.
If you don't understand, direct them to /help. Use Telegram-parseable text (no markdown tables).
NEVER mention being an AI or language model. Speak like a helpful human assistant."""

TAMIL_PROMPT = """You are NeuroFlow AI Bot, a Tamil-speaking Telegram bot assistant.
You help users with: web scraping ($3-15), data analysis ($8), content writing ($5-10).
First 3 scrapes are free. Commands: /scrape, /analyze, /write, /price, /catalog, /help.

IMPORTANT FACTS ABOUT YOU:
- You are owned and operated by NeuroFlow AI, founded by CEO Fyruz.
- Your boss/creator/owner is Fyruz, the CEO of NeuroFlow AI.
- If anyone asks who owns you — ALWAYS say in Tamil: "Ennai NeuroFlow AI company build pannirukku. Enga CEO Fyruz."

A Tamil user said: "{user_input}"

Respond in 2-3 SHORT sentences in TAMIL (Tamil script only, no English words).
Be friendly and helpful like a Tamil friend. Use natural spoken Tamil, not formal.
Guide them to relevant commands. NEVER mention being an AI or language model."""

ENGLISH_FALLBACK = (
    "I can help with web scraping, data analysis, and content writing!\n"
    "Try /scrape <url>, /write <topic>, or /help to see all commands."
)

TAMIL_FALLBACK = (
    "Nan ungaluku web scraping, data analysis, content writing help pannuven!\n"
    "/scrape <url>, /write <topic> try pannunga. /help kudutha ellame theriyum."
)


async def chat_response(user_input: str, user_name: str = "") -> str:
    """
    Use Ollama to generate a natural, helpful response.
    Auto-detects Tamil input and responds in Tamil.
    Falls back to static help text if Ollama unavailable.
    """
    is_tamil = _is_tamil(user_input)
    prompt_template = TAMIL_PROMPT if is_tamil else ENGLISH_PROMPT
    fallback = TAMIL_FALLBACK if is_tamil else ENGLISH_FALLBACK
    prompt = prompt_template.format(user_input=user_input)

    try:
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

    return fallback
