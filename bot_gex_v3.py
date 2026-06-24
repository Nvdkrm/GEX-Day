"""
=============================================================================
BOT DISCORD — QG TRADING (v4 — multi-canaux + journal de trading)
=============================================================================
  #menthor-q          → webhook n8n "menthor-q"
  #gex-daily-outlook  → webhook n8n "gex-outlook"
  #gex-levels-dc      → webhook n8n "gex-levels"
  #trades-bruce       → webhook n8n "trade-bruce"
  #trades-antho       → webhook n8n "trade-antho"
  #journal-vocal      → webhook n8n "journal-vocal"

VARIABLES D'ENVIRONNEMENT RAILWAY :
    DISCORD_BOT_TOKEN
    MENTHORQ_CHANNEL_ID        → 1493925337317511178
    GEX_OUTLOOK_CHANNEL_ID     → 1510366498776940644
    GEX_LEVELS_CHANNEL_ID      → 1493925486588330035
    TRADES_BRUCE_CHANNEL_ID    → 1517576143933407323
    TRADES_ANTHO_CHANNEL_ID    → 1517576223197364244
    JOURNAL_VOCAL_CHANNEL_ID   → 1519420310716158022
    N8N_WEBHOOK_MENTHORQ
    N8N_WEBHOOK_GEX_OUTLOOK
    N8N_WEBHOOK_GEX_LEVELS
    N8N_WEBHOOK_TRADE_BRUCE    → https://navidkarimi.app.n8n.cloud/webhook/trade-bruce
    N8N_WEBHOOK_TRADE_ANTHO    → https://navidkarimi.app.n8n.cloud/webhook/trade-antho
    N8N_WEBHOOK_JOURNAL_VOCAL  → https://navidkarimi.app.n8n.cloud/webhook/journal-vocal
    SILENCE_DELAY_SECONDS         → défaut 60
    TRADES_SILENCE_DELAY_SECONDS  → défaut 60
    JOURNAL_SILENCE_DELAY_SECONDS → défaut 5
=============================================================================
"""

import discord
import requests
import asyncio
import os

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
SILENCE_DELAY_SECONDS = int(os.environ.get("SILENCE_DELAY_SECONDS", "60"))
TRADES_SILENCE_DELAY_SECONDS = int(os.environ.get("TRADES_SILENCE_DELAY_SECONDS", "60"))
JOURNAL_SILENCE_DELAY_SECONDS = int(os.environ.get("JOURNAL_SILENCE_DELAY_SECONDS", "5"))

ROUTES = {
    int(os.environ.get("MENTHORQ_CHANNEL_ID", "0")): {
        "name": "menthor-q",
        "webhook": os.environ.get("N8N_WEBHOOK_MENTHORQ", ""),
        "include_attachments": True,
        "silence_delay": SILENCE_DELAY_SECONDS,
    },
    int(os.environ.get("GEX_OUTLOOK_CHANNEL_ID", "0")): {
        "name": "gex-outlook",
        "webhook": os.environ.get("N8N_WEBHOOK_GEX_OUTLOOK", ""),
        "include_attachments": False,
        "silence_delay": SILENCE_DELAY_SECONDS,
    },
    int(os.environ.get("GEX_LEVELS_CHANNEL_ID", "0")): {
        "name": "gex-levels",
        "webhook": os.environ.get("N8N_WEBHOOK_GEX_LEVELS", ""),
        "include_attachments": True,
        "silence_delay": SILENCE_DELAY_SECONDS,
    },
    int(os.environ.get("TRADES_BRUCE_CHANNEL_ID", "0")): {
        "name": "trade-bruce",
        "webhook": os.environ.get("N8N_WEBHOOK_TRADE_BRUCE", ""),
        "include_attachments": True,
        "silence_delay": TRADES_SILENCE_DELAY_SECONDS,
    },
    int(os.environ.get("TRADES_ANTHO_CHANNEL_ID", "0")): {
        "name": "trade-antho",
        "webhook": os.environ.get("N8N_WEBHOOK_TRADE_ANTHO", ""),
        "include_attachments": True,
        "silence_delay": TRADES_SILENCE_DELAY_SECONDS,
    },
    int(os.environ.get("JOURNAL_VOCAL_CHANNEL_ID", "0")): {
        "name": "journal-vocal",
        "webhook": os.environ.get("N8N_WEBHOOK_JOURNAL_VOCAL", ""),
        "include_attachments": True,
        "silence_delay": JOURNAL_SILENCE_DELAY_SECONDS,
    },
}

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
pending_state = {}


