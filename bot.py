import os
import asyncio
import httpx
from telegram import Bot
from telegram.constants import ParseMode

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
PROXY_URL = "https://raw.githubusercontent.com/SoliSpirit/mtproto/refs/heads/master/all_proxies.txt"

MAX_MESSAGE_LENGTH = 4096  # Telegram limit


async def fetch_proxies() -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(PROXY_URL)
        response.raise_for_status()
        return response.text.strip()


def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split long text into chunks that fit Telegram's message limit."""
    lines = text.splitlines(keepends=True)
    chunks = []
    current = ""

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


async def send_proxies():
    bot = Bot(token=TELEGRAM_TOKEN)
    print("Fetching proxy list...")

    content = await fetch_proxies()
    total_lines = len([l for l in content.splitlines() if l.strip()])
    print(f"Fetched {total_lines} lines. Sending to Telegram...")

    header = (
        f"🔄 *MTProto Proxy Update*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 `{total_lines}` proxies fetched\n"
        f"🔗 Source: `SoliSpirit/mtproto`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    chunks = split_message(content)

    # Send header + first chunk together if they fit
    first_chunk = header + f"```\n{chunks[0]}\n```"
    if len(first_chunk) <= MAX_MESSAGE_LENGTH:
        await bot.send_message(
            chat_id=CHAT_ID,
            text=first_chunk,
            parse_mode=ParseMode.MARKDOWN_V2.value if False else "Markdown",
        )
        remaining = chunks[1:]
    else:
        await bot.send_message(chat_id=CHAT_ID, text=header, parse_mode="Markdown")
        remaining = chunks

    for i, chunk in enumerate(remaining):
        msg = f"```\n{chunk}\n```"
        if len(msg) > MAX_MESSAGE_LENGTH:
            # Send as plain text if code block makes it too long
            msg = chunk
        await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
        await asyncio.sleep(0.5)  # Avoid hitting rate limits

    print("✅ Done! Message(s) sent successfully.")


if __name__ == "__main__":
    asyncio.run(send_proxies())
