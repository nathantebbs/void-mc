# void-mc Minimum Viable Product (MVP)

## Project Vision

**void-mc** is a professional-grade Minecraft server management toolkit that enables users to:
1. Deploy optimized Fabric servers locally or on cloud infrastructure
2. Integrate Discord notifications and monitoring via a centrally-hosted bot
3. Manage server operations through a unified CLI interface

## Architecture Overview

### Two-Component System

#### Component 1: `vmc` CLI Tool (User's Machine/Server)
- **Installation**: `brew install vmc`
- **Purpose**: Server deployment, configuration, and lifecycle management
- **Runs On**: User's local machine or their chosen hosting (personal VPS, home server, etc.)
- **Responsibilities**:
  - Minecraft server installation and configuration
  - Mod management and updates
  - Backup and restore operations
  - Server lifecycle (start/stop/restart)
  - Log monitoring and performance metrics

#### Component 2: Public Discord Bot (Oracle Free Tier)
- **Purpose**: Centralized notification relay service
- **Runs On**: Oracle Cloud free tier (maintained by void-mc team)
- **Responsibilities**:
  - Receive webhooks from user servers
  - Post notifications to user Discord servers
  - Provide read-only server status queries
  - **DOES NOT** control user servers directly

### Security Model

**Key Principle**: Users maintain full control of their Minecraft servers. The Discord bot is a passive monitoring service.

```
User's Server (vmc) ─────webhook────> Public Bot (Oracle) ─────message────> User's Discord
                     (one-way push)                        (notifications)
```

## MVP Feature Set

### Phase 1: Core Server Management (Week 1-2)

#### 1.1 CLI Installation & Setup
```bash
brew tap void-mc/tap
brew install vmc

vmc init
# Interactive wizard:
# - Minecraft/Fabric version selection
# - World settings (seed, difficulty, gamemode)
# - Server resource allocation (RAM, view distance)
# - Mod preset selection (vanilla, performance, technical)
# - Creates ~/.vmc/ directory structure
```

#### 1.2 Server Lifecycle Management
```bash
vmc start           # Start Minecraft server in background
vmc stop            # Graceful shutdown with player warning
vmc restart         # Restart with configurable delay
vmc status          # Show server status (running/stopped, uptime, players)
vmc logs [--follow] # View server logs
vmc console         # Attach to RCON console for commands
```

#### 1.3 Configuration Management
```bash
vmc config get <key>             # Get configuration value
vmc config set <key> <value>     # Update configuration
vmc config list                  # Show all configuration
vmc config reset                 # Reset to defaults (with confirmation)
```

**Managed Configuration:**
- Server properties (difficulty, gamemode, max-players, view-distance, pvp)
- JVM arguments (heap size, garbage collection)
- RCON settings
- Backup settings

#### 1.4 Mod Management
```bash
vmc mod list                    # List installed mods with versions
vmc mod search <query>          # Search Modrinth for mods
vmc mod add <slug>              # Install mod from Modrinth
vmc mod remove <name>           # Remove installed mod
vmc mod update [name]           # Update specific or all mods
vmc mod preset apply <preset>   # Apply mod preset (performance, technical, qol)
```

**Presets:**
- `performance`: lithium, c2me, ferritecore, krypton
- `technical`: carpet, litematica, tweakeroo, minihud
- `qol`: simple-voice-chat, waystones, veinminer

#### 1.5 Backup System
```bash
vmc backup create [--name]      # Create manual backup
vmc backup list                 # List available backups
vmc backup restore <name>       # Restore from backup (with confirmation)
vmc backup delete <name>        # Delete backup
vmc backup auto enable          # Enable automatic backups (daily at 4 AM)
vmc backup auto disable         # Disable automatic backups
```

**Backup Features:**
- Automatic pre-shutdown backups
- Configurable retention policy (keep last N backups)
- Backup metadata (timestamp, world size, server version)
- Compression (tar.gz) for space efficiency

---

### Phase 2: Discord Integration (Week 3-4)

#### 2.1 Discord Bot Setup (Oracle Free Tier)

**Bot Hosting:**
- Deployed on Oracle Cloud free tier ARM instance
- Runs 24/7 as systemd service
- Handles webhook requests from user servers
- Posts notifications to configured Discord channels

**Bot Capabilities (Read-Only):**
- Receive and relay server status updates
- Post player join/leave notifications
- Post player death messages with statistics
- Display server online/offline alerts
- **NO** direct server control commands

#### 2.2 User Discord Configuration
```bash
vmc discord setup
# Interactive wizard:
# - Discord channel ID for notifications
# - Webhook authentication token (generated locally)
# - Test connection to public bot
# - Verify permissions (bot can post in channel)
```