async def send_accumulated(channel_id):
    route = ROUTES[channel_id]
    await asyncio.sleep(route["silence_delay"])
    state = pending_state.get(channel_id)
    if not state or not state["messages"]:
        return
    full_text = "\n".join(state["messages"])
    attachments = state["attachments"]
    author_name = state["author"]
    message_count = len(state["messages"])
    print(f"\n⏰ [{route['name']}] Silence de {route['silence_delay']}s détecté")
    print(f"   {message_count} message(s), {len(full_text)} caractères, {len(attachments)} pièce(s) jointe(s)")
    print(f"   ➜ Envoi vers webhook {route['name']}...")
    payload = {
        "content": full_text,
        "author": {"username": author_name, "bot": False},
        "channel_id": str(channel_id),
        "source": route["name"],
        "attachments": attachments if route["include_attachments"] else [],
    }
    webhook_url = route["webhook"]
    if not webhook_url:
        print(f"   ⚠️ Aucun webhook configuré pour {route['name']} — message ignoré")
        pending_state[channel_id] = {"messages": [], "attachments": [], "author": None, "task": None}
        return
    try:
        response = requests.post(webhook_url, json=payload, timeout=20)
        if response.status_code in (200, 201, 202):
            print(f"   ✅ Envoyé avec succès vers {route['name']}.")
        else:
            print(f"   ⚠️ Webhook {route['name']} a répondu avec le code {response.status_code}")
            print(f"   Réponse : {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur de connexion au webhook {route['name']} : {e}")
    pending_state[channel_id] = {"messages": [], "attachments": [], "author": None, "task": None}


@client.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {client.user}")
    print(f"⏱️  GEX: {SILENCE_DELAY_SECONDS}s | Trades: {TRADES_SILENCE_DELAY_SECONDS}s | Journal: {JOURNAL_SILENCE_DELAY_SECONDS}s")
    print("─" * 60)
    print("👀 Canaux surveillés :")
    for channel_id, route in ROUTES.items():
        status = "✅" if (channel_id != 0 and route["webhook"]) else "⚠️ INCOMPLET"
        print(f"   {status} #{route['name']:15s} (ID: {channel_id}, délai {route['silence_delay']}s) → {route['webhook'][:50] or 'WEBHOOK MANQUANT'}")
    print("─" * 60)
    print("Le bot est actif sur Railway — tourne 24/7.")
    print("─" * 60)


def extract_embed_text(embeds):
    parts = []
    for embed in embeds:
        if embed.title:
            parts.append(str(embed.title))
        if embed.description:
            parts.append(str(embed.description))
        for field in embed.fields:
            parts.append(f"{field.name}: {field.value}")
        if embed.footer and embed.footer.text:
            parts.append(str(embed.footer.text))
    return "\n".join(parts)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    channel_id = message.channel.id
    if channel_id not in ROUTES:
        return
    route = ROUTES[channel_id]
    content_text = message.content
    content_attachments = message.attachments
    content_embeds = message.embeds
    if not content_text and not content_attachments and not content_embeds and getattr(message, "message_snapshots", None):
        snapshot = message.message_snapshots[0]
        content_text = snapshot.content
        content_attachments = snapshot.attachments
        content_embeds = getattr(snapshot, "embeds", [])
    embed_text = extract_embed_text(content_embeds) if content_embeds else ""
    if embed_text:
        content_text = (content_text + "\n" + embed_text).strip() if content_text else embed_text
    text_attachments = [a for a in content_attachments if a.content_type and a.content_type.startswith("text/")]
    if text_attachments:
        text_parts = []
        for att in text_attachments:
            try:
                data = await att.read()
                text_parts.append(data.decode("utf-8", errors="replace"))
            except Exception as e:
                print(f"   ⚠️ Impossible de lire {att.filename} : {e}")
        text_from_files = "\n".join(text_parts)
        if text_from_files:
            content_text = (content_text + "\n" + text_from_files).strip() if content_text else text_from_files
        content_attachments = [a for a in content_attachments if a not in text_attachments]
    has_text = content_text and len(content_text.strip()) > 0
    has_attachments = len(content_attachments) > 0
    if not has_text and not has_attachments:
        return
    print(f"📨 [{route['name']}] Message de {message.author.name} ({len(content_text) if content_text else 0} chars, {len(content_attachments)} pj) — en attente...")
    if channel_id not in pending_state or not pending_state[channel_id].get("messages") and not pending_state[channel_id].get("attachments"):
        pending_state[channel_id] = {"messages": [], "attachments": [], "author": None, "task": None}
    state = pending_state[channel_id]
    if has_text:
        state["messages"].append(content_text)
    for att in content_attachments:
        state["attachments"].append({"filename": att.filename, "url": att.url, "content_type": att.content_type})
    state["author"] = message.author.name
    if state["task"] and not state["task"].done():
        state["task"].cancel()
    state["task"] = asyncio.create_task(send_accumulated(channel_id))


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ DISCORD_BOT_TOKEN manquant.")
        exit(1)
    valid_routes = {k: v for k, v in ROUTES.items() if k != 0}
    if not valid_routes:
        print("❌ Aucun canal configuré.")
        exit(1)
    client.run(DISCORD_BOT_TOKEN)
