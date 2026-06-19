"""
=============================================================================
BOT DISCORD — TRADE DOJO GEX OUTLOOK (v3 — Railway / variables d'environnement)
=============================================================================
Version conçue pour tourner 24/7 sur Railway (ou tout autre hébergeur).

Différence avec la version locale : le token Discord et l'ID du canal
ne sont PLUS écrits en dur dans ce fichier. Ils sont lus depuis des
"variables d'environnement" que tu configures directement sur Railway
(jamais dans le code = plus sécurisé, le fichier peut être visible
publiquement sans risque).

VARIABLES D'ENVIRONNEMENT À CONFIGURER SUR RAILWAY :
    DISCORD_BOT_TOKEN       → ton token Discord
    CHANNEL_ID_TO_WATCH     → l'ID du canal #gex-daily-outlook
    N8N_WEBHOOK_URL         → l'URL de ton webhook n8n
    SILENCE_DELAY_SECONDS   → (optionnel) délai de regroupement, défaut 60
=============================================================================
"""

import discord
import requests
import asyncio
import os

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURATION — lue depuis les variables d'environnement Railway
# ─────────────────────────────────────────────────────────────────────────

DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
CHANNEL_ID_TO_WATCH = int(os.environ.get("CHANNEL_ID_TO_WATCH", "0"))
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "https://navidkarimi.app.n8n.cloud/webhook/gex-outlook")
SILENCE_DELAY_SECONDS = int(os.environ.get("SILENCE_DELAY_SECONDS", "60"))

# ─────────────────────────────────────────────────────────────────────────
# NE RIEN MODIFIER EN DESSOUS
# ─────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

pending_messages = []
pending_author = None
debounce_task = None


async def send_accumulated_outlook():
    global pending_messages, pending_author

    await asyncio.sleep(SILENCE_DELAY_SECONDS)

    if not pending_messages:
        return

    full_text = "\n".join(pending_messages)
    author_name = pending_author
    message_count = len(pending_messages)

    print(f"\n⏰ Silence de {SILENCE_DELAY_SECONDS}s détecté — outlook considéré complet")
    print(f"   {message_count} message(s) regroupé(s), {len(full_text)} caractères au total")
    print("   ➜ Envoi vers n8n...")

    payload = {
        "content": full_text,
        "author": {"username": author_name, "bot": False},
        "channel_id": str(CHANNEL_ID_TO_WATCH),
    }

    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=20)
        if response.status_code in (200, 201, 202):
            print("   ✅ Envoyé avec succès à n8n. L'analyse Claude arrive en DM.")
        else:
            print(f"   ⚠️ n8n a répondu avec le code {response.status_code}")
            print(f"   Réponse : {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Erreur de connexion à n8n : {e}")

    pending_messages = []
    pending_author = None


@client.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {client.user}")
    print(f"👀 Surveillance du canal ID : {CHANNEL_ID_TO_WATCH}")
    print(f"📡 Webhook n8n : {N8N_WEBHOOK_URL}")
    print(f"⏱️  Délai de regroupement : {SILENCE_DELAY_SECONDS} secondes")
    print("─" * 60)
    print("Le bot est actif sur Railway — tourne 24/7.")
    print("─" * 60)


@client.event
async def on_message(message):
    global pending_messages, pending_author, debounce_task

    if message.author == client.user:
        return
    if message.channel.id != CHANNEL_ID_TO_WATCH:
        return
    if not message.content or len(message.content.strip()) == 0:
        return

    print(f"📨 Message reçu de {message.author.name} ({len(message.content)} caractères) — en attente de regroupement...")

    pending_messages.append(message.content)
    pending_author = message.author.name

    if debounce_task and not debounce_task.done():
        debounce_task.cancel()

    debounce_task = asyncio.create_task(send_accumulated_outlook())


# ─────────────────────────────────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("❌ Variable d'environnement DISCORD_BOT_TOKEN manquante.")
        exit(1)
    if CHANNEL_ID_TO_WATCH == 0:
        print("❌ Variable d'environnement CHANNEL_ID_TO_WATCH manquante.")
        exit(1)

    client.run(DISCORD_BOT_TOKEN)
