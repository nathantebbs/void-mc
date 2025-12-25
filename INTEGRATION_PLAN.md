# void-mc Discord Integration Plan

## Executive Summary

This document outlines the secure architecture for integrating user-hosted Minecraft servers with a centrally-hosted Discord bot. The design prioritizes security, privacy, and user control while providing seamless monitoring and notification capabilities.

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INFRASTRUCTURE                      │
│                                                                  │
│  ┌──────────────────┐         ┌─────────────────┐              │
│  │  Minecraft       │         │   vmc CLI       │              │
│  │  Server          │◄────────│   Background    │              │
│  │  (Fabric)        │  RCON   │   Monitor       │              │
│  └──────────────────┘         └────────┬────────┘              │
│         │                               │                        │
│         │ logs/latest.log              │                        │
│         │                               │                        │
│         ▼                               │                        │
│  ┌──────────────────┐                  │                        │
│  │  Log Parser      │                  │                        │
│  │  (Player Events) │                  │                        │
│  └────────┬─────────┘                  │                        │
│           │                             │                        │
│           └─────────────────────────────┘                        │
│                       │                                          │
│                       │ HTTPS POST (Webhook)                     │
│                       │ Bearer Token Auth                        │
└───────────────────────┼──────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ORACLE FREE TIER (PUBLIC BOT)                  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │               FastAPI Webhook Receiver                  │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  POST /webhook/event                             │  │    │
│  │  │  - Validate Bearer token                         │  │    │
│  │  │  - Verify HMAC signature                         │  │    │
│  │  │  - Rate limit check                              │  │    │
│  │  │  - Queue notification                            │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                          │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           SQLite Token Registry                         │    │
│  │  webhook_token -> channel_id, server_id, created_at    │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                          │
│                       ▼                                          │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Discord.py Bot Client                      │    │
│  │  - Send formatted messages to user's channel           │    │
│  │  - Handle slash commands (/status, /stats, etc.)       │    │
│  └────────────────────┬───────────────────────────────────┘    │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   User's Discord     │
              │   Server/Channel     │
              └──────────────────────┘
```

---

## Security Architecture

### Threat Model

**Threats Considered:**
1. ✅ Unauthorized webhook posting (spoofed notifications)
2. ✅ Token theft/leakage
3. ✅ Rate limiting abuse (DoS on bot)
4. ✅ Channel ID enumeration
5. ✅ Man-in-the-middle attacks
6. ✅ Replay attacks
7. ✅ Bot compromise leading to server control

**Threats Explicitly NOT Addressed:**
- ❌ User's Discord server security (out of scope)
- ❌ Minecraft server vulnerabilities (use vanilla + trusted mods)
- ❌ Physical access to user's server

### Defense Mechanisms

#### 1. Webhook Authentication (Multi-Layer)

**Layer 1: Bearer Token Authentication**
```python
# User generates token locally
import secrets
webhook_token = secrets.token_urlsafe(32)  # 256-bit entropy

# Stored in ~/.vmc/.env (never transmitted during setup)
DISCORD_WEBHOOK_TOKEN=abc123...xyz

# Sent with every webhook request
headers = {
    "Authorization": f"Bearer {webhook_token}",
    "Content-Type": "application/json"
}
```

**Layer 2: HMAC Signature Verification**
```python
# User also generates signing key
signing_key = secrets.token_bytes(32)

# Each webhook payload is signed
import hmac
import hashlib
import json

payload = {"event": "player_join", "player": "Steve"}
payload_json = json.dumps(payload, sort_keys=True)
signature = hmac.new(
    signing_key,
    payload_json.encode(),
    hashlib.sha256
).hexdigest()

headers["X-VMC-Signature"] = signature
```

**Layer 3: Timestamp Validation (Replay Protection)**
```python
import time
payload["timestamp"] = int(time.time())

# Bot rejects requests older than 60 seconds
if abs(payload["timestamp"] - current_time) > 60:
    raise ValidationError("Request expired")
```

**Layer 4: TLS/HTTPS**
- All webhook traffic over HTTPS (Let's Encrypt on Oracle)
- Certificate pinning optional for paranoid users

#### 2. Rate Limiting

**Per-Token Limits:**
```python
# In-memory rate limiter (Redis for production)
RATE_LIMITS = {
    "per_minute": 100,   # 100 events per minute per token
    "per_hour": 1000,    # 1000 events per hour per token
    "per_day": 10000     # 10k events per day per token
}