**Configuration stored in `~/.vmc/.env`:**
```bash
DISCORD_WEBHOOK_TOKEN=<user-generated-secret>
DISCORD_NOTIFICATIONS_CHANNEL_ID=123456789
DISCORD_BOT_ENDPOINT=https://bot.void-mc.io/webhook
```

#### 2.3 Notification Types

**Automatic Notifications (sent to Discord):**
1. **Server Lifecycle:**
   - ✅ Server started
   - ⏹️ Server stopped (with reason: manual, crash, scheduled maintenance)
   - 🔄 Server restarted

2. **Player Events:**
   - ➡️ Player joined (`Steve joined the server`)
   - ⬅️ Player left (`Steve left the server`)
   - 💀 Player death (`Steve fell from a high place | Total deaths: 7`)

3. **Performance Alerts:**
   - ⚠️ Low TPS warning (< 18 TPS)
   - ⚠️ High memory usage (> 85%)
   - ✅ Performance recovered

4. **Backup Events:**
   - 💾 Backup started
   - ✅ Backup completed successfully
   - ❌ Backup failed (with error details)

#### 2.4 Discord Slash Commands (Read-Only)

**Slash commands call user's server via webhook (if online):**
```
/status              # Server status, player count, uptime
/players             # List online players with playtime
/stats [player]      # Player statistics (deaths, playtime, first join)
/leaderboard deaths  # Top death counts
/leaderboard playtime # Most active players
/world-info          # World seed, difficulty, gamemode, spawn
```

**All commands are read-only queries.** No server control.

#### 2.5 Webhook Security

**Authentication Flow:**
```
1. User runs `vmc discord setup`
2. CLI generates random webhook token (stored locally)
3. CLI sends registration request to public bot:
   {
     "webhook_token": "user-secret-token",
     "channel_id": "123456789",
     "server_id": "unique-server-id"
   }
4. Public bot stores mapping: webhook_token -> channel_id
5. User server sends notifications:
   POST https://bot.void-mc.io/webhook
   Headers: { "Authorization": "Bearer user-secret-token" }
   Body: { "event": "player_join", "player": "Steve" }
6. Bot validates token and posts to correct channel
```

**Security Features:**
- Webhook tokens are cryptographically random (32 bytes, base64)
- Tokens are user-generated, never transmitted in plain text
- Rate limiting: 100 requests/minute per token
- Token rotation support: `vmc discord rotate-token`
- Webhook payload signing (HMAC-SHA256) to prevent spoofing

---

### Phase 3: Polish & Production (Week 5-6)

#### 3.1 Service Management
```bash
vmc service install    # Install systemd/launchd service
vmc service enable     # Enable auto-start on boot
vmc service disable    # Disable auto-start
vmc service status     # Show service status
vmc service logs       # View service logs
```

#### 3.2 Health Checks & Auto-Recovery
```bash
vmc health-check       # Validate configuration and dependencies
# Checks:
# - Java runtime (version 21+)
# - Disk space (> 5GB free)
# - Memory availability (> 2GB recommended)
# - RCON connectivity
# - Discord webhook connectivity
# - Mod integrity (verify checksums)

vmc auto-restart enable   # Enable auto-restart on crash
vmc auto-restart disable  # Disable auto-restart
```

**Auto-Restart Logic:**
- Detects server crash (unexpected process exit)
- Waits 30 seconds before restart attempt
- Creates crash backup before restart
- Sends Discord notification with crash report
- Maximum 3 restart attempts per hour (prevents restart loops)

#### 3.3 Update Management
```bash
vmc update check         # Check for vmc CLI updates
vmc update apply         # Update vmc CLI
vmc server update-check  # Check for Minecraft/Fabric updates
vmc server upgrade       # Upgrade Minecraft/Fabric version (with backup)
```

#### 3.4 Documentation & Help
```bash
vmc help                 # Show all commands
vmc help <command>       # Show command-specific help
vmc docs                 # Open web documentation
vmc version              # Show vmc version and server info
```

#### 3.5 Observability Dashboard (Optional)
```bash
vmc dashboard start      # Launch web UI on localhost:8080
# Features:
# - Real-time player list
# - Server performance graphs (TPS, memory, CPU)
# - Log viewer with filtering
# - Backup management UI
# - Configuration editor
```

---

## Technical Implementation Details

### CLI Architecture (Python)

