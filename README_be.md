<div align="center">

<img src="assets/images/be/hero_banner.png" alt="Migrebot Banner" width="100%" style="border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 16px;" />

# 🧠 Migrebot Analog (Rust Edition)
### Высокапрадукцыйны Telegram-дзённік прыступаў мігрэні і галаўнога болю на чыстым Rust

[![Rust](https://img.shields.io/badge/Rust-1.85%2B-DEA584?style=for-the-badge&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![teloxide](https://img.shields.io/badge/teloxide-0.13-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://teloxide.rs/)
[![tokio](https://img.shields.io/badge/tokio-async-blue?style=for-the-badge&logo=rust&logoColor=white)](https://tokio.rs/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-FSM%20Sessions-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![sqlx](https://img.shields.io/badge/sqlx-0.8-green?style=for-the-badge)](https://github.com/launchbadge/sqlx)
[![i18n](https://img.shields.io/badge/Languages-5%20Locales-9cf?style=for-the-badge&logo=google-translate&logoColor=white)](#4-🌐-мультымоўнасць-5-лакалей)
[![Follow-up](https://img.shields.io/badge/Follow--up-Аўтаматычны%20кантроль-blueviolet?style=for-the-badge&logo=clockify&logoColor=white)](#2-🩺-аўтаматычны-follow-up-і-ацэнка-прэпаратаў)
[![Rich Messages](https://img.shields.io/badge/Telegram-Rich%20Components%20TG--13-informational?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)
[![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](LICENSE)

<p align="center">
  <a href="README.md"><b>🇷🇺 Русский</b></a> &nbsp;•&nbsp; 🇧🇾 <b>Беларуская</b> &nbsp;•&nbsp; <a href="README_en.md"><b>🇬🇧 English</b></a>
</p>

<p align="center">
  <b>Разумны бот для структураванай фіксацыі сімптомаў, характару і інтэнсіўнасці болю,<br>
  з кнопкамі ўнутры тэксту паведамленняў (Telegram Rich Text TG-13), аўтаматычным кантролем палёгкі і выгрузкай справаздач для лекара.</b>
</p>

<p align="center">
  <a href="#-асноўныя-магчымасці">✨ Магчымасці</a> •
  <a href="#-архітэктура-сістэмы">📐 Архітэктура</a> •
  <a href="#-галерэя-персанажаў">🌸 Персанажы</a> •
  <a href="#-каманды-і-навігацыя">⌨️ Навігацыя</a> •
  <a href="#-стэк-тэхналогій">🛠 Стэк</a> •
  <a href="#-структура-праекта">📂 Структура</a> •
  <a href="#-хуткі-старт">⚙️ Хуткі старт</a> •
  <a href="#-разгортванне-на-серверы-systemd">🚀 Дэплой</a> •
  <a href="#-база-даных">📋 База даных</a>
</p>

</div>

---

## 📐 Архітэктура сістэмы

Цалкам асінхронная адмоваўстойлівая архітэктура на базе чыстага **Rust** (кампіляваны бінарнік з нулявым аверхедам), шматпатокавага рантайму **Tokio**, пула злучэнняў **SQLx**, размеркаванага **Redis** для FSM-сесій і СУБД **PostgreSQL**:

| Кампанент | Тэхналогія | Прызначэнне |
| :--- | :--- | :--- |
| **Telegram Client & Rich UI** | Telegram Bot API 8+ (Rich Messages TG-13) | Інтэрактыўныя кнопкі ўнутры тэксту паведамленняў (`<tg-button-row>`, `<tg-button>`), спайлеры і згортвальныя блокі (`<blockquote expandable>`), убудаваныя медыя |
| **Core Engine** | `teloxide 0.13` + `tokio` (Rust) | Высокапрадукцыйны асінхронны роўтынг паведамленняў і колбэкаў, надзейная апрацоўка патокаў апдэйтаў |
| **Session Cache (Redis)** | `redis 0.27` (`tokio-comp`) | Персістэнтнае захаванне незавершаных апытанняў і станаў FSM па ключу `migrebot:session:{user_id}` з TTL 7200 сек (2 гадзіны) |
| **Primary Database** | `PostgreSQL 14+` (`sqlx 0.8`) | Пул асінхронных злучэнняў `sqlx::PgPool`, строгая тыпізацыя, міграцыі схемы, гісторыя прыступаў (JSONB) і профілі карыстальнікаў |
| **Follow-up Scheduler** | Tokio Background Task | Фанавы варкер кантролю сціхання болю праз 2 гадзіны пасля пачатку прыступу і збору клінічнай ацэнкі эфектыўнасці лекаў |
| **Reminder Scheduler** | Tokio Background Task | Фанавы планіроўшчык штодзённых чэк-інаў з улікам індывідуальных часавых паясоў (Chrono + Chrono-Tz) |
| **Localization Engine** | Compile-time embedded JSON | Імгненная лакалізацыя на 5 моў праз `include_str!` і `LazyLock<HashMap>` без дыскавага I/O у рантайме |

---

## 🌸 Галерэя персанажаў (5 анімэ-стыляў лакалізацый)

Кожная лакалізацыя суправаджаецца унікальным мастацкім анімэ-банерам:

| 🇧🇾 Беларуская (`be`) | 🇷🇺 Русский (`ru`) | 🇬🇧 English (`en`) |
| :---: | :---: | :---: |
| <img src="assets/images/be/hero_banner.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/ru/hero_banner.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/en/hero_banner.png" width="100%" style="border-radius: 8px;" /> |
| **Лісічка ў вышыванцы з васількамі** | **Клінічная класіка** | **ICHD-3 Medical English** |

| 🎭 Мемны (`meme`) | 🦾 Cyberpunk 2077 (`cyberpunk`) |
| :---: | :---: |
| <img src="assets/images/meme/hero_banner.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/cyberpunk/hero_banner.png" width="100%" style="border-radius: 8px;" /> |
| **Вайбовая мемная атмасфера** | **Неонавы нэтранэр & Хром** |

---

## 🌟 Асноўныя магчымасці

### 1. ⏱ Пакрокавы апытальнік з Rich Text інтэрфейсам
- **Кнопкі ўнутры тэксту (Telegram TG-13)**: Кнопкі навігацыі, шкалы болю і выбару сімптомаў убудаваныя непасрэдна ў цела паведамлення праз тэгі `<tg-button-row>` і `<tg-button>`.
- **Час пачатку**: Хуткія прэсэты (*Толькі што, 30 хвілін таму, 1 гадзіну таму, 2 гадзіны таму*) альбо дакладны час.
- **Шкала болю (1–10)**: Зразумелая градацыя ад ледзь адчувальнай (1) да невыноснай (10 🔥).
- **Лакалізацыя цэфалагіі**: Злева, справа, з абодвух бакоў, лоб/скроні, патыліца, дыфузны боль.
- **Характар болю**: Пульсуючы, сціскаючы, колючы, тупы.
- **Мультыселект сімптомаў**: Кнопкі з дынамічным пераключэннем ✅ у рэальным часе (млоснасць, ваніты, святлабоязь, гукабоязь, аўра, галавакружэнне).
- **Збор трыгераў**: Мультывыбар ключавых правакацыйных фактараў (стрэс, недасыпанне, надвор'е, стомленасць, алкаголь, пропуск ежы).
- **Медыкаменты і дазіроўка**: Выбар канкрэтнага прэпарата, указанне затрымкі прыёму і ацэнка купіравання.

<div align="center">
<table>
  <tr>
    <td align="center" width="50%">
      <b>⏱ Крок 1: Час пачатку прыступу</b><br>
      <img src="assets/images/ru/steps/start_time.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
    <td align="center" width="50%">
      <b>📊 Крок 2: Шкала інтэнсіўнасці болю (1–10)</b><br>
      <img src="assets/images/ru/steps/pain_scale.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>🎯 Крок 3: Лакалізацыя цэфалагіі</b><br>
      <img src="assets/images/ru/steps/location.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
    <td align="center" width="50%">
      <b>⚡️ Крок 4: Характар болю</b><br>
      <img src="assets/images/ru/steps/pain_type.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>🩺 Крок 5: Сімптомы і аўра</b><br>
      <img src="assets/images/ru/steps/symptoms.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
    <td align="center" width="50%">
      <b>🌪 Крок 6: Правакацыйныя трыгеры</b><br>
      <img src="assets/images/ru/steps/triggers.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>💊 Крок 7: Медыкаменты і дазіроўка</b><br>
      <img src="assets/images/ru/steps/medication.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
    <td align="center" width="50%">
      <b>🛡 Крок 8: Пацверджанне запісу</b><br>
      <img src="assets/images/ru/steps/confirm.png" width="100%" style="border-radius: 8px; margin-top: 6px;" />
    </td>
  </tr>
</table>
</div>

### 2. 🩺 Аўтаматычны follow-up і ацэнка прэпаратаў
- **Кантроль праз 2 гадзіны**: Фанавы таймер Tokio аўтаматычна знаходзіць адкрытыя прыступы і дасылае запыт: *«Ці прайшоў галаўны боль?»*.
- **Фіксацыя часу сціхання**: Хуткія кнопкі адказу (*толькі што, 30 хвілін таму, 1 гадзіну таму, 2 гадзіны таму*).
- **Ацэнка эфектыўнасці**: Фіксацыя клінічнага дзеяння лекаў:
  - `🟢 Дапамагло` (`helped`)
  - `🟡 Часткова` (`partially`)
  - `🔴 Не дапамагло` (`not_helped`)

### 3. 🌐 Мультымоўнасць (5 лакалей)
- 🇧🇾 **Беларуская (`be`)**: Аўтэнтычная беларуская мова з нацыянальнай атрыбутыкай.
- 🇷🇺 **Русский (`ru`)**: Класічная акадэмічная медыцынская тэрміналогія.
- 🇬🇧 **English (`en`)**: Міжнародная тэрміналогія (ICHD-3).
- 🎭 **Мемны слэнг (`meme`)**: Вірусны рунэтаўскі слэнг.
- 🦾 **Cyberpunk 2077 (`cyberpunk`)**: Стылістыка неонавага нэтранэра, нейраглітчы, пратаколы Trauma Team і трываласць хрому.

### 4. 📅 Інтэрактыўны каляндар прыступаў (`/calendar` / `/history`)
- Месячная сетка з індыкацыяй дзён болю (🔴) і бессімптомых дзён (🟢).
- Зручная навігацыя па месяцах наперад/назад і падрабязныя карткі дзён.

<div align="center">
  <img src="assets/images/ru/history.png" alt="Інтэрактыўны каляндар" width="85%" style="border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.15); margin-top: 8px;" />
</div>

### 5. ⏰ Штодзённыя персаналізаваныя чэк-іны
- Рэгулярнае апытанне ва ўсталяваны карыстальнікам час (*«Ці балела галава сёння?»*).
- Поўная падтрымка часавых паясоў (Мінск, Варшава, Вільня, Кіеў, Масква і сусветныя зоны).

### 6. 📊 Клінічны экспарт справаздачы для лекара (`/export`)
- Структураваныя выгрузкі гісторыі эпізодаў, трыгераў і эфектыўнасці медыкаментаў.

<div align="center">
  <img src="assets/images/ru/export.png" alt="Клінічны экспарт" width="85%" style="border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.15); margin-top: 8px;" />
</div>

---

## ⌨️ Каманды і навігацыя

| Каманда | Прызначэнне |
| :--- | :--- |
| `/start` | Прывітанне, рэгістрацыя ў БД і адкрыццё галоўнага Rich-меню |
| `/menu` | Галоўнае інтэрактыўнае меню з кнопкамі |
| `/log`, `/headache` | Запуск пакрокавага апытальніка фіксацыі прыступу болю |
| `/status` | Праверка актыўнага прыступу і статусу купіравання |
| `/calendar`, `/history` | Інтэрактыўны каляндар прыступаў па днях |
| `/reminder`, `/settings` | Меню налады штодзённага чэк-іну і часавога пояса |
| `/language` | Выбар мовы інтэрфейсу (BE, RU, EN, Meme, Cyberpunk) |
| `/help` | Даведачная інфармацыя па шкале болю і вядзенні дзённіка |
| `/cancel` | Перапыненне бягучага сцэнарыя і вяртанне ў галоўнае меню |

---

## 🛠 Стэк тэхналогій

- **Ядро**: Rust 1.85+ (Edition 2021)
- **Фрэймворк Telegram**: `teloxide 0.13`
- **Асінхронны рантайм**: `tokio 1.x`
- **База даных**: `PostgreSQL 14+` + пул злучэнняў `sqlx 0.8`
- **FSM кэш**: `redis 0.27` (`tokio-comp`) з аўтаматычным TTL
- **Час і таймзоны**: `chrono` + `chrono-tz`
- **Серыялізацыя**: `serde`, `serde_json`
- **Інтэрфейс UI**: Telegram Rich Text (HTML-мадэль з `<tg-button-row>`, `<tg-button>`, `<blockquote expandable>`)
- **Менеджар сэрвісаў**: `systemd`

---

## 📂 Структура праекта

```text
migrebot_analog/
├── assets/
│   └── images/            # Анімэ-банеры персанажаў для кожнай лакалі
│       ├── be/            # Беларускі банер (лісічка ў вышыванцы з васількамі)
│       ├── ru/            # Расійскі банер
│       ├── en/            # Англійскі банер
│       ├── meme/          # Мемны банер
│       └── cyberpunk/     # Cyberpunk банер
├── locales/               # Чыстыя JSON-слоўнікі лакалізацыі
│   ├── be.json
│   ├── ru.json
│   ├── en.json
│   ├── meme.json
│   └── cyberpunk.json
├── src/                   # Зыходны код на чыстым Rust
│   ├── db.rs              # SQLx-запыты да PostgreSQL і ініцыялізацыя табліц
│   ├── handlers/          # Апрацоўшчыкі каманд, колбэкаў і дыялогаў
│   │   ├── calendar.rs    # Каляндарная сетка і гісторыя
│   │   ├── commands.rs    # Сістэмныя каманды (/start, /menu, /help, /cancel)
│   │   ├── export.rs      # Экспарт даных
│   │   ├── followup.rs    # Кантроль сціхання болю і ацэнка лекаў
│   │   ├── headache.rs    # Пакрокавы FSM-апытальнік прыступу
│   │   ├── language.rs    # Змена мовы
│   │   ├── mod.rs
│   │   └── reminder.rs    # Налады чэк-іну і часавых паясоў
│   ├── keyboards.rs       # Генератары інлайн-клавіятур
│   ├── locales/
│   │   └── mod.rs         # Убудаванне JSON у бінарнік і функцыі get_text / get_text_fmt
│   ├── main.rs            # Точка ўваходу, пул БД, кліент Redis і дыспетчар Teloxide
│   ├── models.rs          # Даменныя структуры даных
│   ├── rich.rs            # Генератар Rich-паведамленняў TG-13 з убудаванымі кнопкамі
│   ├── services/
│   │   ├── export.rs
│   │   ├── mod.rs
│   │   └── schedulers.rs  # Фанавыя Tokio-варкеры для чэк-інаў і follow-up
│   └── session.rs         # Персістэнтнае сховішча FSM у Redis з in-memory fallback
├── Cargo.toml             # Маніфест залежнасцей Rust
├── Cargo.lock
├── Dockerfile             # Multi-stage Dockerfile
├── docker-compose.yml
└── README_be.md           # Беларуская дакументацыя праекта
```

---

## ⚙️ Хуткі старт

### 1. Кланаванне рэпазіторыя
```bash
git clone https://github.com/xanax01d/migrebot_analog.git
cd migrebot_analog
```

### 2. Канфігурацыя (`.env`)
Стварыце файл `.env` у корані праекта:

```dotenv
# Токен бота Telegram
TELOXIDE_TOKEN="your_telegram_bot_token"

# База даных PostgreSQL
DATABASE_URL="postgres://migrebot:your_password@127.0.0.1:5432/migrebot"
# Альбо асобныя параметры:
# POSTGRES_HOST=127.0.0.1
# POSTGRES_PORT=5432
# POSTGRES_USER=migrebot
# POSTGRES_PASSWORD=your_password
# POSTGRES_DB=migrebot

# Кэш FSM-сесій Redis
REDIS_URL="redis://127.0.0.1:6379"
# Альбо асобныя параметры падключэння:
# REDIS_HOST=127.0.0.1
# REDIS_PORT=6379
# REDIS_PASSWORD=""

# Лагіраванне
RUST_LOG="info"
```

### 3. Зборка і запуск
```bash
# Праверка кампіляцыі
cargo check

# Запуск у dev-рэжыме
cargo run

# Зборка аптымізаванага рэлізнага бінарніка
cargo build --release
./target/release/migrebot
```

### 4. Запуск праз Docker Compose (PostgreSQL + Redis + Bot)
```bash
docker-compose up -d
```

---

## 🚀 Разгортванне на серверы (Systemd)

1. Збярыце рэлізны бінарнік у `/opt/migrebot`:
   ```bash
   cd /opt/migrebot
   cargo build --release
   ```

2. Стварыце канфігурацыю службы `/etc/systemd/system/migrebot.service`:
   ```ini
   [Unit]
   Description=Migrebot Rust Telegram Bot
   After=network.target postgresql.service redis-server.service
   Wants=postgresql.service redis-server.service

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

3. Перазапусціце сэрвіс:
   ```bash
   systemctl daemon-reload
   systemctl enable migrebot.service
   systemctl restart migrebot.service
   ```

---

<div align="center">
  <sub>Pure Rust • Анімэ-стылістыка • Высокая прадукцыйнасць • Rich Telegram UI</sub>
</div>