# Burst protection
MAX_CONCURRENT_REQUESTS = 5  # Per token
```

**Global Limits:**
```python
# Protect bot from aggregate abuse
GLOBAL_RATE_LIMITS = {
    "per_second": 1000,  # Total across all users
    "per_minute": 10000
}
```

**Response to Rate Limit Violations:**
- HTTP 429 with `Retry-After` header
- Exponential backoff suggested
- Persistent violations (>3 in 1 hour) trigger temporary token suspension
- Discord notification to user about suspension

#### 3. Token Management

**Token Registration Flow:**
```bash
# User runs setup command
$ vmc discord setup

# CLI generates credentials locally
webhook_token = secrets.token_urlsafe(32)
signing_key = secrets.token_bytes(32)
server_id = uuid.uuid4()

# CLI prompts for Discord channel ID
Enter Discord channel ID for notifications: 123456789

# CLI registers token with bot (ONE TIME ONLY)
POST https://bot.void-mc.io/webhook/register
{
    "webhook_token_hash": sha256(webhook_token),  # Never send raw token!
    "channel_id": "123456789",
    "server_id": "unique-uuid",
    "public_key": <optional, for future encryption>
}

# Bot responds with confirmation
{
    "status": "registered",
    "server_id": "unique-uuid"
}

# CLI saves credentials locally
~/.vmc/.env:
  DISCORD_WEBHOOK_TOKEN=abc123...xyz
  DISCORD_SIGNING_KEY=def456...uvw
  DISCORD_SERVER_ID=uuid
```

**Token Storage Security:**
```bash
# Credentials stored with restrictive permissions
chmod 600 ~/.vmc/.env

# CLI warns if permissions are insecure
$ vmc discord status
⚠️  Warning: ~/.vmc/.env has insecure permissions (644)
    Run: chmod 600 ~/.vmc/.env
```

**Token Rotation:**
```bash
# User can rotate compromised tokens
$ vmc discord rotate-token

Generating new token...
Updating bot registration...
✅ Token rotated successfully

Old token will be valid for 5 minutes to allow in-flight requests.
```

**Token Revocation:**
```bash
# Immediate revocation
$ vmc discord revoke-token

⚠️  This will stop all Discord notifications.
Continue? (y/N): y

✅ Token revoked. Run 'vmc discord setup' to reconfigure.
```

#### 4. Data Privacy

**Data Stored by Bot (SQLite):**
```sql
CREATE TABLE webhook_registrations (
    webhook_token_hash TEXT PRIMARY KEY,  -- SHA-256 hash (never plaintext)
    channel_id TEXT NOT NULL,
    server_id TEXT UNIQUE NOT NULL,       -- UUID for identifying server
    signing_key_hash TEXT NOT NULL,       -- For HMAC verification
    created_at INTEGER NOT NULL,
    last_used_at INTEGER,
    request_count INTEGER DEFAULT 0,
    is_suspended BOOLEAN DEFAULT FALSE
);

-- Index for efficient lookup
CREATE INDEX idx_server_id ON webhook_registrations(server_id);
CREATE INDEX idx_last_used ON webhook_registrations(last_used_at);
```

**Data NOT Stored:**
- ❌ Raw webhook tokens (only hashes)
- ❌ Player usernames (ephemeral, only in Discord messages)
- ❌ Server IP addresses
- ❌ World data or gameplay information
- ❌ User's Discord user IDs (only channel IDs)

**Data Retention:**
```python
# Auto-cleanup inactive registrations
DELETE FROM webhook_registrations
WHERE last_used_at < (current_time - 90 days)
  AND request_count = 0;

# User can request data deletion
$ vmc discord delete-data
This will permanently delete your server registration from the bot.
Continue? (y/N): y

Sending deletion request...
✅ Data deleted from bot. Token is now invalid.
```

#### 5. Bot Permissions (Principle of Least Privilege)

**Discord Bot Permissions Required:**
```
✅ Send Messages         (post notifications)
✅ Embed Links           (rich embeds for status)
✅ Read Message History  (for slash command context)

