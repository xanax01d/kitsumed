<div align="center">

<img src="assets/images/en/hero_banner.png" alt="Migrebot Banner" width="100%" style="border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 16px;" />

# 🧠 Migrebot Analog (Rust Edition)
### High-Performance Telegram Headache & Migraine Diary Bot written in pure Rust

[![Rust](https://img.shields.io/badge/Rust-1.85%2B-DEA584?style=for-the-badge&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![teloxide](https://img.shields.io/badge/teloxide-0.13-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://teloxide.rs/)
[![tokio](https://img.shields.io/badge/tokio-async-blue?style=for-the-badge&logo=rust&logoColor=white)](https://tokio.rs/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![sqlx](https://img.shields.io/badge/sqlx-0.8-green?style=for-the-badge)](https://github.com/launchbadge/sqlx)
[![i18n](https://img.shields.io/badge/Languages-5%20Locales-9cf?style=for-the-badge&logo=google-translate&logoColor=white)](#3-🌐-multilingual-support-5-locales)
[![Follow-up](https://img.shields.io/badge/Follow--up-Automated%20Check-blueviolet?style=for-the-badge&logo=clockify&logoColor=white)](#2-🩺-automated-follow-up--medication-efficacy-tracking)
[![Rich Messages](https://img.shields.io/badge/Telegram-Rich%20Components%20TG--13-informational?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)
[![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](LICENSE)

<p align="center">
  <a href="README.md"><b>🇷🇺 Русский</b></a> &nbsp;•&nbsp; 🇬🇧 <b>English</b>
</p>

<p align="center">
  <b>Smart bot for structured tracking of headache symptoms, character, and intensity,<br>
  featuring in-message button interfaces (Telegram Rich Text TG-13), automated pain relief follow-ups, and clinical reporting.</b>
</p>

<p align="center">
  <a href="#-key-features">✨ Features</a> •
  <a href="#-system-architecture">📐 Architecture</a> •
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

Fully asynchronous, resilient architecture built entirely in **Rust** (single compiled binary, zero-cost abstractions), multi-threaded **Tokio** runtime, **SQLx** connection pool, and **PostgreSQL**:

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Telegram Client & Rich UI** | Telegram Bot API 8+ (Rich Messages TG-13) | In-message interactive buttons (`<tg-button-row>`, `<tg-button>`), collapsible blockquotes (`<blockquote expandable>`), and hero banners |
| **Core Engine** | `teloxide 0.13` + `tokio` (Rust) | High-throughput asynchronous update routing, thread-safe in-memory session store (`Arc<RwLock<SessionStore>>`) |
| **Primary Database** | `PostgreSQL 14+` (`sqlx 0.8`) | Asynchronous connection pool `sqlx::PgPool`, compile-time query verification, automatic schema migrations, and JSONB fields |
| **Follow-up Scheduler** | Tokio Background Task | Automated background timer checking pain resolution 2 hours after episode onset and recording medication efficacy |
| **Reminder Scheduler** | Tokio Background Task | Daily wellness check-in scheduler with per-user timezone resolution (Chrono + Chrono-Tz) |
| **Localization Engine** | Compile-time embedded JSON | Zero-latency multilingual dictionaries via `include_str!` and `LazyLock<HashMap>` without disk I/O |

---

## 🌟 Key Features

### 1. ⏱ Structured Questionnaire with Rich UI
- **Buttons inside text (TG-13)**: Navigation, pain sliders, and checkboxes are embedded directly within the message bubble.
- **Onset Time**: Quick presets (*Right now, 30m ago, 1h ago, 2h ago*) or custom time input.
- **Pain Scale (1–10)**: Clear severity gradation from mild (1) to unbearable (10 🔥).
- **Headache Location**: Left, right, bilateral, forehead/temples, back of head, diffuse.
- **Pain Quality**: Throbbing, pressing, stabbing, dull.
- **Associated Symptoms**: Interactive real-time multi-select toggles ✅ (nausea, vomiting, photophobia, phonophobia, aura, dizziness).
- **Triggers**: Multi-select of common factors (stress, lack of sleep, weather changes, fatigue, alcohol, skipped meals).
- **Medications & Relief**: Specific medication tracking, intake delay calculation, and efficacy recording.

### 2. 🩺 Automated Follow-up & Medication Efficacy
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
- 🦾 **Cyberpunk 2077 (`cyberpunk`)**: Immersive Night City theme.

### 4. 📅 Interactive Monthly Calendar (`/history` / `/calendar`)
- Visual month grid marking pain days (🔴) and symptom-free days (🟢).
- Month-by-month navigation and detailed daily cards.

### 5. ⏰ Personalized Daily Check-ins
- Scheduled daily check-ins (*"Did you experience any headache today?"*).
- Full timezone support across all standard IANA identifiers and UTC offsets.

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
| `/help` | User guide and headache pain scale explanation |
| `/cancel` | Cancel active questionnaire and return to menu |

---

## 🛠 Technology Stack

- **Core**: Rust 1.85+ (Edition 2021)
- **Telegram Bot Framework**: `teloxide 0.13`
- **Async Runtime**: `tokio 1.x`
- **Database**: `PostgreSQL 14+` with `sqlx 0.8`
- **Time & Timezones**: `chrono`, `chrono-tz`
- **Serialization**: `serde`, `serde_json`
- **UI Format**: Telegram Rich Text (HTML model with `<tg-button-row>`, `<tg-button>`, `<blockquote expandable>`)
- **Process Manager**: `systemd`

---

## 📂 Project Structure

```text
migrebot_analog/
├── assets/
│   └── images/            # Localized banners and graphic cards
│       ├── ru/
│       ├── be/
│       ├── en/
│       ├── meme/
│       └── cyberpunk/
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
│   ├── main.rs            # Entry point & dispatcher
│   ├── models.rs          # Domain structs
│   ├── rich.rs            # Rich Text TG-13 generator with in-message buttons
│   ├── services/
│   │   ├── export.rs
│   │   ├── mod.rs
│   │   └── schedulers.rs  # Background Tokio workers
│   └── session.rs         # In-memory FSM state store
├── Cargo.toml             # Rust dependency manifest
├── Cargo.lock
├── Dockerfile             # Multi-stage lightweight Docker image
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/xanax01d/migrebot_analog.git
cd migrebot_analog
```

### 2. Configuration (`.env`)
Create a `.env` file in the project root:

```dotenv
TELOXIDE_TOKEN="your_telegram_bot_token"
DATABASE_URL="postgres://migrebot:your_password@127.0.0.1:5432/migrebot"
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
./target/release/migrebot
```

---

## 🚀 Server Deployment (Systemd)

1. Build release binary in `/opt/migrebot`:
   ```bash
   cd /opt/migrebot
   cargo build --release
   ```

2. Create systemd service `/etc/systemd/system/migrebot.service`:
   ```ini
   [Unit]
   Description=Migrebot Rust Telegram Bot
   After=network.target postgresql.service
   Wants=postgresql.service

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/migrebot
   ExecStart=/opt/migrebot/target/release/migrebot
   EnvironmentFile=/opt/migrebot/.env
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
   systemctl enable migrebot.service
   systemctl restart migrebot.service
   ```

4. Stream logs:
   ```bash
   journalctl -u migrebot.service -f
   ```

---

<div align="center">
  <sub>Pure Rust • Blazing Fast • Rich Telegram UI</sub>
</div>
