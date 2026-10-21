<div align="center">

<img src="assets/images/readme/ru_kitsune.png" alt="KitsuMed Banner" width="100%" style="border-radius: 14px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); margin-bottom: 16px;" />

# 🦊 KitsuMed (Rust Edition)
### Высокопроизводительный Telegram-дневник приступов мигрени и головной боли на чистом Rust

[![Rust](https://img.shields.io/badge/Rust-1.85%2B-DEA584?style=for-the-badge&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![teloxide](https://img.shields.io/badge/teloxide-0.13-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://teloxide.rs/)
[![tokio](https://img.shields.io/badge/tokio-async-blue?style=for-the-badge&logo=rust&logoColor=white)](https://tokio.rs/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-FSM%20Sessions-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![sqlx](https://img.shields.io/badge/sqlx-0.8-green?style=for-the-badge)](https://github.com/launchbadge/sqlx)
[![i18n](https://img.shields.io/badge/Languages-5%20Locales-9cf?style=for-the-badge&logo=google-translate&logoColor=white)](#4-🌐-локализация-и-мультиязычность-5-языков)
[![Follow-up](https://img.shields.io/badge/Follow--up-Automated%20Check-blueviolet?style=for-the-badge&logo=clockify&logoColor=white)](#3-🩺-автоматический-follow-up-и-оценка-препаратов)
[![Rich Messages](https://img.shields.io/badge/Telegram-Rich%20Components%20TG--13-informational?style=for-the-badge&logo=telegram&logoColor=white)](https://telegram.org/)
[![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](LICENSE)

<p align="center">
  🇷🇺 <b>Русский</b> &nbsp;•&nbsp; <a href="README_be.md"><b>🇧🇾 Беларуская</b></a> &nbsp;•&nbsp; <a href="README_en.md"><b>🇬🇧 English</b></a>
</p>

<p align="center">
  <b>Умный бот для структурированной фиксации симптомов, характера и интенсивности боли,<br>
  интерактивного интерфейса с кнопками внутри сообщений (Telegram Rich Text), автоматического контроля купирования приступа и выгрузки отчетов.</b>
</p>

<p align="center">
  <a href="#-основные-возможности">✨ Возможности</a> •
  <a href="#-архитектура-системы">📐 Архитектура</a> •
  <a href="#-галерея-персонажей">🌸 Персонажи</a> •
  <a href="#-команды-и-навигация">⌨️ Навигация</a> •
  <a href="#-стек-технологий">🛠 Стек</a> •
  <a href="#-структура-проекта">📂 Структура</a> •
  <a href="#-быстрый-старт">⚙️ Быстрый старт</a> •
  <a href="#-развертывание-на-сервере-systemd">🚀 Деплой</a> •
  <a href="#-база-данных">📋 База данных</a>
</p>

</div>

---

## 📐 Архитектура системы

Полностью асинхронная отказоустойчивая архитектура на базе чистого **Rust** (компилируемый бинарник с нулевым оверхедом), многопоточного рантайма **Tokio**, пула соединений **SQLx**, распределенного **Redis** для FSM-сессий и СУБД **PostgreSQL**:

| Компонент | Технология | Назначение |
| :--- | :--- | :--- |
| **Telegram Client & Rich UI** | Telegram Bot API 8+ (Rich Messages TG-13) | Интерактивные inline-кнопки прямо внутри текста сообщений (`<tg-button-row>`, `<tg-button>`), спойлеры и сворачиваемые блоки (`<blockquote expandable>`), встроенные медиа |
| **Core Engine** | `teloxide 0.13` + `tokio` (Rust) | Высокопроизводительный асинхронный роутинг сообщений и коллбэков, надежная обработка потоков апдейтов |
| **Session Cache (Redis)** | `redis 0.27` (`tokio-comp`) | Персистентное хранение незавершенных опросов и состояний FSM по ключу `kitsumed:session:{user_id}` с TTL 7200 сек (2 часа) |
| **Primary Database** | `PostgreSQL 14+` (`sqlx 0.8`) | Пул асинхронных соединений `sqlx::PgPool`, строгая типизация, миграции схемы, история приступов (JSONB) и профили пользователей |
| **Follow-up Scheduler** | Tokio Background Task | Фоновый воркер контроля стихания боли через 2 часа после начала приступа и сбора оценки эффективности медикаментов |
| **Reminder Scheduler** | Tokio Background Task | Фоновый планировщик ежедневных чек-инов с учетом индивидуальных часовых поясов пользователей (Chrono + Chrono-Tz) |
| **Localization Engine** | Compile-time embedded JSON | Молниеносная локализация на 5 языков через `include_str!` и `LazyLock<HashMap>` без дискового I/O в рантайме |

---

## 🌸 Галерея лисичек (Аниме-маскоты 5 локализаций)

Каждая локализация сопровождается уникальной иллюстрацией маскота-лисички:

| 🇧🇾 Беларуская (`be`) | 🇷🇺 Русский (`ru`) | 🇬🇧 English (`en`) |
| :---: | :---: | :---: |
| <img src="assets/images/readme/be_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/ru_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/en_kitsune.png" width="100%" style="border-radius: 8px;" /> |
| **Лисичка в вышиванке с васильками** | **Лисичка-невролог в клинике** | **British Scholar Kitsune** |

| 🎭 Мемный (`meme`) | 🦾 Cyberpunk 2077 (`cyberpunk`) |
| :---: | :---: |
| <img src="assets/images/readme/meme_kitsune.png" width="100%" style="border-radius: 8px;" /> | <img src="assets/images/readme/cyberpunk_kitsune.png" width="100%" style="border-radius: 8px;" /> |
| **Вайбовая мемная атмосфера** | **Неоновый нетраннер & Хром** |

---

## 🌟 Основные возможности

### 1. ⏱ Пошаговый опросник с Rich Text интерфейсом
- **Кнопки внутри текста (Telegram TG-13)**: Кнопки навигации, шкалы боли и выбора симптомов встроены прямо в тело сообщения через теги `<tg-button-row>` и `<tg-button>`.
- **Время начала**: Быстрые пресеты (*Прямо сейчас, 30 минут назад, 1 час, 2 часа назад*) или точное время.
- **Шкала боли (1–10)**: Интуитивная градация от едва ощутимой (1) до невыносимой (10 🔥).
- **Локализация цефалгии**: Слева, справа, с обеих сторон, лоб/виски, затылок, диффузная боль.
- **Характер боли**: Пульсирующая, давящая, колющая, тупая.
- **Мультиселект симптомов**: Интерактивные кнопки с динамическим переключением ✅ в реальном времени (тошнота, рвота, светобоязнь, звукобоязнь, аура, головокружение).
- **Сбор триггеров**: Мультивыбор ключевых триггеров (стресс, недосып, погода, усталость, алкоголь, пропуск еды).
- **Медикаменты и дозировка**: Выбор конкретного препарата, указание задержки приема и оценка купирования.

### 2. 🩺 Автоматический follow-up и оценка препаратов
- **Контроль через 2 часа**: Фоновый таймер Tokio автоматически находит открытые приступы и отправляет запрос: *«Прошла ли головная боль?»*.
- **Фиксация времени стихания**: Быстрые кнопки ответа (*только что, 30 минут назад, 1 час назад, 2 часа назад*).
- **Оценка эффективности**: Фиксация клинического действия лекарств:
  - `🟢 Помогло` (`helped`)
  - `🟡 Частично` (`partially`)
  - `🔴 Не помогло` (`not_helped`)

### 3. 🌐 Локализация и мультиязычность (5 языков)
- 🇷🇺 **Русский (`ru`)**: Классическая академическая медицинская терминология.
- 🇧🇾 **Беларуская (`be`)**: Аўтэнтычная беларуская мова з нацыянальнай атрыбутыкай.
- 🇬🇧 **English (`en`)**: Международная терминология (ICHD-3).
- 🎭 **Мемный сленг (`meme`)**: Вирусный рунетовский сленг.
- 🦾 **Cyberpunk 2077 (`cyberpunk`)**: Стилистика неонового нетраннера, нейроглитчи, протоколы Trauma Team и устойчивость хрома.

### 4. 📅 Интерактивный календарь приступов (`/history` / `/calendar`)
- Месячная сетка с индикацией дней боли (🔴) и бессимптомных дней (🟢).
- Навигация по месяцам вперед/назад и подробные карточки дней с полной клинической информацией.

### 5. ⏰ Ежедневные персонализированные чек-ины
- Регулярный опрос в установленное пользователем время (*«Болела ли голова сегодня?»*).
- Полная поддержка часовых поясов (IANA и смещения UTC).

### 6. 📊 Клинический экспорт отчёта для невролога (`/export`)
- Формирование структурированных выгрузок истории эпизодов, триггеров и эффективности медикаментов.

---

## ⌨️ Команды и навигация

| Команда | Назначение |
| :--- | :--- |
| `/start` | Приветствие, регистрация в БД и открытие главного Rich-меню |
| `/menu` | Главное интерактивное меню с кнопками |
| `/log`, `/headache` | Запуск пошагового опросника фиксации приступа боли |
| `/status` | Проверка активного приступа и статуса купирования |
| `/calendar`, `/history` | Интерактивный календарь приступов по дням |
| `/reminder`, `/settings` | Меню настройки ежедневного чек-ина и часового пояса |
| `/language` | Выбор языка интерфейса (RU, BE, EN, Meme, Cyberpunk) |
| `/help` | Справочная информация по шкале боли и ведению дневника |
| `/cancel` | Прерывание текущего сценария и возврат в главное меню |

---

## 🛠 Стек технологий

- **Ядро**: Rust 1.85+ (Edition 2021)
- **Фреймворк Telegram**: `teloxide 0.13`
- **Асинхронный рантайм**: `tokio 1.x` (многопоточный планировщик)
- **База данных**: `PostgreSQL 14+` + пул соединений `sqlx 0.8` (асинхронный Postgres-драйвер)
- **Кэш сессий и FSM**: `Redis 7+` (`redis 0.27` с `tokio-comp`) — персистентное асинхронное хранение состояний опросов по ключу `kitsumed:session:{user_id}` с TTL 7200 сек и fallback на in-memory
- **Время и таймзоны**: `chrono` + `chrono-tz`
- **Сериализация**: `serde`, `serde_json`
- **Локализация**: compile-time `include_str!` с быстрой адресацией в памяти
- **Форматирование UI**: Telegram Rich Text (HTML-модель с кастомными тегами `<tg-button-row>`, `<tg-button>`, `<blockquote expandable>`)
- **Менеджер процессов**: `systemd`

---

## 📂 Структура проекта

```text
kitsumed/
├── assets/
│   └── images/            # Локализованные баннеры персонажей и визуальные схемы
│       ├── ru/            # Русский баннер, шаги опросника и скриншоты UI
│       ├── be/            # Беларускі банер (лісічка ў вышыванцы з вянком)
│       ├── en/            # English banner, questionnaire steps & UI screens
│       ├── meme/          # Мемный баннер
│       └── cyberpunk/     # Cyberpunk баннер
├── locales/               # Чистые JSON-словари локализации
│   ├── ru.json
│   ├── be.json
│   ├── en.json
│   ├── meme.json
│   └── cyberpunk.json
├── src/                   # Исходный код на чистом Rust
│   ├── db.rs              # SQLx-запросы к PostgreSQL и инициализация таблиц
│   ├── handlers/          # Обработчики команд, коллбэков и сценариев
│   │   ├── calendar.rs    # Календарная сетка и история
│   │   ├── commands.rs    # Системные команды (/start, /menu, /help, /cancel)
│   │   ├── export.rs      # Экспорт данных
│   │   ├── followup.rs    # Контроль стихания боли и оценка лекарств
│   │   ├── headache.rs    # Пошаговый FSM-опросник приступа
│   │   ├── language.rs    # Смена языка
│   │   ├── mod.rs
│   │   └── reminder.rs    # Настройки чек-ина и часовых поясов
│   ├── keyboards.rs       # Генераторы инлайн-клавиатур
│   ├── locales/
│   │   └── mod.rs         # Встраивание JSON в бинарник и функции get_text / get_text_fmt
│   ├── main.rs            # Точка входа, инициализация пула БД, Redis и диспетчера Teloxide
│   ├── models.rs          # Доменные структуры данных
│   ├── rich.rs            # Генератор Rich-сообщений TG-13 с встроенными кнопками
│   ├── services/
│   │   ├── export.rs      # Формирование выгрузок
│   │   ├── mod.rs
│   │   └── schedulers.rs  # Фоновые Tokio-воркеры для чек-инов и follow-up
│   └── session.rs         # Персистентное хранилище FSM-сессий (Redis + In-memory fallback)
├── Cargo.toml             # Манифест зависимостей Rust
├── Cargo.lock             # Зафиксированные версии библиотек
├── Dockerfile             # Multi-stage Dockerfile для легковесного контейнера
├── docker-compose.yml     # Compose-конфигурация для сервиса, PostgreSQL и Redis
└── README.md              # Документация проекта
```

---

## ⚙️ Быстрый старт

### 1. Клонирование репозитория
```bash
git clone https://github.com/xanax01d/kitsumed.git
cd kitsumed
```

### 2. Конфигурация (`.env`)
Создайте файл `.env` в корне проекта:

```dotenv
# Telegram Bot Token
TELOXIDE_TOKEN="your_telegram_bot_token"

# База данных PostgreSQL
DATABASE_URL="postgres://kitsumed:your_password@127.0.0.1:5432/kitsumed"
# Либо раздельные параметры подключения к PostgreSQL:
# POSTGRES_HOST=127.0.0.1
# POSTGRES_PORT=5432
# POSTGRES_USER=kitsumed
# POSTGRES_PASSWORD=your_password
# POSTGRES_DB=kitsumed

# Кэш сессий Redis FSM
REDIS_URL="redis://127.0.0.1:6379"
# Либо раздельные параметры подключения к Redis:
# REDIS_HOST=127.0.0.1
# REDIS_PORT=6379
# REDIS_PASSWORD=""

# Логирование
RUST_LOG="info"
```

### 3. Сборка и запуск
```bash
# Проверка компиляции
cargo check

# Запуск в dev-режиме
cargo run

# Сборка оптимизированного релизного бинарника
cargo build --release
./target/release/kitsumed
```

### 4. Запуск через Docker Compose (PostgreSQL + Redis + Bot)
```bash
docker-compose up -d
```

---

## 🚀 Развертывание на сервере (Systemd)

1. Установите релизный бинарник в `/opt/kitsumed`:
   ```bash
   cd /opt/kitsumed
   cargo build --release
   ```

2. Создайте файл службы `/etc/systemd/system/kitsumed.service`:
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

3. Запустите сервис:
   ```bash
   systemctl daemon-reload
   systemctl enable kitsumed.service
   systemctl restart kitsumed.service
   ```

4. Просмотр логов:
   ```bash
   journalctl -u kitsumed.service -f
   ```

---

## 📋 База данных

Схема таблиц PostgreSQL автоматически инициализируется при запуске бота:

### `users`
| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `user_id` | `BIGINT PRIMARY KEY` | ID пользователя Telegram |
| `username` | `VARCHAR(255)` | Никнейм (@username) |
| `first_name` | `VARCHAR(255)` | Имя профиля |
| `language` | `VARCHAR(16) DEFAULT 'ru'` | Выбранный язык (`ru`, `be`, `en`, `meme`, `cyberpunk`) |
| `reminder_time` | `VARCHAR(8)` | Время ежедневного опроса (`21:00`) |
| `reminder_enabled` | `BOOLEAN` | Включен ли опрос |
| `timezone` | `VARCHAR(64)` | Часовой пояс пользователя (`Europe/Minsk`, `Europe/Moscow` и т.д.) |
| `last_reminded_date` | `VARCHAR(16)` | Дата последней отправки чек-ина |
| `created_at` | `TIMESTAMPTZ` | Дата регистрации |

### `headache_episodes`
| Колонка | Тип | Описание |
| :--- | :--- | :--- |
| `id` | `SERIAL PRIMARY KEY` | Номер приступа |
| `user_id` | `BIGINT REFERENCES users` | ID пользователя |
| `start_time` | `VARCHAR(64)` | Время начала |
| `end_time` | `VARCHAR(64)` | Время окончания |
| `intensity` | `SMALLINT` | Сила боли (1-10) |
| `location` | `VARCHAR(64)` | Локализация |
| `pain_type` | `VARCHAR(64)` | Характер боли |
| `symptoms` | `JSONB` | Массив сопутствующих симптомов |
| `triggers` | `JSONB` | Массив провоцирующих факторов |
| `medication` | `VARCHAR(255)` | Принятый препарат |
| `status` | `VARCHAR(32)` | `active` или `completed` |
| `medication_relief` | `VARCHAR(32)` | Оценка действия препарата (`helped`, `partially`, `not_helped`) |
| `pain_resolved` | `BOOLEAN` | Стихание боли по результатам follow-up |
| `followup_sent` | `BOOLEAN DEFAULT false` | Отметка отправки двухчасового контроля |
| `created_at` | `TIMESTAMPTZ` | Время фиксации записи |

---

<div align="center">
  <sub>Pure Rust • Высокая производительность • Интерактивный Rich UI</sub>
</div>