❌ Manage Messages       (not needed)
❌ Manage Channels       (not needed)
❌ Administrator         (NEVER)
```

**OAuth2 Scopes:**
```
applications.commands  (slash commands)
bot                    (bot user)
```

**Bot Invite URL:**
```
https://discord.com/api/oauth2/authorize
  ?client_id=BOT_CLIENT_ID
  &permissions=19456      # Minimal permissions
  &scope=bot%20applications.commands
```

---

## API Specification

### Webhook Endpoints

#### 1. Register Webhook Token
```http
POST /webhook/register
Content-Type: application/json

{
    "webhook_token_hash": "sha256_hash",
    "signing_key_hash": "sha256_hash",
    "channel_id": "123456789",
    "server_id": "uuid-v4"
}

Response 200:
{
    "status": "registered",
    "server_id": "uuid-v4"
}

Response 400:
{
    "error": "invalid_channel_id",
    "message": "Channel ID must be numeric"
}

Response 409:
{
    "error": "already_registered",
    "message": "Server ID already registered. Use /webhook/rotate to update."
}
```

#### 2. Send Notification Event
```http
POST /webhook/event
Authorization: Bearer <webhook_token>
X-VMC-Signature: <hmac_sha256_signature>
Content-Type: application/json

{
    "timestamp": 1703462400,
    "event_type": "player_join",
    "data": {
        "player": "Steve"
    }
}

Response 200:
{
    "status": "delivered",
    "message_id": "discord_message_id"
}

Response 401:
{
    "error": "unauthorized",
    "message": "Invalid or revoked token"
}

Response 429:
{
    "error": "rate_limit_exceeded",
    "retry_after": 60
}
```

**Supported Event Types:**
```python
EVENT_TYPES = {
    # Server lifecycle
    "server_started": {
        "data": {"uptime": int, "version": str}
    },
    "server_stopped": {
        "data": {"reason": str}  # "manual", "crash", "scheduled"
    },
    "server_restarted": {
        "data": {"reason": str}
    },
    
    # Player events
    "player_join": {
        "data": {"player": str}
    },
    "player_leave": {
        "data": {"player": str}
    },
    "player_death": {
        "data": {"player": str, "message": str, "death_count": int}
    },
    
    # Performance alerts
    "low_tps": {
        "data": {"tps": float, "threshold": float}
    },
    "high_memory": {
        "data": {"usage_percent": float, "threshold": float}
    },
    
    # Backup events
    "backup_started": {
        "data": {"backup_name": str}
    },
    "backup_completed": {
        "data": {"backup_name": str, "size_mb": float}
    },
    "backup_failed": {
        "data": {"backup_name": str, "error": str}
    }
}
```

#### 3. Query Server Status (for Slash Commands)
```http
POST /webhook/query
Authorization: Bearer <webhook_token>
Content-Type: application/json

{
    "query_type": "status"  # or "players", "stats", etc.
}

Response 200:
{
    "status": "online",
    "players": {
        "online": 3,
        "max": 20,
        "list": ["Steve", "Alex", "Notch"]
    },
    "uptime": 3600,
    "version": "1.21.1"
}

Response 503:
{
    "status": "offline"
}
```

**Note:** Query endpoint requires bi-directional communication. Two implementation options:

**Option A: Polling (Simple, MVP)**
- Bot queries user server via webhook
- User server must expose callback endpoint (NAT/firewall issues)
- **Pros**: Real-time data
- **Cons**: Requires port forwarding/ngrok

**Option B: Cached State (Recommended for MVP)**
- User server pushes state updates periodically (every 60s)
- Bot stores latest state in database
- Slash commands return cached data
- **Pros**: No inbound connections needed
- **Cons**: Data may be up to 60s stale

**MVP Recommendation: Option B** (simpler, no networking hassles)

#### 4. Rotate Token
```http
POST /webhook/rotate
Authorization: Bearer <old_webhook_token>
Content-Type: application/json

{
    "new_token_hash": "sha256_hash",
    "new_signing_key_hash": "sha256_hash"
}

Response 200:
{
    "status": "rotated",
    "grace_period_seconds": 300
}
```

#### 5. Revoke Token
```http
DELETE /webhook/revoke
Authorization: Bearer <webhook_token>

