<div align="center">

<img src="assets/images/be/hero_banner.png" alt="KitsuMed Banner" width="100%" style="border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 20px;" />

<hr style="margin: 20px 0; border: none; border-top: 1px solid rgba(128,128,128,0.2);" />

<img src="assets/images/avatar_4k.png" alt="KitsuMed Logo" width="180" style="margin: 10px 0;" />

# 🦊 KitsuMed
### Высокапрадукцыйны Telegram-дзённік прыступаў мігрэні і галаўнога болю на чыстым Rust

<p align="center">
  <a href="https://t.me/KitsuMedBot">
    <img src="https://img.shields.io/badge/Telegram_Bot-@KitsuMedBot-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="Запусціць бота ў Telegram" />
  </a>
</p>

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
[![Donate](https://img.shields.io/badge/Donate-Tribute-FF5B5B?style=for-the-badge&logo=telegram&logoColor=white)](https://web.tribute.tg/d/TXJ)
[![Channel](https://img.shields.io/badge/Channel-Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/kitsumed)

<p align="center">
  <a href="README.md"><b>🇷🇺 Русский</b></a> &nbsp;•&nbsp; 🇧🇾 <b>Беларуская</b> &nbsp;•&nbsp; <a href="README_en.md"><b>🇬🇧 English</b></a>
</p>

<p align="center">
  🤖 <b>Тэлеграм-бот:</b> <a href="https://t.me/KitsuMedBot"><b>@KitsuMedBot</b></a> &nbsp;•&nbsp; 📢 <b>Канал:</b> <a href="https://t.me/kitsumed"><b>@kitsumed</b></a><br>
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
| **Session Cache (Redis)** | `redis 0.27` (`tokio-comp`) | Персістэнтнае захаванне незавершаных апытанняў і станаў FSM па ключу `kitsumed:session:{user_id}` з TTL 7200 сек (2 гадзіны) |
| **Primary Database** | `PostgreSQL 14+` (`sqlx 0.8`) | Пул асінхронных злучэнняў `sqlx::PgPool`, строгая тыпізацыя, міграцыі схемы, гісторыя прыступаў (JSONB) і профілі карыстальнікаў |
| **Follow-up Scheduler** | Tokio Background Task | Фанавы варкер кантролю сціхання болю праз 2 гадзіны пасля пачатку прыступу і збору клінічнай ацэнкі эфектыўнасці лекаў |
| **Reminder Scheduler** | Tokio Background Task | Фанавы планіроўшчык штодзённых чэк-інаў з улікам індывідуальных часавых паясоў (Chrono + Chrono-Tz) |
| **Localization Engine** | Compile-time embedded JSON | Імгненная лакалізацыя на 5 моў праз `include_str!` і `LazyLock<HashMap>` без дыскавага I/O у рантайме |

---

## 🌸 Галерэя лісічак (Анімэ-маскоты 5 лакалізацый)

Кожная лакалізацыя суправаджаецца унікальнай ілюстрацыяй маскота-лісічкі:

| 🇧🇾 Беларуская (`be`) | 🇷🇺 Русский (`ru`) | 🇬🇧 English (`en`) |
| :---: | :---: | :---: |
| <img src="assets/images/readme/be_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/ru_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/en_kitsune.png" width="100%" style="border-radius: 8px;" /> |
| **Лісічка ў вышыванцы з васількамі** | **Лісічка-неўролаг у клініцы** | **British Scholar Kitsune** |

| 🎭 Мемны (`meme`) | 🦾 Cyberpunk 2077 (`cyberpunk`) |
| :---: | :---: |
| <img src="assets/images/readme/meme_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/cyberpunk_kitsune.png" width="100%" style="border-radius: 8px;" /> |
| **Вайбовая мемная атмасфера** | **Неонавы нэтранэр & Хром** |

---

## 🌟 Асноўныя магчымасці

<p align="center">
  <img src="assets/images/be/hero_banner.png" alt="Клінічныя магчымасці KitsuMed" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

### 1. ⏱ Пакрокавы апытальнік з Rich Text інтэрфейсам

<p align="center">
  <img src="assets/images/readme/sections/be/survey.jpg" alt="Пакрокавы апытальнік KitsuMed" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- **Кнопкі ўнутры тэксту (Telegram TG-13)**: Кнопкі навігацыі, шкалы болю і выбару сімптомаў убудаваныя непасрэдна ў цела паведамлення праз тэгі `<tg-button-row>` і `<tg-button>`.
- **Час пачатку**: Хуткія прэсэты (*Толькі што, 30 хвілін таму, 1 гадзіну таму, 2 гадзіны таму*) альбо дакладны час.
- **Шкала болю (1–10)**: Зразумелая градацыя ад ледзь адчувальнай (1) да невыноснай (10 🔥).
- **Лакалізацыя цэфалагіі**: Злева, справа, з абодвух бакоў, лоб/скроні, патыліца, дыфузны боль.
- **Характар болю**: Пульсуючы, сціскаючы, колючы, тупы.
- **Мультыселект сімптомаў**: Кнопкі з дынамічным пераключэннем ✅ у рэальным часе (млоснасць, ваніты, святлабоязь, гукабоязь, аўра, галавакружэнне).
- **Збор трыгераў**: Мультывыбар ключавых правакацыйных фактараў (стрэс, недасыпанне, надвор'е, стомленасць, алкаголь, пропуск ежы).
- **Медыкаменты і дазіроўка**: Выбар канкрэтнага прэпарата, указанне затрымкі прыёму і ацэнка купіравання.

### 2. 🩺 Аўтаматычны follow-up і ацэнка прэпаратаў

<p align="center">
  <img src="assets/images/readme/sections/be/followup.jpg" alt="Аўтаматычны follow-up і ацэнка прэпаратаў" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

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

> 💡 **Хочаце дадаць сваю мову?** Азнаёмцеся з [Кіраўніцтвам па стварэнні лакалізацый](docs/LOCALIZATION_be.md).

### 4. 📅 Інтэрактыўны каляндар прыступаў (`/calendar` / `/history`)

<p align="center">
  <img src="assets/images/readme/sections/be/calendar.jpg" alt="Інтэрактыўны каляндар прыступаў" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- Месячная сетка з індыкацыяй дзён болю (🔴) і бессімптомых дзён (🟢).
- Зручная навігацыя па месяцах наперад/назад і падрабязныя карткі дзён.

### 5. ⏰ Штодзённыя персаналізаваныя чэк-іны

<p align="center">
  <img src="assets/images/readme/sections/be/reminder.jpg" alt="Штодзённыя персаналізаваныя чэк-іны" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- Рэгулярнае апытанне ва ўсталяваны карыстальнікам час (*«Ці балела галава сёння?»*).
- Поўная падтрымка часавых паясоў (Мінск, Варшава, Вільня, Кіеў, Масква і сусветныя зоны).

### 6. 📊 Клінічны экспарт справаздачы для лекара (`/export`)

<p align="center">
  <img src="assets/images/readme/sections/be/export.jpg" alt="Клінічны экспарт справаздачы для лекара" width="100%" style="border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); margin-bottom: 16px;" />
</p>

- Структураваныя выгрузкі гісторыі эпізодаў, трыгераў і эфектыўнасці медыкаментаў.

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
| `/donate` | Падтрымаць распрацоўку і аплату сервераў праекта |
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
kitsumed/
├── .github/               # CI/CD аўтаматызацыя і налады спонсарства
│   ├── workflows/         # GitHub Actions (праверка лакалей і тэсты)
│   └── FUNDING.yml        # Канфігурацыя данатаў і Tribute
├── assets/                # Графічныя рэсурсы і шрыфты
│   ├── fonts/             # DejaVu Sans шрыфты для кірыліцы ў PDF-справаздачах
│   └── images/            # Лакалізаваныя банеры персанажаў і візуальныя схемы
│       ├── be/            # Беларускі банер (лісічка ў вышыванцы з васількамі)
│       ├── ru/            # Расійскі банер (доктар Кіцумэ)
│       ├── en/            # British Scholar банеры і экраны
│       ├── meme/          # Мемныя банеры
│       ├── cyberpunk/     # Кіберпанк нэтранэр банеры
│       ├── readme/        # Ілюстрацыі раздзелаў дакументацыі
│       └── avatar_4k.png  # Афіцыйны 4K-маскот праекта
├── docs/                  # Кіраўніцтвы і дакументацыя для супольнасці
│   ├── LOCALIZATION.md    # Кіраўніцтва па даданні моў (RU)
│   ├── LOCALIZATION_be.md # Кіраўніцтва па лакалізацыі (BE)
│   └── LOCALIZATION_en.md # Community Localization Guide (EN)
├── locales/               # Слоўнікі лакалізацыі (i18n) і шаблоны
│   ├── be.json            # Беларускі інтэрфейс
│   ├── ru.json            # Расійскі інтэрфейс
│   ├── en.json            # English interface
│   ├── meme.json          # Мемны рэжым
│   ├── cyberpunk.json     # Кіберпанк 2077 рэжым
│   └── template.json      # Стартовы шаблон для новых моў
├── scripts/               # Службовыя Python-скрыпты аўтаматызацыі
│   ├── generate_pdf.py    # Генератар медыцынскіх PDF-справаздач ReportLab
│   └── validate_locale.py # Скрыпт праверкі сінтаксісу і ключоў лакалей
├── src/                   # Зыходны код на чыстым Rust
│   ├── db.rs              # SQLx-запыты да PostgreSQL і міграцыі схемы БД
│   ├── handlers/          # Апрацоўшчыкі каманд, колбэкаў і дыялогаў
│   │   ├── calendar.rs    # Каляндарная сетка прыступаў і гісторыя
│   │   ├── commands.rs    # Сістэмныя каманды (/start, /menu, /help, /donate, /cancel)
│   │   ├── export.rs      # Экспарт даных у PDF і CSV
│   │   ├── followup.rs    # Кантроль сціхання болю і ацэнка лекаў
│   │   ├── headache.rs    # Пакрокавы FSM-апытальнік фіксацыі прыступу
│   │   ├── language.rs    # Змена мовы і персаны маскота
│   │   ├── mod.rs
│   │   └── reminder.rs    # Налады штодзённага чэк-іну і часавых паясоў
│   ├── keyboards.rs       # Генератары інлайн-клавіятур і навігацыі
│   ├── locales/
│   │   └── mod.rs         # Убудаванне JSON у бінарнік і функцыі get_text / get_text_fmt
│   ├── main.rs            # Точка ўваходу, Telegram Stars хэндлеры, пул БД і дыспетчар
│   ├── models.rs          # Даменныя структуры даных і серыялізацыя
│   ├── rich.rs            # Генератар Rich-паведамленняў TG-13 з убудаванымі кнопкамі
│   ├── services/
│   │   ├── export.rs      # Фарміраванне выгрузак CSV і выклік генератара PDF
│   │   ├── mod.rs
│   │   └── schedulers.rs  # Фанавыя Tokio-варкеры для апытанняў і follow-up
│   └── session.rs         # Персістэнтнае сховішча FSM (Redis + Memory fallback)
├── Cargo.toml             # Маніфест залежнасцей і метаданыя Rust
├── Cargo.lock             # Зафіксаваныя версіі бібліятэк (lockfile)
├── Dockerfile             # Multi-stage Dockerfile
├── Dockerfile.prebuilt    # Dockerfile для хуткага разгортвання гатовага бінарніка
├── docker-compose.yml     # Compose-канфігурацыя для сэрвісу, PostgreSQL і Redis
├── install.sh             # Інтэрактыўны bash-усталёўшчык у 1 клік
├── LICENSE                # Ліцэнзія MIT
├── README.md              # Дакументацыя (Русский)
├── README_be.md           # Дакументацыя (Беларуская)
└── README_en.md           # Documentation (English)
```

---

## ⚙️ Хуткі старт

### 🦊 Аўтаматычная ўсталёўка ў 1 клік (Рэкамендуецца)
Вы можаце запусціць інтэрактыўны ўсталёўшчык з прыгожым кансольным інтэрфейсам:

```bash
git clone https://github.com/xanax01d/kitsumed.git
cd kitsumed
./install.sh
```
Скрыпт аўтаматычна праверыць сістэму (АС, памяць, дыск), паставіць залежнасці і прапануе рэжым запуску:
- **`[1] 🐳 Docker Compose`** — Бот, PostgreSQL 16 і Redis 7 у ізаляваных кантэйнерах (з аўтагенерацыяй `.env`).
- **`[2] ⚡ Native Systemd`** — Зборка Rust-бінарніка і стварэнне сістэмнай службы Linux.
- **`[3] 📊 Праверыць статус`** — Дыягностыка працуючага бота і кантэйнераў.

Опцыі каманднага радка:
```bash
./install.sh --docker --token "ВАШ_ТОКЕН"   # Аўтаматычны запуск у Docker
./install.sh --systemd --token "ВАШ_ТОКЕН"  # Аўтаматычная зборка і запуск у Systemd
./install.sh --status                       # Праверка статусу
```

---

### Ручная ўсталёўка

#### 1. Кланаванне рэпазіторыя
```bash
git clone https://github.com/xanax01d/kitsumed.git
cd kitsumed
```

#### 2. Канфігурацыя (`.env`)
Стварыце файл `.env` у корані праекта:

```dotenv
# Токен бота Telegram
TELOXIDE_TOKEN="your_telegram_bot_token"

# База даных PostgreSQL
DATABASE_URL="postgres://kitsumed:your_password@127.0.0.1:5432/kitsumed"
# Альбо асобныя параметры:
# POSTGRES_HOST=127.0.0.1
# POSTGRES_PORT=5432
# POSTGRES_USER=kitsumed
# POSTGRES_PASSWORD=your_password
# POSTGRES_DB=kitsumed

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
./target/release/kitsumed
```

### 4. 🐳 Разгортванне ў Docker

Праект цалкам кантэйнерызаваны. У вобраз уключаны ўсе неабходныя кампаненты: лёгкаважны Rust-бінарнік, асяроддзе Python 3 з бібліятэкай ReportLab і шрыфты DejaVu для генерацыі клінічных PDF-справаздач.

#### Варыянт А: Запуск поўнага стэка праз Docker Compose (Рэкамендуецца)
Падымае ізаляваныя PostgreSQL 16, Redis 7 і KitsuMed Bot адной камандай:

```bash
# 1. Задайце токен вашага бота
export TOKEN="your_telegram_bot_token"

# 2. Запусціце ўсе сэрвісы ў фанавым рэжыме
docker compose up -d --build

# 3. Прагляд логаў бота ў рэальным часе
docker compose logs -f bot
```

Кіраванне кантэйнерамі:
```bash
docker compose ps          # Праверка статусу кантэйнераў
docker compose stop        # Спыненне сэрвісаў
docker compose down -v     # Поўнае спыненне з ачысткай тамоў БД
```

#### Варыянт Б: Зборка і запуск асобнага Docker-вобраза
Калі ў вас ужо працуюць PostgreSQL і Redis:

```bash
# Поўная зборка з зыходнікаў (multi-stage):
docker build -t kitsumed .

# Альбо хуткая зборка (калі бінарнік скампіляваны праз cargo build --release):
docker build -f Dockerfile.prebuilt -t kitsumed .

# Запуск кантэйнера:
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

## 🚀 Разгортванне на серверы (Systemd)

1. Збярыце рэлізны бінарнік у `/opt/kitsumed`:
   ```bash
   cd /opt/kitsumed
   cargo build --release
   ```

2. Стварыце канфігурацыю службы `/etc/systemd/system/kitsumed.service`:
   ```ini
   [Unit]
   Description=KitsuMed Rust Telegram Bot
   After=network.target postgresql.service redis-server.service
   Wants=postgresql.service redis-server.service

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

3. Перазапусціце сэрвіс:
   ```bash
   systemctl daemon-reload
   systemctl enable kitsumed.service
   systemctl restart kitsumed.service
   ```

---

## 📋 База даных

Схема табліц PostgreSQL аўтаматычна ініцыялізуецца і мігруе пры старце бота (`init_db` у [`src/db.rs`](file:///Users/zahariaklimkovich/Documents/projects/migrebot_analog/src/db.rs)):

### `users` — Профілі карыстальнікаў
Захоўвае налады раскладу напамінкаў, часавы пояс і выбраную мову інтэрфейсу.

| Калонка | Тып | Апісанне |
| :--- | :--- | :--- |
| `user_id` | `BIGINT PRIMARY KEY` | Унікальны Telegram ID карыстальніка |
| `username` | `VARCHAR(255)` | Юзернэйм у Telegram (`@username`) |
| `first_name` | `VARCHAR(255)` | Імя профілю ў Telegram |
| `reminder_time` | `VARCHAR(8) DEFAULT '21:00'` | Час штодзённага вячэрняга чэк-іну (`ГГ:ХХ`) |
| `reminder_enabled` | `BOOLEAN DEFAULT TRUE` | Статус актыўнасці штодзённага напамінку |
| `timezone` | `VARCHAR(64) DEFAULT 'Europe/Moscow'` | Часавы пояс карыстальніка (IANA, напр. `Europe/Minsk`, `Europe/Moscow`) |
| `last_reminded_date` | `VARCHAR(16) DEFAULT NULL` | Дата апошняй адпраўкі чэк-іну (`ГГГГ-ММ-ДД`) дзеля выключэння дубляў |
| `language` | `VARCHAR(16) DEFAULT 'ru'` | Выбраная персона/мова інтэрфейсу (`ru`, `be`, `en`, `meme`, `cyberpunk`) |
| `created_at` | `TIMESTAMPTZ DEFAULT NOW()` | Дата і час першай рэгістрацыі |

### `headache_episodes` — Запісы прыступаў галаўнога болю
Захоўвае поўную клінічную карціну эпізоду: лакалізацыю, моц болю, сімптомы, трыгеры, прынятыя прэпараты, дынаміку купіравання і ўмовы надвор'я.

| Калонка | Тып | Апісанне |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Унікальны ідэнтыфікатар эпізоду |
| `user_id` | `BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE` | Знешні ключ Telegram ID карыстальніка з каскадным выдаленнем |
| `start_time` | `VARCHAR(64) NOT NULL` | Дата і час пачатку прыступу |
| `end_time` | `VARCHAR(64)` | Дата і час заканчэння прыступу (для завершаных эпізодаў) |
| `intensity` | `INTEGER NOT NULL` | Інтэнсіўнасць болю па 10-бальнай шкале (1–10) |
| `location` | `VARCHAR(128) NOT NULL` | Лакалізацыя болю (скроні, лоб, патыліца, аднабаковы і г.д.) |
| `pain_type` | `VARCHAR(128) NOT NULL` | Характар болю (пульсуючы, сціскальны, распіральны, колючы і г.д.) |
| `symptoms` | `JSONB` | JSON-масіў спадарожных сімптомаў (`["nausea", "photophobia", ...]`) |
| `triggers` | `JSONB` | JSON-масіў правакацыйных фактараў (`["stress", "sleep_lack", ...]`) |
| `medication` | `TEXT` | Назва і дазіроўка прынятага прэпарата |
| `status` | `VARCHAR(32) DEFAULT 'active'` | Бягучы статус эпізоду: `active` (трывае) або `completed` (завершаны) |
| `medication_relief` | `VARCHAR(32) DEFAULT NULL` | Эфектыўнасць прэпарата паводле кантролю (`helped`, `partially`, `not_helped`) |
| `pain_resolved` | `BOOLEAN DEFAULT NULL` | Поўнае сціханне болю па выніках кантрольнага апытання (`true`/`false`) |
| `med_take_delay` | `VARCHAR(32) DEFAULT NULL` | Затрымка прыёму лекаў ад пачатку болю (`<30min`, `30-60min`, `1-2h`, `>2h`) |
| `relief_delay` | `VARCHAR(32) DEFAULT NULL` | Час да надыходу палёгкі (`<30min`, `30-60min`, `1-2h`, `>2h`) |
| `followup_due_at` | `TIMESTAMPTZ DEFAULT NULL` | Разліковы час адпраўкі кантрольнага чэк-іну эфектыўнасці (праз 2 гадзіны) |
| `followup_sent` | `BOOLEAN DEFAULT FALSE` | Сцяжок адпраўкі кантрольнага апытання эфектыўнасці |
| `pressure_hpa` | `REAL DEFAULT NULL` | Атмасферны ціск у гПа на момант прыступу (Open-Meteo) |
| `temperature_c` | `REAL DEFAULT NULL` | Тэмпература паветра ў °C на момант прыступу (Open-Meteo) |
| `is_quick_log` | `BOOLEAN DEFAULT FALSE` | Адзнака экспрэс-запісу ў адзін клік |
| `created_at` | `TIMESTAMPTZ DEFAULT NOW()` | Адзнака часу стварэння запісу ў БД |

### `user_medications` — Персанальны даведнік прэпаратаў
Аўтаматычна папаўняльны спіс лекаў карыстальніка для хуткага выбару на інлайн-клавіятуры.

| Калонка | Тып | Апісанне |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Унікальны ідэнтыфікатар запісу |
| `user_id` | `BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE` | Знешні ключ Telegram ID карыстальніка з каскадным выдаленнем |
| `name` | `VARCHAR(255) NOT NULL` | Гандлёвая ці міжнародная назва прэпарата |
| `last_used_at` | `TIMESTAMPTZ DEFAULT NOW()` | Адзнака часу апошняга ўжывання (для сартавання па актуальнасці) |

*Абмежаванне ўнікальнасці:* `UNIQUE(user_id, name)` — прадухіляе дубляванне назвы прэпарата ў аднаго карыстальніка.

### ⚡ Індэксы базы даных
- `idx_headache_episodes_user_status` — `ON headache_episodes(user_id, status)`: забяспечвае імгненную выбарку бягучых актыўных прыступаў карыстальніка і паскарае фонавыя варкеры follow-up.
- `idx_user_medications_user_id` — `ON user_medications(user_id, last_used_at DESC)`: аптымізуе хуткі рэндэрынг кнопак апошніх прынятых лекаў.

---

---

## 💖 Падтрымка праекта

KitsuMed — цалкам бясплатны, незалежны праект з адкрытым зыходным кодам. Калі бот дапамагае вам сачыць за мігрэнню і галаўным болем, вы можаце падтрымаць аплату сервераў і распрацоўку:

<p align="center">
  <a href="https://web.tribute.tg/d/TXJ">
    <img src="https://img.shields.io/badge/Падтрымаць_праз_Tribute-FF5B5B?style=for-the-badge&logo=telegram&logoColor=white" alt="Падтрымаць праз Tribute" />
  </a>
</p>

---

<div align="center">
  <sub>Pure Rust • Анімэ-стылістыка • Высокая прадукцыйнасць • Rich Telegram UI</sub>
</div>