**Directory Structure:**
```
vmc/
├── vmc                      # Shell wrapper (entry point)
├── vmc_core/                # Python package
│   ├── __init__.py
│   ├── cli.py               # Click/Typer CLI interface
│   ├── server_manager.py    # Server lifecycle management
│   ├── config_manager.py    # Configuration handling
│   ├── mod_manager.py       # Modrinth integration
│   ├── backup_manager.py    # Backup/restore logic
│   ├── discord_client.py    # Webhook sender
│   ├── health_checker.py    # Health check logic
│   ├── service_manager.py   # systemd/launchd integration
│   └── utils/
│       ├── rcon.py          # RCON client
│       ├── log_parser.py    # Log event detection
│       └── webhook_auth.py  # Token generation/management
├── templates/
│   ├── config.toml.template
│   ├── systemd.service.template
│   └── launchd.plist.template
└── tests/
```

**Dependencies:**
- `click` or `typer` - CLI framework
- `requests` - HTTP client for webhooks
- `toml` - Configuration parsing
- `mcrcon` - RCON client
- `watchdog` - File system monitoring (for log parsing)
- `psutil` - Process and system monitoring
- `rich` - Beautiful terminal output

### Discord Bot Architecture (FastAPI)

**Hosted on Oracle Free Tier:**
```
discord-bot/
├── main.py                  # FastAPI application entry point
├── bot.py                   # Discord.py bot client
├── webhook_handler.py       # Webhook endpoint logic
├── database.py              # SQLite for token -> channel mapping
├── rate_limiter.py          # Rate limiting middleware
├── notification_service.py  # Format and send Discord messages
└── config.py                # Bot configuration
```

**Deployment:**
- Docker container on Oracle ARM instance
- Nginx reverse proxy with SSL (Let's Encrypt)
- systemd service for auto-restart
- SQLite database for webhook registrations
- Logging with logrotate

**API Endpoints:**
```
POST /webhook/register       # Register new webhook token
POST /webhook/event          # Send notification event
POST /webhook/query          # Query server status (for slash commands)
GET /health                  # Health check
GET /metrics                 # Prometheus metrics (optional)
```

---

## Success Criteria

### Phase 1 (Core CLI)
- ✅ User can install vmc via Homebrew
- ✅ User can initialize and start Minecraft server with single command
- ✅ User can manage mods without manual file operations
- ✅ User can create/restore backups
- ✅ Server runs stably with auto-restart on crash

### Phase 2 (Discord Integration)
- ✅ User can configure Discord notifications in < 5 minutes
- ✅ Notifications appear in Discord within 2 seconds of events
- ✅ Slash commands return accurate server data
- ✅ Zero unauthorized access to user servers (security audit)
- ✅ Public bot maintains 99.9% uptime

### Phase 3 (Production Ready)
- ✅ Comprehensive documentation (installation, configuration, troubleshooting)
- ✅ Automated tests (unit + integration)
- ✅ Health checks catch 95% of common configuration errors
- ✅ Update process is seamless (no downtime)
- ✅ Community feedback incorporated (Discord server, GitHub issues)

---

## Non-Goals (Out of Scope for MVP)

- ❌ Web-based admin panel (CLI-first approach)
- ❌ Multi-server management (one server per vmc installation)
- ❌ Built-in voice chat (use existing mods like Simple Voice Chat)
- ❌ Custom plugin development (Fabric mods only)
- ❌ Paid hosting service (users bring their own infrastructure)
- ❌ Mobile app (Discord mobile is sufficient)
- ❌ Automatic mod compatibility checking (user responsibility)
- ❌ In-game chat bridge (Discord <-> Minecraft chat)

---

## Timeline Estimate

**Phase 1**: 2 weeks
**Phase 2**: 2 weeks  
**Phase 3**: 2 weeks

**Total MVP**: 6 weeks for solo developer, 4 weeks with 2 developers

---

## Post-MVP Roadmap

### Version 1.1 (Quality of Life)
- Plugin system for custom vmc extensions
- Advanced log analysis (crash detection patterns)
- Backup to cloud storage (S3, B2, Oracle Object Storage)
- Performance profiling tools (spark integration)

### Version 1.2 (Community Features)
- Mod pack support (import from CurseForge, Modrinth)
- Server templates (share configurations)
- Migration tools (import from existing servers)
- Discord slash command customization

### Version 2.0 (Advanced)
- Multi-server management
- Web dashboard
- Proxy support (Velocity, BungeeCord)
- Metrics and analytics (Grafana integration)

---

## Open Questions for Discussion

1. **Homebrew Distribution**: Tap vs. official Homebrew core?
2. **Bot Branding**: Custom bot name or generic "void-mc Bot"?
3. **Pricing Model**: Free tier limits? Premium features?
4. **Platform Support**: macOS + Linux only, or Windows via WSL?
5. **Database Choice**: SQLite vs. PostgreSQL for bot webhook registry?
6. **Monitoring**: Self-hosted Prometheus or cloud service?

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-24  
**Author**: void-mc team
