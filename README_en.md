<div align="center">

<img src="assets/images/en/hero_banner.png" alt="KitsuMed Banner" width="100%" style="border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 20px;" />

<hr style="margin: 20px 0; border: none; border-top: 1px solid rgba(128,128,128,0.2);" />

<img src="assets/images/avatar_4k.png" alt="KitsuMed Logo" width="180" style="margin: 10px 0;" />

# 🦊 KitsuMed
### High-Performance Telegram Headache & Migraine Diary Bot written in pure Rust

<p align="center">
  <a href="https://t.me/KitsuMedBot">
    <img src="https://img.shields.io/badge/Telegram_Bot-@KitsuMedBot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Launch Bot in Telegram" />
  </a>
</p>

[![Rust](https://img.shields.io/badge/Rust-1.85%2B-DEA584?style=for-the-badge&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![teloxide](https://img.shields.io/badge/teloxide-0.13-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://teloxide.rs/)
[![tokio](https://img.shields.io/badge/tokio-async-blue?style=for-the-badge&logo=rust&logoColor=white)](https://tokio.rs/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-FSM%20Sessions-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![sqlx](https://img.shields.io/badge/sqlx-0.8-green?style=for-the-badge)](https://github.com/launchbadge/sqlx)
[![i18n](https://img.shields.io/badge/Languages-5%20Locales-9cf?style=for-the-badge&logo=google-translate&logoColor=white)](#3-🌐-multilingual-support-5-locales)
[![Follow-up](https://img.shields.io/badge/Follow--up-Automated%20Check-blueviolet?style=for-the-badge&logo=clockify&logoColor=white)](#2-🩺-automated-follow-up--medication-efficacy-tracking)
[![Rich Messages](https://img.shields.io/badge/Telegram-Rich%20Components%20TG--13-informational?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)
[![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](LICENSE)
[![Donate](https://img.shields.io/badge/Donate-Tribute-FF5B5B?style=for-the-badge&logo=telegram&logoColor=white)](https://web.tribute.tg/d/TXJ)
[![Channel](https://img.shields.io/badge/Channel-Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/kitsumed)

<p align="center">
  <a href="README.md"><b>🇷🇺 Русский</b></a> &nbsp;•&nbsp; <a href="README_be.md"><b>🇧🇾 Беларуская</b></a> &nbsp;•&nbsp; 🇬🇧 <b>English</b>
</p>

<p align="center">
  🤖 <b>Telegram Bot:</b> <a href="https://t.me/KitsuMedBot"><b>@KitsuMedBot</b></a> &nbsp;•&nbsp; 📢 <b>Channel:</b> <a href="https://t.me/kitsumed"><b>@kitsumed</b></a><br>
  <b>Smart bot for structured tracking of headache symptoms, character, and intensity,<br>
  featuring in-message button interfaces (Telegram Rich Text TG-13), automated pain relief follow-ups, and clinical reporting.</b>
</p>

<p align="center">
  <a href="#-key-features">✨ Features</a> •
  <a href="#-system-architecture">📐 Architecture</a> •
  <a href="#-character-gallery">🌸 Characters</a> •
  <a href="#-commands--navigation">⌨️ Navigation</a> •
  <a href="#-technology-stack">🛠 Tech Stack</a> •
  <a href="#-project-structure">📂 Structure</a> •
  <a href="#-quick-start">⚙️ Quick Start</a> •
  <a href="#-server-deployment-systemd">🚀 Deployment</a> •
  <a href="#-database-schema">📋 Database</a>
</p>

</div>

---

## 📐 System Architecture

Fully asynchronous, resilient architecture built entirely in **Rust** (single compiled binary, zero-cost abstractions), multi-threaded **Tokio** runtime, **SQLx** connection pool, distributed **Redis** for FSM sessions, and **PostgreSQL**:

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Telegram Client & Rich UI** | Telegram Bot API 8+ (Rich Messages TG-13) | In-message interactive buttons (`<tg-button-row>`, `<tg-button>`), collapsible blockquotes (`<blockquote expandable>`), and hero banners |
| **Core Engine** | `teloxide 0.13` + `tokio` (Rust) | High-throughput asynchronous update routing, robust event stream processing |
| **Session Cache (Redis)** | `redis 0.27` (`tokio-comp`) | Persistent storage for in-flight surveys and FSM states at `kitsumed:session:{user_id}` with 7200s (2h) TTL |
| **Primary Database** | `PostgreSQL 14+` (`sqlx 0.8`) | Asynchronous connection pool `sqlx::PgPool`, compile-time query verification, automatic schema migrations, and JSONB fields |
| **Follow-up Scheduler** | Tokio Background Task | Automated background timer checking pain resolution 2 hours after episode onset and recording medication efficacy |
| **Reminder Scheduler** | Tokio Background Task | Daily wellness check-in scheduler with per-user timezone resolution (Chrono + Chrono-Tz) |
| **Localization Engine** | Compile-time embedded JSON | Zero-latency multilingual dictionaries via `include_str!` and `LazyLock<HashMap>` without disk I/O |

---

## 🌸 Kitsune Gallery (Anime Mascots for 5 Locales)

Each locale features its own unique stylized anime fox girl (kitsune) mascot:

| 🇧🇾 Belarusian (`be`) | 🇷🇺 Russian (`ru`) | 🇬🇧 English (`en`) |
| :---: | :---: | :---: |
| <img src="assets/images/readme/be_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/ru_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/en_kitsune.png" width="100%" style="border-radius: 8px;" /> |
| **Kitsune in Vyshyvanka** | **Neurologist Kitsune Doctor** | **British Scholar Kitsune** |

| 🎭 Meme (`meme`) | 🦾 Cyberpunk 2077 (`cyberpunk`) |
| :---: | :---: |
| <img src="assets/images/readme/meme_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/cyberpunk_kitsune.png" width="100%" style="border-radius: 8px;" /> |
| **Vibe Meme Atmosphere** | **Neon Netrunner & Chrome** |

---

## 🌟 Key Features

<p align="center">
  <img src="assets/images/en/hero_banner.png" alt="KitsuMed Key Features" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

### 1. ⏱ Structured Questionnaire with Rich UI

<p align="center">
  <img src="assets/images/readme/sections/en/survey.jpg" alt="Structured Questionnaire with Rich UI" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- **Buttons inside text (TG-13)**: Navigation, pain sliders, and checkboxes are embedded directly within the message bubble.
- **Onset Time**: Quick presets (*Right now, 30m ago, 1h ago, 2h ago*) or custom time input.
- **Pain Scale (1–10)**: Clear severity gradation from mild (1) to unbearable (10 🔥).
- **Headache Location**: Left, right, bilateral, forehead/temples, back of head, diffuse.
- **Pain Quality**: Throbbing, pressing, stabbing, dull.
- **Associated Symptoms**: Interactive real-time multi-select toggles ✅ (nausea, vomiting, photophobia, phonophobia, aura, dizziness).
- **Triggers**: Multi-select of common factors (stress, lack of sleep, weather changes, fatigue, alcohol, skipped meals).
- **Medications & Relief**: Specific medication tracking, intake delay calculation, and efficacy recording.

### 2. 🩺 Automated Follow-up & Medication Efficacy

<p align="center">
  <img src="assets/images/readme/sections/en/followup.jpg" alt="Automated Follow-up & Medication Efficacy" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- **2-Hour Check**: Automatically prompts the user: *"Has your headache resolved?"*.
- **Resolution Timing**: Quick responses (*just now, 30 min ago, 1 hour ago, 2 hours ago*).
- **Medication Relief Rating**:
  - `🟢 Helped` (`helped`)
  - `🟡 Partially` (`partially`)
  - `🔴 Did not help` (`not_helped`)

### 3. 🌐 Multilingual Support (5 Locales)
- 🇷🇺 **Russian (`ru`)**: Academic clinical terminology.
- 🇧🇾 **Belarusian (`be`)**: Authentic Belarusian with national attributes.
- 🇬🇧 **English (`en`)**: International standard terminology (ICHD-3).
- 🎭 **Meme (`meme`)**: Internet slang.
- 🦾 **Cyberpunk 2077 (`cyberpunk`)**: Neon netrunner aesthetic, neuro-glitches, Trauma Team protocols, and chrome resilience.

> 💡 **Want to contribute your language?** Check out our [Localization Contributor Guide](docs/LOCALIZATION_en.md).

### 4. 📅 Interactive Monthly Calendar (`/history` / `/calendar`)

<p align="center">
  <img src="assets/images/readme/sections/en/calendar.jpg" alt="Interactive Monthly Calendar" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- Visual month grid marking pain days (🔴) and symptom-free days (🟢).
- Month-by-month navigation and detailed daily episode cards.

### 5. ⏰ Personalized Daily Check-ins

<p align="center">
  <img src="assets/images/readme/sections/en/reminder.jpg" alt="Personalized Daily Check-ins" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- Scheduled daily check-ins (*"Did you experience any headache today?"*).
- Full timezone support across all standard IANA identifiers and UTC offsets.

### 6. 📊 Clinical Reports for Neurologists (`/export`)

<p align="center">
  <img src="assets/images/readme/sections/en/export.jpg" alt="Clinical Reports for Neurologists" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- Structured data exports detailing episode frequency, severity, triggers, and acute treatment response.

---

## ⌨️ Commands & Navigation

| Command | Action |
| :--- | :--- |
| `/start` | Welcome message, user registration, and main Rich menu |
| `/menu` | Interactive main navigation menu |
| `/log`, `/headache` | Start headache recording flow |
| `/status` | Check active episode details and pain resolution status |
| `/calendar`, `/history` | Interactive monthly calendar of past episodes |
| `/reminder`, `/settings` | Daily check-in and timezone configuration |
| `/language` | Interface language selection (RU, BE, EN, Meme, Cyberpunk) |
| `/donate` | Support project development and cloud hosting |
| `/help` | User guide and headache pain scale explanation |
| `/cancel` | Cancel active questionnaire and return to menu |

---

## 🛠 Technology Stack

- **Core**: Rust 1.85+ (Edition 2021)
- **Telegram Bot Framework**: `teloxide 0.13`
- **Async Runtime**: `tokio 1.x`
- **Database**: `PostgreSQL 14+` with `sqlx 0.8`
- **Session Cache & FSM**: Redis 7+ (`redis 0.27` with `tokio-comp`) — persistent asynchronous survey state storage at `kitsumed:session:{user_id}` with 7200s TTL and memory fallback
- **Time & Timezones**: `chrono`, `chrono-tz`
- **Serialization**: `serde`, `serde_json`
- **UI Format**: Telegram Rich Text (HTML model with `<tg-button-row>`, `<tg-button>`, `<blockquote expandable>`)
- **Process Manager**: `systemd`

---

## 📂 Project Structure

```text
kitsumed/
├── assets/
│   └── images/            # Localized banners and graphic cards
│       ├── ru/            # Russian banner, steps & UI screens
│       ├── be/            # Belarusian banner (kitsune in vyshyvanka)
│       ├── en/            # English banner, steps & UI screens
│       ├── meme/          # Meme banner
│       └── cyberpunk/     # Cyberpunk banner
├── locales/               # Standalone JSON translation dictionaries
│   ├── ru.json
│   ├── be.json
│   ├── en.json
│   ├── meme.json
│   └── cyberpunk.json
├── src/                   # Pure Rust source tree
│   ├── db.rs              # PostgreSQL queries and schema migrations
│   ├── handlers/          # Command, callback, and dialogue handlers
│   │   ├── calendar.rs
│   │   ├── commands.rs
│   │   ├── export.rs
│   │   ├── followup.rs
│   │   ├── headache.rs
│   │   ├── language.rs
│   │   ├── mod.rs
│   │   └── reminder.rs
│   ├── keyboards.rs       # Inline button helpers
│   ├── locales/           # Embedded JSON translation lookup
│   ├── main.rs            # Entry point, DB pool, Redis connection & dispatcher
│   ├── models.rs          # Domain structs
│   ├── rich.rs            # Rich Text TG-13 generator with in-message buttons
│   ├── services/
│   │   ├── export.rs
│   │   ├── mod.rs
│   │   └── schedulers.rs  # Background Tokio workers
│   └── session.rs         # Persistent FSM session store (Redis + In-memory fallback)
├── Cargo.toml             # Rust dependency manifest
├── Cargo.lock
├── Dockerfile             # Multi-stage lightweight Docker image
├── docker-compose.yml     # Compose config for bot, PostgreSQL, and Redis
└── README.md
```

---

## ⚙️ Quick Start

### 🦊 Automated 1-Click Installer (Recommended)
You can launch our interactive installer with a beautiful CLI interface:

```bash
git clone https://github.com/xanax01d/kitsumed.git
cd kitsumed
./install.sh
```
The script automatically performs system diagnostics (OS, RAM, disk space), installs prerequisites, and lets you choose:
- **`[1] 🐳 Docker Compose`** — Bot, PostgreSQL 16, and Redis 7 in isolated containers (with auto-generated `.env`).
- **`[2] ⚡ Native Systemd`** — Native Rust release build & Linux systemd service.
- **`[3] 📊 Check Status`** — Live diagnostics of running containers or service.

CLI flags for automated/CI setups:
```bash
./install.sh --docker --token "YOUR_TOKEN"   # Headless Docker deployment
./install.sh --systemd --token "YOUR_TOKEN"  # Headless Systemd build & launch
./install.sh --status                        # Diagnostics check
```

---

### Manual Setup

#### 1. Clone Repository
```bash
git clone https://github.com/xanax01d/kitsumed.git
cd kitsumed
```

#### 2. Configuration (`.env`)
Create a `.env` file in the project root:

```dotenv
# Telegram Bot Token
TELOXIDE_TOKEN="your_telegram_bot_token"

# Primary Database (PostgreSQL)
DATABASE_URL="postgres://kitsumed:your_password@127.0.0.1:5432/kitsumed"
# Or separate PostgreSQL parameters:
# POSTGRES_HOST=127.0.0.1
# POSTGRES_PORT=5432
# POSTGRES_USER=kitsumed
# POSTGRES_PASSWORD=your_password
# POSTGRES_DB=kitsumed

# FSM Session Cache (Redis)
REDIS_URL="redis://127.0.0.1:6379"
# Or separate Redis parameters:
# REDIS_HOST=127.0.0.1
# REDIS_PORT=6379
# REDIS_PASSWORD=""

# Logging
RUST_LOG="info"
```

### 3. Build & Run
```bash
# Verify compilation
cargo check

# Run in development mode
cargo run

# Build optimized release binary
cargo build --release
./target/release/kitsumed
```

### 4. 🐳 Docker Deployment

The project is fully containerized. The image includes all required components: a lightweight compiled Rust binary, Python 3 with ReportLab, and DejaVu fonts for generating clinical PDF reports.

#### Option A: Run Full Stack via Docker Compose (Recommended)
Spins up isolated PostgreSQL 16, Redis 7, and KitsuMed Bot with one command:

```bash
# 1. Set your Telegram bot token
export TOKEN="your_telegram_bot_token"

# 2. Start all services in the background
docker compose up -d --build

# 3. View live bot logs
docker compose logs -f bot
```

Managing containers:
```bash
docker compose ps          # Check container status
docker compose stop        # Stop services gracefully
docker compose down -v     # Stop and remove volumes (wipes DB)
```

#### Option B: Standalone Docker Image
If you already have PostgreSQL and Redis running:

```bash
# Full multi-stage build from source:
docker build -t kitsumed .

# Or instant build using precompiled release binary:
docker build -f Dockerfile.prebuilt -t kitsumed .

# Run container:
docker run -d \
  --name kitsumed-bot \
  --restart unless-stopped \
  -e TELOXIDE_TOKEN="your_bot_token" \
  -e DATABASE_URL="postgresql://kitsumed:kitsumed_secure_pass@host:5432/kitsumed" \
  -e REDIS_URL="redis://host:6379" \
  -v $(pwd)/assets:/app/assets:ro \
  kitsumed:latest
```

---

## 🚀 Server Deployment (Systemd)

1. Build release binary in `/opt/kitsumed`:
   ```bash
   cd /opt/kitsumed
   cargo build --release
   ```

2. Create systemd service `/etc/systemd/system/kitsumed.service`:
   ```ini
   [Unit]
   Description=KitsuMed Rust Telegram Bot
   After=network.target postgresql.service redis.service
   Wants=postgresql.service redis.service

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/kitsumed
   ExecStart=/opt/kitsumed/target/release/kitsumed
   EnvironmentFile=/opt/kitsumed/.env
   Restart=always
   RestartSec=5
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   systemctl daemon-reload
   systemctl enable kitsumed.service
   systemctl restart kitsumed.service
   ```

4. Stream logs:
   ```bash
   journalctl -u kitsumed.service -f
   ```

---

## 💖 Support the Project

KitsuMed is a completely free, independent, open-source project. If the bot helps you manage and track your headaches or migraines, you can support our server infrastructure and development:

<p align="center">
  <a href="https://web.tribute.tg/d/TXJ">
    <img src="https://img.shields.io/badge/Support_via_Tribute-FF5B5B?style=for-the-badge&logo=telegram&logoColor=white" alt="Support via Tribute" />
  </a>
</p>

---

<div align="center">
  <sub>Pure Rust • Blazing Fast • Rich Telegram UI</sub>
</div>