Response 200:
{
    "status": "revoked"
}
```

---

## Discord Bot Implementation

### Bot Architecture (FastAPI + Discord.py)

**File Structure:**
```
discord-bot/
├── main.py                    # FastAPI app + Discord bot launcher
├── api/
│   ├── __init__.py
│   ├── webhook.py             # Webhook endpoints
│   ├── auth.py                # Token validation middleware
│   └── rate_limiter.py        # Rate limiting logic
├── bot/
│   ├── __init__.py
│   ├── client.py              # Discord.py client
│   ├── commands.py            # Slash commands
│   └── notifications.py       # Message formatting
├── database/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   └── operations.py          # CRUD operations
├── config.py                  # Configuration (env vars)
├── security.py                # Crypto utilities (HMAC, hashing)
└── tests/
    ├── test_webhook.py
    ├── test_auth.py
    └── test_rate_limiter.py
```

**main.py:**
```python
import asyncio
from fastapi import FastAPI
from discord.ext import commands
import uvicorn

from api.webhook import router as webhook_router
from bot.client import VoidBot
from config import settings

# FastAPI app for webhooks
app = FastAPI(title="void-mc Discord Bot API")
app.include_router(webhook_router, prefix="/webhook")

# Discord bot
bot = VoidBot()

@app.on_event("startup")
async def startup():
    # Start Discord bot in background
    asyncio.create_task(bot.start(settings.DISCORD_TOKEN))

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bot_ready": bot.is_ready(),
        "latency_ms": round(bot.latency * 1000, 2)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**api/webhook.py:**
```python
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
import hashlib
import hmac
import time

from database.operations import get_registration_by_token
from bot.notifications import send_notification
from api.rate_limiter import check_rate_limit

router = APIRouter()

class WebhookEvent(BaseModel):
    timestamp: int
    event_type: str
    data: dict

@router.post("/event")
async def receive_event(
    event: WebhookEvent,
    authorization: str = Header(...),
    x_vmc_signature: str = Header(...)
):
    # Extract token from "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")
    
    token = authorization[7:]
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Look up registration
    registration = await get_registration_by_token(token_hash)
    if not registration:
        raise HTTPException(401, "Invalid token")
    
    if registration.is_suspended:
        raise HTTPException(403, "Token suspended due to abuse")
    
    # Verify timestamp (replay protection)
    current_time = int(time.time())
    if abs(event.timestamp - current_time) > 60:
        raise HTTPException(400, "Request expired")
    
    # Verify HMAC signature
    import json
    payload_json = json.dumps(event.dict(), sort_keys=True)
    expected_signature = hmac.new(
        bytes.fromhex(registration.signing_key_hash),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(x_vmc_signature, expected_signature):
        raise HTTPException(401, "Invalid signature")
    
    # Check rate limits
    if not await check_rate_limit(token_hash):
        raise HTTPException(429, "Rate limit exceeded")
    
    # Send notification to Discord
    message_id = await send_notification(
        registration.channel_id,
        event.event_type,
        event.data
    )
    
    # Update stats
    await update_registration_stats(token_hash)
    
    return {
        "status": "delivered",
        "message_id": message_id
    }
```

**bot/notifications.py:**
```python
import discord
from typing import Dict, Any

from bot.client import get_bot

async def send_notification(channel_id: str, event_type: str, data: Dict[str, Any]):
    bot = get_bot()
    channel = bot.get_channel(int(channel_id))
    
    if not channel:
        raise ValueError(f"Channel {channel_id} not found")
    
    # Format message based on event type
    embed = format_event_embed(event_type, data)
    message = await channel.send(embed=embed)
    
    return str(message.id)

def format_event_embed(event_type: str, data: Dict[str, Any]) -> discord.Embed:
    if event_type == "player_join":
        return discord.Embed(
            title="➡️ Player Joined",
            description=f"**{data['player']}** joined the server",
            color=discord.Color.green()
        )
    
    elif event_type == "player_death":
        return discord.Embed(
            title="💀 Player Death",
            description=f"**{data['player']}** {data['message']}",
            color=discord.Color.red()
        ).add_field(
            name="Total Deaths",
            value=str(data['death_count'])
        )
    
    elif event_type == "server_started":
        return discord.Embed(
            title="✅ Server Started",
            description=f"Server is now online (v{data['version']})",
            color=discord.Color.green()
        )
    
    # ... more event types
    
    # Generic fallback
    return discord.Embed(
        title=event_type.replace("_", " ").title(),
        description=str(data),
        color=discord.Color.blue()
    )
```

