"""
NeuroFlow AI Telegram Bot - Main Entry Point
python-telegram-bot v20+ async bot
"""

import asyncio
import json
import os
import uuid
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

from config import (
    BOT_TOKEN,
    ADMIN_CHAT_ID,
    PRICES,
    FREE_SCRAPES,
    PLANS,
    PAYMENT_METHODS,
    GUMROAD_PRODUCTS,
    DATA_DIR,
    OUTPUT_DIR,
)
from services.scraper import run_scraper
from services.analyzer import run_analysis
from services.writer import generate_content
from services.sheets import log_order
from services.payment import generate_payment_link
from services.nlu import detect_intent, chat_response, _is_tamil, tamil_intent_response
from services.voice import voice_reply, generate_voice_response

# ---------------------------------------------------------------------------
# User & Order DB helpers
# ---------------------------------------------------------------------------

def load_users():
    path = os.path.join(DATA_DIR, "users.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(os.path.join(DATA_DIR, "users.json"), "w") as f:
        json.dump(users, f, indent=2)

def get_user(user_id: str) -> dict:
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "id": uid,
            "username": "",
            "first_seen": datetime.now().isoformat(),
            "free_scrapes_used": 0,
            "plan": "free",
            "total_spent": 0,
        }
        save_users(users)
    return users[uid]

def update_user(user_id: str, updates: dict):
    users = load_users()
    uid = str(user_id)
    if uid not in users:
        get_user(uid)
        users = load_users()
    users[uid].update(updates)
    save_users(users)

# ---------------------------------------------------------------------------
# Order helpers
# ---------------------------------------------------------------------------

def create_order(user_id: str, service: str, amount: float, details: str = "") -> str:
    order_id = str(uuid.uuid4())[:8].upper()
    orders = []
    path = os.path.join(DATA_DIR, "orders.json")
    if os.path.exists(path):
        with open(path) as f:
            orders = json.load(f)
    orders.append({
        "order_id": order_id,
        "user_id": str(user_id),
        "service": service,
        "amount": amount,
        "details": details,
        "status": "pending",
        "created": datetime.now().isoformat(),
    })
    with open(path, "w") as f:
        json.dump(orders, f, indent=2)
    return order_id

def complete_order(order_id: str):
    path = os.path.join(DATA_DIR, "orders.json")
    if os.path.exists(path):
        with open(path) as f:
            orders = json.load(f)
        for o in orders:
            if o["order_id"] == order_id:
                o["status"] = "completed"
                o["completed"] = datetime.now().isoformat()
        with open(path, "w") as f:
            json.dump(orders, f, indent=2)

# ---------------------------------------------------------------------------
# Admin notification
# ---------------------------------------------------------------------------

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, text: str):
    """Send notification to CEO."""
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
        except Exception:
            pass  # Admin not set up yet

# ---------------------------------------------------------------------------
# /start command
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id)
    update_user(user.id, {"username": user.username or ""})

    welcome = f"""
🚀 *NeuroFlow AI Bot*

Hi {user.first_name}!

I can scrape websites, analyze data & write content — all through chat.

*3 FREE scrapes — no catch!*

Try now: send any URL or try:
/scrape https://books.toscrape.com

*Commands:*
/scrape — Scrape any website
/analyze — Upload CSV for analysis
/write — AI content generation
/price — Pricing & plans
/help — All commands

🔥 *Share this bot with friends:*
Forward this message or share @neuroflowfz_Bot
""".strip()
    await update.message.reply_text(welcome, parse_mode=ParseMode.MARKDOWN)

    # Notify admin
    await notify_admin(context, f"New user: {user.first_name} (@{user.username or 'no-username'}) [ID: {user.id}]")

# ---------------------------------------------------------------------------
# /help command
# ---------------------------------------------------------------------------

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
*Commands:*
/scrape <url> - Scrape data from website
/analyze - Upload CSV for analysis
/write <topic> - Generate blog/article
/catalog - Browse digital products
/price - See pricing & plans
/status - Check your usage
/support - Contact human support

*How it works:*
1. Send a task (/scrape, /analyze, /write)
2. If you have free credits, I process immediately
3. If not, I send a payment link
4. Pay -> I deliver your result

Questions? /support
""".strip()
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------------------------------
# /price command
# ---------------------------------------------------------------------------

async def cmd_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    free_left = max(0, FREE_SCRAPES - user.get("free_scrapes_used", 0))

    text = f"""
*Pricing*

*Pay-Per-Use:*
- Small scrape (<100 items): $3
- Medium scrape (100-1000): $7
- Large scrape (1000-5000): $15
- Data analysis report: $8
- Blog post / article: $10
- Social media post: $5

*Your Status:*
Free scrapes remaining: *{free_left}*
Current plan: *{user.get('plan', 'free').title()}*

*Subscriptions:*
- Pro ($9/mo): 50 scrapes/month + Sheets export
- Business ($29/mo): Unlimited + API access

