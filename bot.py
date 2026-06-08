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
MAX_LENGTH = 4000  # کمی کمتر از ۴۰۹۶ برای اطمینان


# ─── User Storage ─────────────────────────────────────────────────────────────

def load_users() -> set:
    if USERS_FILE.exists():
        return set(json.loads(USERS_FILE.read_text()))
    return set()


def save_users(users: set):
    USERS_FILE.write_text(json.dumps(list(users)))


# ─── Proxy Fetcher ────────────────────────────────────────────────────────────

async def fetch_proxies() -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(PROXY_URL)
        r.raise_for_status()
        return r.text.strip()


def split_text(text: str, max_length: int = MAX_LENGTH) -> list:
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
    chunks = split_text(content)

    # پیام اول: هدر + اولین chunk به صورت plain text
    header = (
        f"🔄 MTProto Proxy Update\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 {total_lines} proxies available\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{chunks[0]}"
    )
    await bot.send_message(chat_id=chat_id, text=header)

    # بقیه chunk ها
    for chunk in chunks[1:]:
        await bot.send_message(chat_id=chat_id, text=chunk)
        await asyncio.sleep(0.5)


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
            f"✅ ثبت‌نام موفق!\n"
            f"هر ۱۲ ساعت لیست پروکسی‌های MTProto برای شما ارسال می‌شود.\n\n"
            f"برای دریافت فوری: /proxies"
        )
    else:
        await update.message.reply_text(
            f"👋 سلام {user.first_name}!\n\n"
            f"✅ شما قبلاً ثبت شده‌اید.\n"
            f"برای دریافت فوری: /proxies"
        )


async def proxies_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # ثبت کاربر اگر قبلاً نبوده
    users = load_users()
    users.add(chat_id)
    save_users(users)

    msg = await update.message.reply_text("⏳ در حال دریافت پروکسی‌ها، لطفاً صبر کنید...")

    try:
        content = await fetch_proxies()
        await msg.delete()
        await send_to_user(context.bot, chat_id, content)
    except Exception as e:
        await msg.edit_text(f"❌ خطا در دریافت پروکسی‌ها:\n{str(e)}")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    users = load_users()
    users.discard(chat_id)
    save_users(users)
    await update.message.reply_text(
        "❌ از لیست آپدیت‌ها حذف شدید.\n"
        "برای عضویت مجدد: /start"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_users()
    await update.message.reply_text(f"👥 تعداد کاربران ثبت‌شده: {len(users)}")


# ─── Broadcast ────────────────────────────────────────────────────────────────

async def broadcast():
    bot = Bot(token=TELEGRAM_TOKEN)
    users = load_users()

    if not users:
        print("No registered users yet.")
        return

    print(f"Fetching proxies for {len(users)} users...")
    content = await fetch_proxies()

    success, failed = 0, 0
    for chat_id in list(users):
        try:
            await send_to_user(bot, chat_id, content)
            success += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")
            failed += 1

    print(f"✅ Done: {success} sent, {failed} failed.")


# ─── Entry Points ─────────────────────────────────────────────────────────────

def run_bot():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("proxies", proxies_now))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("stats", stats))
    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "broadcast":
        asyncio.run(broadcast())
    else:
        run_bot()