**bot/commands.py:**
```python
import discord
from discord import app_commands
from discord.ext import commands

from database.operations import get_registration_by_channel

class ServerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="status", description="Check server status")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        # Find registration for this channel
        registration = await get_registration_by_channel(str(interaction.channel_id))
        
        if not registration:
            await interaction.followup.send(
                "❌ No server configured for this channel. "
                "Run `vmc discord setup` to configure notifications."
            )
            return
        
        # Get cached server state (updated periodically by user server)
        state = await get_cached_server_state(registration.server_id)
        
        if not state or state.get("status") == "offline":
            await interaction.followup.send("🔴 Server is offline")
            return
        
        # Build status embed
        embed = discord.Embed(
            title="🟢 Server Status",
            color=discord.Color.green()
        )
        embed.add_field(
            name="Players",
            value=f"{state['players']['online']}/{state['players']['max']}",
            inline=True
        )
        embed.add_field(
            name="Uptime",
            value=format_uptime(state['uptime']),
            inline=True
        )
        embed.add_field(
            name="Version",
            value=state['version'],
            inline=True
        )
        
        if state['players']['list']:
            embed.add_field(
                name="Online Players",
                value="\n".join(state['players']['list']),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="stats", description="View player statistics")
    async def stats(self, interaction: discord.Interaction, player: str = None):
        # Similar implementation...
        pass

async def setup(bot):
    await bot.add_cog(ServerCommands(bot))
```

---

## Deployment Strategy

### Oracle Free Tier Setup

**Instance Specifications:**
- **Shape**: VM.Standard.A1.Flex (ARM)
- **CPU**: 2 OCPUs
- **RAM**: 12 GB
- **Storage**: 50 GB boot volume
- **OS**: Ubuntu 22.04 LTS (ARM64)
- **Network**: Public IPv4 + IPv6

**Cost**: $0/month (within free tier limits)

### Installation Script

```bash
#!/bin/bash
# deploy-oracle.sh - Deploy void-mc bot to Oracle Cloud

set -e

echo "=== void-mc Discord Bot Deployment ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    certbot \
    python3-certbot-nginx \
    sqlite3 \
    git \
    htop

# Create application user
sudo useradd -r -s /bin/bash -d /opt/vmc-bot vmc-bot

# Clone repository
sudo -u vmc-bot git clone https://github.com/void-mc/void-mc.git /opt/vmc-bot/app
cd /opt/vmc-bot/app/discord-bot

# Create virtual environment
sudo -u vmc-bot python3.11 -m venv /opt/vmc-bot/venv
sudo -u vmc-bot /opt/vmc-bot/venv/bin/pip install --upgrade pip
sudo -u vmc-bot /opt/vmc-bot/venv/bin/pip install -r requirements.txt

# Create .env file
sudo -u vmc-bot tee /opt/vmc-bot/app/discord-bot/.env > /dev/null <<EOF
DISCORD_TOKEN=${DISCORD_TOKEN}
DATABASE_PATH=/opt/vmc-bot/data/registrations.db
LOG_LEVEL=INFO
WEBHOOK_BASE_URL=https://bot.void-mc.io
EOF

# Create data directory
sudo -u vmc-bot mkdir -p /opt/vmc-bot/data

# Initialize database
sudo -u vmc-bot /opt/vmc-bot/venv/bin/python -c "
from database.models import init_db
init_db('/opt/vmc-bot/data/registrations.db')
"

# Create systemd service
sudo tee /etc/systemd/system/vmc-bot.service > /dev/null <<EOF
[Unit]
Description=void-mc Discord Bot
After=network.target

[Service]
Type=simple
User=vmc-bot
WorkingDirectory=/opt/vmc-bot/app/discord-bot
Environment="PATH=/opt/vmc-bot/venv/bin"
ExecStart=/opt/vmc-bot/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx reverse proxy
sudo tee /etc/nginx/sites-available/vmc-bot > /dev/null <<EOF
server {
    listen 80;
    server_name bot.void-mc.io;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/vmc-bot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Configure SSL with Let's Encrypt
sudo certbot --nginx -d bot.void-mc.io --non-interactive --agree-tos -m admin@void-mc.io

# Configure firewall
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables/rules.v4

# Start services
sudo systemctl daemon-reload
sudo systemctl enable vmc-bot
sudo systemctl start vmc-bot

echo "=== Deployment Complete ==="
echo "Bot API: https://bot.void-mc.io"
echo "Health check: https://bot.void-mc.io/health"
```