Pay via Binance Pay, PayHere, or bank transfer.
""".strip()
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------------------------------
# /scrape command
# ---------------------------------------------------------------------------

async def cmd_scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    free_used = user.get("free_scrapes_used", 0)

    # Parse URL from command
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /scrape <url>\nExample: /scrape https://books.toscrape.com\n\n"
            "Or just send me a URL directly!"
        )
        return

    url = args[0]
    if not url.startswith("http"):
        url = "https://" + url

    # Check free tier
    if user.get("plan") != "free" or free_used < FREE_SCRAPES:
        # Process now (free)
        await update.message.reply_text(f"Processing: {url}\nThis may take 1-2 minutes...")

        result = await run_scraper(url)
        if result.get("success"):
            update_user(user_id, {"free_scrapes_used": free_used + 1})
            await update.message.reply_text(
                f"*Scrape Complete!*\nItems found: {result['count']}\n"
                f"Free scrapes left: {max(0, FREE_SCRAPES - free_used - 1)}",
                parse_mode=ParseMode.MARKDOWN,
            )
            # Send CSV
            if result.get("csv_path"):
                await update.message.reply_document(
                    document=open(result["csv_path"], "rb"),
                    filename=f"scrape_{url.replace('https://', '').split('/')[0]}.csv",
                )
        else:
            await update.message.reply_text(f"Error: {result.get('error', 'Unknown error')}")
    else:
        # Need payment
        order_id = create_order(user_id, "scrape", PRICES["scrape_small"], url)
        pay_info = generate_payment_link(order_id, PRICES["scrape_small"])
        await update.message.reply_text(
            f"*Free scrapes used up!*\n"
            f"Pay ${PRICES['scrape_small']} to continue.\n\n{pay_info}",
            parse_mode=ParseMode.MARKDOWN,
        )
        await notify_admin(context, f"Payment needed: Order #{order_id} - ${PRICES['scrape_small']} from user {user_id}")

# ---------------------------------------------------------------------------
# /catalog command
# ---------------------------------------------------------------------------

async def cmd_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "*Digital Products*\n\n"
    for p in GUMROAD_PRODUCTS:
        text += f"- *{p['name']}* — ${p['price']}\n  {p['desc']}\n  [Buy on Gumroad]({p['url']})\n\n"

    text += "More products coming soon!"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

# ---------------------------------------------------------------------------
# /status command
# ---------------------------------------------------------------------------

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(str(update.effective_user.id))
    free_left = max(0, FREE_SCRAPES - user.get("free_scrapes_used", 0))
    text = f"""
