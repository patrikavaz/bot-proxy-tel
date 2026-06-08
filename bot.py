import os
import json
import asyncio
import httpx
from pathlib import Path
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
PROXY_URL = "https://raw.githubusercontent.com/SoliSpirit/mtproto/refs/heads/master/all_proxies.txt"
USERS_FILE = Path("users.json")
MAX_LENGTH = 4096


# ─── User Storage ────────────────────────────────────────────────────────────

def load_users() -> set:
    if USERS_FILE.exists():
        return set(json.loads(USERS_FILE.read_text()))
    return set()


def save_users(users: set):
    USERS_FILE.write_text(json.dumps(list(users)))


# ─── Proxy Fetcher ───────────────────────────────────────────────────────────

async def fetch_proxies() -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(PROXY_URL)
        r.raise_for_status()
        return r.text.strip()


def split_text(text: str, max_length: int = MAX_LENGTH) -> list[str]:
    lines = text.splitlines(keepends=True)
    chunks, current = [], ""
    for line in lines:
        if len(current) + len(line) > max_length:
            if current:
                chunks.append(current.rstrip())
            current = line
        else:
            current += line
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


async def send_to_user(bot: Bot, chat_id: int, content: str):
    total_lines = len([l for l in content.splitlines() if l.strip()])
    header = (
        f"🔄 *MTProto Proxy Update*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 `{total_lines}` proxies available\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    chunks = split_text(content)

    first = header + f"```\n{chunks[0]}\n```"
    await bot.send_message(chat_id=chat_id, text=first, parse_mode="Markdown")

    for chunk in chunks[1:]:
        await bot.send_message(
            chat_id=chat_id,
            text=f"```\n{chunk}\n```",
            parse_mode="Markdown"
        )
        await asyncio.sleep(0.3)


# ─── Command Handlers ─────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    users = load_users()
    is_new = chat_id not in users
    users.add(chat_id)
    save_users(users)

    if is_new:
        await update.message.reply_text(
            f"👋 سلام {user.first_name}!\n\n"
            f"✅ شما با موفقیت ثبت شدید.\n"
            f"هر ۱۲ ساعت یک‌بار لیست پروکسی‌های MTProto برای شما ارسال می‌شود.\n\n"
            f"برای دریافت فوری پروکسی‌ها همین الان دستور /proxies را بفرستید."
        )
    else:
        await update.message.reply_text(
            f"👋 سلام {user.first_name}!\n\n"
            f"✅ شما قبلاً ثبت شده‌اید و آپدیت‌ها را دریافت می‌کنید.\n"
            f"برای دریافت فوری پروکسی‌ها دستور /proxies را بفرستید."
        )


async def proxies_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ در حال دریافت پروکسی‌ها...")

    # Make sure user is registered
    users = load_users()
    users.add(chat_id)
    save_users(users)

    content = await fetch_proxies()
    await send_to_user(context.bot, chat_id, content)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = load_users()
    users.discard(chat_id)
    save_users(users)
    await update.message.reply_text(
        "❌ شما از لیست آپدیت‌ها حذف شدید.\n"
        "برای عضویت مجدد /start را بفرستید."
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    await update.message.reply_text(f"👥 تعداد کاربران ثبت‌شده: *{len(users)}*", parse_mode="Markdown")


# ─── Broadcast (called by GitHub Actions) ────────────────────────────────────

async def broadcast():
    """Fetch proxies and send to all registered users."""
    bot = Bot(token=TELEGRAM_TOKEN)
    users = load_users()

    if not users:
        print("No registered users yet.")
        return

    print(f"Fetching proxies for {len(users)} users...")
    content = await fetch_proxies()

    success, failed = 0, 0
    for chat_id in users:
        try:
            await send_to_user(bot, chat_id, content)
            success += 1
            await asyncio.sleep(0.5)  # Avoid flood limits
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
            failed += 1

    print(f"✅ Broadcast done: {success} sent, {failed} failed.")


# ─── Entry Points ─────────────────────────────────────────────────────────────

def run_bot():
    """Run the interactive bot (polling mode)."""
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("proxies", proxies_now))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("stats", stats))

    print("🤖 Bot is running... Press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "broadcast":
        asyncio.run(broadcast())
    else:
        run_bot()