### Monitoring & Maintenance

**Logging:**
```bash
# Centralized logging with journald
sudo journalctl -u vmc-bot -f

# Log rotation
sudo tee /etc/systemd/journald.conf.d/vmc-bot.conf > /dev/null <<EOF
[Journal]
SystemMaxUse=500M
SystemMaxFileSize=100M
EOF
```

**Automated Backups:**
```bash
# Daily database backup
sudo crontab -e
0 2 * * * /usr/bin/sqlite3 /opt/vmc-bot/data/registrations.db ".backup '/opt/vmc-bot/backups/registrations-$(date +\%Y\%m\%d).db'"
```

**Update Script:**
```bash
#!/bin/bash
# update-bot.sh

cd /opt/vmc-bot/app
sudo -u vmc-bot git pull
sudo -u vmc-bot /opt/vmc-bot/venv/bin/pip install -r discord-bot/requirements.txt
sudo systemctl restart vmc-bot
```

---

## User-Side Implementation (vmc CLI)

### Discord Module (`vmc_core/discord_client.py`)

```python
import secrets
import hashlib
import hmac
import json
import time
import requests
from typing import Dict, Any

class DiscordWebhookClient:
    def __init__(self, token: str, signing_key: bytes, endpoint: str):
        self.token = token
        self.signing_key = signing_key
        self.endpoint = endpoint
    
    def send_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        payload = {
            "timestamp": int(time.time()),
            "event_type": event_type,
            "data": data
        }
        
        # Generate HMAC signature
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            self.signing_key,
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Send request
        try:
            response = requests.post(
                f"{self.endpoint}/event",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "X-VMC-Signature": signature,
                    "Content-Type": "application/json"
                },
                timeout=5
            )
            response.raise_for_status()
            return True
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("⚠️  Rate limit exceeded. Notifications paused.")
            elif e.response.status_code == 401:
                print("❌ Discord token invalid. Run 'vmc discord setup'")
            else:
                print(f"❌ Failed to send notification: {e}")
            return False
        
        except Exception as e:
            print(f"❌ Network error: {e}")
            return False
```

### Log Monitor Integration

```python
# vmc_core/log_monitor.py
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from vmc_core.discord_client import DiscordWebhookClient
from vmc_core.config_manager import load_config

class LogEventHandler(FileSystemEventHandler):
    def __init__(self, discord_client: DiscordWebhookClient):
        self.discord = discord_client
        self.last_position = 0
    
    def on_modified(self, event):
        if event.src_path.endswith("latest.log"):
            self.process_new_lines()
    
    def process_new_lines(self):
        # Similar to existing player_events_monitor.py
        # Parse log, detect events, send to Discord via webhook
        pass

async def start_monitoring():
    config = load_config()
    
    discord_client = DiscordWebhookClient(
        token=config.discord_webhook_token,
        signing_key=config.discord_signing_key,
        endpoint=config.discord_endpoint
    )
    
    # Monitor server logs
    event_handler = LogEventHandler(discord_client)
    observer = Observer()
    observer.schedule(event_handler, path=config.server_log_path, recursive=False)
    observer.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

---

## Testing Strategy

### Security Testing

**Penetration Testing Checklist:**
- [ ] Token brute-force resistance (rate limit validation)
- [ ] HMAC signature bypass attempts
- [ ] Replay attack with old timestamps
- [ ] SQL injection in webhook payload
- [ ] XSS in Discord message embeds
- [ ] DDoS resilience (rate limiter stress test)
- [ ] Token enumeration via timing attacks
- [ ] Channel ID enumeration

**Automated Security Scanning:**
```bash
# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py -t https://bot.void-mc.io

# Bandit (Python security linter)
bandit -r discord-bot/ -ll