*Your Status*
Plan: {user.get('plan', 'free').title()}
Free scrapes left: {free_left}
Total spent: ${user.get('total_spent', 0)}
""".strip()
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------------------------------
# /support command
# ---------------------------------------------------------------------------

async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Need help? Contact us at neuroflowai.official@gmail.com\n"
        "We'll get back to you within 24 hours."
    )
    await notify_admin(
        context,
        f"Support request from {update.effective_user.first_name} (@{update.effective_user.username})"
    )

# ---------------------------------------------------------------------------
# Handle direct URL messages (quick scrape)
# ---------------------------------------------------------------------------

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route plain text messages through NLU for smart responses."""
    text = update.message.text.strip()
    user = update.effective_user
    user_name = user.first_name

    # Extract URL first
    import re
    urls = re.findall(r'https?://[^\s]+', text)
    if urls:
        context.args = [urls[0]]
        await cmd_scrape(update, context)
        return

    # Route through NLU
    intent = detect_intent(text)
    is_tamil = _is_tamil(text)

    # Tamil input with known intent → hardcoded Tamil response
    if is_tamil and intent in ["help", "price", "scrape", "write", "analyze", "catalog", "owner", "greeting"]:
        reply = tamil_intent_response(intent)
        await update.message.reply_text(reply)
        return

    if intent == "help":
        await cmd_help(update, context)
    elif intent == "price":
        await cmd_price(update, context)
    elif intent == "scrape":
        await update.message.reply_text(
            f"Sure! Send me the URL you want to scrape.\nExample: /scrape https://example.com",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif intent == "write":
        # Extract topic from message
        topic = text
        for kw in ["write", "content about", "blog about", "article about", "generate"]:
            topic = topic.lower().replace(kw, "").strip()
        if topic:
            context.args = topic.split()
            await cmd_write(update, context)
        else:
            await update.message.reply_text("What topic should I write about?\nExample: /write AI automation benefits")
    elif intent == "analyze":
        await update.message.reply_text("Send me a CSV or Excel file and I'll analyze it!")
    elif intent == "catalog":
        await cmd_catalog(update, context)
    elif intent == "owner":
        await update.message.reply_text(
            "I'm built and operated by *NeuroFlow AI*, founded by CEO *Fyruz*. 🚀\n"
            "A solo founder from Sri Lanka building AI automation tools.\n"
            "Contact: neuroflowai.official@gmail.com",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        # Use Ollama for natural conversation
        reply = await chat_response(text, user_name)
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)

# ---------------------------------------------------------------------------
# Handle file uploads (CSV for analysis)
# ---------------------------------------------------------------------------

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """When user sends a CSV/Excel file, offer analysis."""
    doc = update.message.document
    if doc.file_name and doc.file_name.endswith(('.csv', '.xlsx', '.xls')):
        file = await doc.get_file()
        filepath = os.path.join(OUTPUT_DIR, doc.file_name)
        await file.download_to_drive(filepath)

        await update.message.reply_text(
            f"Got *{doc.file_name}*! Running analysis...",
            parse_mode=ParseMode.MARKDOWN,
        )

        result = await run_analysis(filepath)
        if result.get("success"):
            await update.message.reply_text(result["summary"], parse_mode=ParseMode.MARKDOWN)
            if result.get("report_path"):
                await update.message.reply_document(
                    document=open(result["report_path"], "rb"),
                    filename="analysis_report.md",
                )
        else:
            await update.message.reply_text(f"Analysis error: {result.get('error')}")

# ---------------------------------------------------------------------------
# /write command
# ---------------------------------------------------------------------------

async def cmd_write(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /write <topic>\nExample: /write benefits of AI automation"
        )
        return

    topic = " ".join(args)
    await update.message.reply_text(f"Writing about: *{topic}*...", parse_mode=ParseMode.MARKDOWN)

    result = await generate_content(topic)
    if result.get("success"):
        await update.message.reply_text(result["content"][:4000], parse_mode=ParseMode.MARKDOWN)
        if len(result["content"]) > 4000:
            await update.message.reply_text("(Content truncated. Full version available on request.)")
    else:
        await update.message.reply_text(f"Error: {result.get('error')}")

# ---------------------------------------------------------------------------
# Voice message handler (Tamil + English STT + TTS)
# ---------------------------------------------------------------------------

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages: STT → NLU → reply text + TTS voice reply."""
    user = update.effective_user
    user_name = user.first_name

    # 1. Download voice file
    voice = update.message.voice
    voice_file = await voice.get_file()
    audio_path = os.path.join(OUTPUT_DIR, f"voice_{uuid.uuid4().hex[:8]}.ogg")
    await voice_file.download_to_drive(audio_path)

    # 2. STT: voice → text
    await update.message.reply_text("🎤 கேட்கிறேன்... / Listening...")
    result = await voice_reply(audio_path)

    if not result["success"]:
        await update.message.reply_text("மன்னிக்கவும், voice-ஐ understand பண்ண முடியல. Text-ல try பண்ணுங்க.")
        return

    text = result["text"]
    lang = result["lang"]

    # 3. Route through NLU
    intent = detect_intent(text)
    is_tamil = _is_tamil(text) or lang == "ta"

    # Get text response
    if is_tamil and intent in ["help", "price", "scrape", "write", "analyze", "catalog", "owner", "greeting"]:
        reply_text = tamil_intent_response(intent)
    elif intent == "help":
        reply_text = "Here are my commands:\n/scrape, /write, /analyze, /price, /catalog, /help"
    elif intent == "owner":
        reply_text = "I'm built by NeuroFlow AI, CEO Fyruz."
    elif intent == "price":
        reply_text = "Web Scraping $3-15 | Data Analysis $8 | Content $5-10"
    else:
        reply_text = await chat_response(text, user_name)

    # 4. Send text reply
    await update.message.reply_text(f"📝 *{text}*\n\n{reply_text}", parse_mode=ParseMode.MARKDOWN)

    # 5. Generate & send voice reply
    try:
        voice_lang = "ta" if (is_tamil or lang == "ta") else "en"
        voice_path = await generate_voice_response(reply_text, voice_lang)
        if voice_path and os.path.exists(voice_path):
            await update.message.reply_voice(voice=open(voice_path, "rb"))
    except Exception as e:
        print(f"[VOICE REPLY ERROR] {e}")

    # Cleanup audio
    try:
        os.remove(audio_path)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Start the bot."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("ERROR: BOT_TOKEN not set!")
        print("1. Create bot on @BotFather in Telegram")
        print("2. Set NEUROFLOW_BOT_TOKEN environment variable")
        print("   export NEUROFLOW_BOT_TOKEN=your_token_here")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("price", cmd_price))
    app.add_handler(CommandHandler("scrape", cmd_scrape))
    app.add_handler(CommandHandler("catalog", cmd_catalog))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("support", cmd_support))
    app.add_handler(CommandHandler("write", cmd_write))
    app.add_handler(CommandHandler("analyze", lambda u, c: u.message.reply_text("Send me a CSV/Excel file and I'll analyze it!")))

    # Message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("NeuroFlow AI Bot starting...")
    print("Press Ctrl+C to stop")
    app.run_polling()

if __name__ == "__main__":
    main()