# Safety (dependency vulnerability check)
safety check -r discord-bot/requirements.txt
```

### Integration Testing

**Test Scenarios:**
1. ✅ User completes `vmc discord setup` successfully
2. ✅ Server sends player join notification (appears in Discord within 2s)
3. ✅ Rate limit triggers after 101 requests/minute
4. ✅ Token rotation preserves notification functionality
5. ✅ Slash command `/status` returns correct data
6. ✅ Bot gracefully handles server going offline
7. ✅ Invalid signature is rejected with 401

**Load Testing:**
```bash
# Apache Bench - simulate 1000 webhook requests
ab -n 1000 -c 10 \
   -H "Authorization: Bearer test-token" \
   -H "X-VMC-Signature: test-sig" \
   -p payload.json \
   https://bot.void-mc.io/webhook/event
```

---

## Privacy & Compliance

### GDPR Compliance

**Data Subject Rights:**
- ✅ Right to access: `vmc discord export-data`
- ✅ Right to erasure: `vmc discord delete-data`
- ✅ Right to portability: Export as JSON
- ✅ Data minimization: Only store token hashes, channel IDs

**Privacy Policy:**
```
void-mc Bot Privacy Policy

Data Collected:
- Discord channel ID (where you want notifications)
- Hashed webhook token (for authentication)
- Request timestamps and counts (for rate limiting)

Data NOT Collected:
- Player usernames (only transmitted, not stored)
- Server IP addresses
- Gameplay data
- Your Discord user ID

Data Retention:
- Registrations deleted after 90 days of inactivity
- You can request immediate deletion: vmc discord delete-data

Third Parties:
- Discord Inc. (message delivery only)
- No data sold or shared with advertisers

Contact: privacy@void-mc.io
```

### Terms of Service

**Key Terms:**
- Free tier: Unlimited notifications, fair use policy
- Rate limits: 100 req/min per server (subject to change)
- Abuse: Accounts violating ToS may be suspended
- No warranty: Service provided "as-is"
- Liability: We are not liable for lost data or downtime

---

## Success Metrics

### Technical Metrics
- **Uptime**: 99.9% (< 43 minutes downtime/month)
- **Latency**: < 2 seconds from event to Discord message
- **Throughput**: 1000 concurrent servers supported
- **Error Rate**: < 0.1% failed webhook deliveries

### User Metrics
- **Setup Time**: < 5 minutes from `vmc discord setup` to first notification
- **Adoption**: 70% of vmc users enable Discord integration
- **Retention**: 90% of users keep integration active after 30 days

### Security Metrics
- **Token Compromises**: 0 per quarter
- **Rate Limit Violations**: < 1% of requests
- **Unauthorized Access Attempts**: 100% blocked

---

## Migration Plan

### Transitioning Existing Users

**Current Architecture (Local Bot per User):**
```
User runs: python discord-bot/main.py
Bot connects directly to Minecraft server
```

**New Architecture (Centralized Bot + Webhooks):**
```
User runs: vmc start (includes background webhook sender)
Bot receives webhooks from user server
```

**Migration Steps:**
1. Release vmc CLI with Discord integration disabled
2. Send announcement: "New Discord integration coming soon"
3. Deploy centralized bot to Oracle
4. Release vmc 1.1 with webhook support
5. Deprecate local bot instructions in README
6. After 6 months, remove local bot code from repository

**Backward Compatibility:**
- Support both architectures during transition (6 months)
- Add migration command: `vmc discord migrate`
- Auto-detect old config and offer migration

---

## Conclusion

This integration plan provides a secure, scalable, and privacy-respecting architecture for connecting user-hosted Minecraft servers to a centrally-hosted Discord bot. Key principles:

1. **User Control**: Users own their servers; bot is read-only
2. **Security**: Multi-layer authentication with HMAC signatures
3. **Privacy**: Minimal data collection, GDPR compliant
4. **Reliability**: Rate limiting, auto-recovery, 99.9% uptime
5. **Simplicity**: 5-minute setup, zero networking configuration

**Next Steps:**
1. Review and approve architecture
2. Implement MVP webhook endpoints (FastAPI)
3. Implement vmc CLI discord module
4. Security audit and penetration testing
5. Deploy to Oracle free tier
6. Beta testing with 10-20 users
7. Public launch

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-24  
**Author**: void-mc team  
**Security Review**: Pending  
**Legal Review**: Pending
