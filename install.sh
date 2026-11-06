#!/usr/bin/env bash
# ==============================================================================
# KitsuMed — Interactive Installer & Deployment Manager
# Supports: Docker Compose (Recommended) & Native Systemd Service
# ==============================================================================

set -eo pipefail

# --- Color Palette (Truecolor / 256 Colors fallback) ---
if [ -t 1 ]; then
    BOLD="\033[1m"
    DIM="\033[2m"
    ITALIC="\033[3m"
    UNDERLINE="\033[4m"
    RED="\033[38;5;196m"
    GREEN="\033[38;5;48m"
    YELLOW="\033[38;5;220m"
    BLUE="\033[38;5;39m"
    PURPLE="\033[38;5;141m"
    CYAN="\033[38;5;51m"
    ORANGE="\033[38;5;208m"
    WHITE="\033[38;5;255m"
    MUTED="\033[38;5;244m"
    RESET="\033[0m"
else
    BOLD="" DIM="" ITALIC="" UNDERLINE=""
    RED="" GREEN="" YELLOW="" BLUE="" PURPLE="" CYAN="" ORANGE="" WHITE="" MUTED="" RESET=""
fi

# --- Symbols ---
TICK="${GREEN}✔${RESET}"
CROSS="${RED}✖${RESET}"
INFO="${BLUE}ℹ${RESET}"
ARROW="${CYAN}➜${RESET}"
FOX="${ORANGE}🦊${RESET}"
GEAR="${PURPLE}⚙${RESET}"
LOCK="${YELLOW}🔒${RESET}"

# --- Logging Functions ---
log_info()    { echo -e "  ${INFO}  $*"; }
log_success() { echo -e "  ${TICK}  ${GREEN}$*${RESET}"; }
log_warn()    { echo -e "  ${YELLOW}⚠  $*${RESET}"; }
log_error()   { echo -e "  ${CROSS}  ${RED}${BOLD}$*${RESET}"; }
log_step()    { echo -e "\n${BOLD}${CYAN}▶  $*${RESET}"; }

# --- Spinner Animation ---
run_spinner() {
    local pid=$1
    local message="$2"
    local spinchars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local delay=0.08
    local i=0

    tput civis 2>/dev/null || true
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i+1) % 10 ))
        printf "\r  ${CYAN}%s${RESET}  %s" "${spinchars:$i:1}" "$message"
        sleep "$delay"
    done
    wait "$pid"
    local exit_code=$?
    tput cnorm 2>/dev/null || true

    if [ $exit_code -eq 0 ]; then
        printf "\r  ${TICK}  %s\n" "$message"
    else
        printf "\r  ${CROSS}  ${RED}%s (ошибка: код %d)${RESET}\n" "$message" "$exit_code"
        return $exit_code
    fi
}

# --- Banner ---
print_banner() {
    clear 2>/dev/null || true
    echo -e "${ORANGE}"
    cat << 'EOF'
   /\_/\      _  ___ _             __  __          _ 
  ( o.o )    | |/ (_) |_ ___ _   _|  \/  | ___  __| |
   > ^ <     | ' /| | __/ __| | | | |\/| |/ _ \/ _` |
  /  🦊 \    | . \| | || (__| |_| | |  | |  __/ (_| |
 /_/   \_    |_|\_\_|\__\___|\__,_|_|  |_|\___|\__,_|
EOF
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "  ${BOLD}${WHITE}KitsuMed Medical Diary${RESET} ${MUTED}•${RESET} ${CYAN}Установочный менеджер${RESET}"
    echo -e "  ${MUTED}Rust 1.85 • PostgreSQL 16 • Redis 7 • ReportLab Clinical PDF${RESET}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
}

# --- System Diagnostics ---
check_system_environment() {
    log_step "Диагностика системы и окружения"

    OS_TYPE="unknown"
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            # shellcheck source=/dev/null
            . /etc/os-release
            OS_TYPE="$ID"
            OS_PRETTY="$PRETTY_NAME"
        else
            OS_TYPE="linux"
            OS_PRETTY="Linux Generic"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS_TYPE="macos"
        OS_PRETTY="macOS $(sw_vers -productVersion 2>/dev/null || true)"
    fi

    log_info "ОС: ${BOLD}${OS_PRETTY:-$OS_TYPE}${RESET}"

    # RAM Check
    if command -v free >/dev/null 2>&1; then
        RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
        log_info "Оперативная память: ${RAM_MB} MB"
        if [ "$RAM_MB" -lt 512 ]; then
            log_warn "Мало оперативной памяти (<512MB). Рекомендуется включить swap-файл."
        fi
    fi

    # Disk Space Check
    if [[ "$OS_TYPE" == "macos" ]]; then
        FREE_DISK_GB=$(df -g . 2>/dev/null | awk 'NR==2 {print $4}' || echo "10")
    else
        FREE_DISK_GB=$(df -BG . 2>/dev/null | awk 'NR==2 {gsub("G","",$4); print $4}' || df -m . 2>/dev/null | awk 'NR==2 {print int($4/1024)}' || echo "10")
    fi
    log_info "Свободно на диске: ~${FREE_DISK_GB} GB"
    if [ "$FREE_DISK_GB" -lt 2 ] 2>/dev/null; then
        log_warn "Мало свободного места (<2GB). Сборка Rust или Docker может завершиться с ошибкой."
    fi
}

# --- Bot Token Prompt ---
prompt_token() {
    if [ -n "$CLI_TOKEN" ]; then
        BOT_TOKEN="$CLI_TOKEN"
        return 0
    fi

    # Check if .env already has TOKEN
    if [ -f .env ] && grep -q '^TOKEN=' .env 2>/dev/null; then
        EXISTING_TOKEN=$(grep '^TOKEN=' .env | cut -d '=' -f2- | tr -d '"'\'' ')
        if [[ "$EXISTING_TOKEN" =~ ^[0-9]+:[a-zA-Z0-9_-]+$ ]]; then
            echo -e "  ${LOCK}  Найден токен бота в файле .env: ${MUTED}${EXISTING_TOKEN:0:10}...${RESET}"
            read -r -p "     Использовать его? [Y/n]: " USE_EXISTING
            USE_EXISTING=${USE_EXISTING:-Y}
            if [[ "$USE_EXISTING" =~ ^[YyДд]$ ]]; then
                BOT_TOKEN="$EXISTING_TOKEN"
                return 0
            fi
        fi
    fi

    echo -e "\n  ${LOCK}  ${BOLD}Введите токен вашего Telegram-бота (от @BotFather):${RESET}"
    while true; do
        read -r -p "     TOKEN: " BOT_TOKEN
        BOT_TOKEN=$(echo "$BOT_TOKEN" | tr -d '[:space:]')
        if [[ "$BOT_TOKEN" =~ ^[0-9]+:[a-zA-Z0-9_-]+$ ]]; then
            log_success "Формат токена подтвержден."
            break
        else
            log_error "Неверный формат токена! Токен должен выглядеть как: 123456789:ABCDefgh..."
        fi
    done
}

# --- Write .env Configuration ---
setup_env_file() {
    local target_file=".env"
    log_step "Подготовка файла конфигурации (${target_file})"

    PG_PASS="${POSTGRES_PASSWORD:-$(openssl rand -hex 12 2>/dev/null || echo "kitsumed_secure_$(date +%s)")}"

    cat > "$target_file" << EOF
# ==============================================================================
# KitsuMed Production Environment Configuration
# Generated automatically by install.sh
# ==============================================================================

# Telegram Bot Token
TOKEN="${BOT_TOKEN}"
TELOXIDE_TOKEN="${BOT_TOKEN}"

# PostgreSQL Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=kitsumed
POSTGRES_PASSWORD=${PG_PASS}
POSTGRES_DB=kitsumed

# Redis Session Storage
REDIS_HOST=redis
REDIS_PORT=6379

# Logging level (error, warn, info, debug, trace)
RUST_LOG=info
EOF

    chmod 600 "$target_file"
    log_success "Файл ${target_file} успешно сгенерирован и защищен (chmod 600)."
}

# --- Deploy Mode 1: Docker Compose ---
deploy_docker() {
    log_step "Развертывание через Docker Compose"

    # Check Docker installation
    if ! command -v docker >/dev/null 2>&1; then
        log_warn "Docker не установлен."
        if [[ "$OS_TYPE" == "macos" ]]; then
            log_error "На macOS установите Docker Desktop: https://www.docker.com/products/docker-desktop"
            exit 1
        fi

        read -r -p "     Установить Docker автоматически официальным скриптом get.docker.com? [Y/n]: " INSTALL_DOCKER
        INSTALL_DOCKER=${INSTALL_DOCKER:-Y}
        if [[ "$INSTALL_DOCKER" =~ ^[YyДд]$ ]]; then
            log_info "Установка Docker..."
            curl -fsSL https://get.docker.com | sh
            systemctl enable --now docker 2>/dev/null || true
            log_success "Docker успешно установлен."
        else
            log_error "Невозможно продолжить без установленного Docker."
            exit 1
        fi
    fi

    # Verify Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_warn "Docker демон не запущен. Пытаюсь запустить службу..."
        sudo systemctl start docker 2>/dev/null || true
        sleep 2
        if ! docker info >/dev/null 2>&1; then
            log_error "Не удалось подключиться к демону Docker. Проверьте права (sudo usermod -aG docker $USER) или запуск сервиса."
            exit 1
        fi
    fi

    # Determine docker compose command
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        log_error "Команда docker compose / docker-compose не найдена."
        exit 1
    fi

    prompt_token
    setup_env_file

    log_info "Сборка контейнеров и запуск сервисов в фоне..."
    $DOCKER_COMPOSE_CMD up -d --build

    echo ""
    log_success "Стек KitsuMed успешно запущен!"
    echo -e "\n  ${BOLD}Текущее состояние контейнеров:${RESET}"
    $DOCKER_COMPOSE_CMD ps

    echo -e "\n  ${FOX}  ${BOLD}${GREEN}Бот KitsuMed готов к работе!${RESET}"
    echo -e "  ${MUTED}─────────────────────────────────────────────────────────────────${RESET}"
    echo -e "  ${ARROW} Просмотр логов бота:   ${CYAN}$DOCKER_COMPOSE_CMD logs -f bot${RESET}"
    echo -e "  ${ARROW} Перезапуск сервисов:  ${CYAN}$DOCKER_COMPOSE_CMD restart${RESET}"
    echo -e "  ${ARROW} Остановка сервисов:   ${CYAN}$DOCKER_COMPOSE_CMD stop${RESET}"
    echo -e "  ${MUTED}─────────────────────────────────────────────────────────────────${RESET}\n"
}

# --- Deploy Mode 2: Native Systemd Service ---
deploy_systemd() {
    log_step "Развертывание нативного Systemd-сервиса (Bare-metal)"

    if [[ "$OS_TYPE" == "macos" ]]; then
        log_error "Systemd доступен только на Linux! Для macOS используйте вариант Docker."
        exit 1
    fi

    if [ "$EUID" -ne 0 ]; then
        log_warn "Для настройки Systemd, PostgreSQL и пакетов требуются права sudo."
        SUDO="sudo"
    else
        SUDO=""
    fi

    prompt_token

    log_info "Установка системных зависимостей (PostgreSQL, Redis, Python3, ReportLab, DejaVu)..."
    if [ "$OS_TYPE" = "ubuntu" ] || [ "$OS_TYPE" = "debian" ]; then
        $SUDO apt-get update -qq
        $SUDO apt-get install -y -qq \
            curl \
            build-essential \
            pkg-config \
            libssl-dev \
            postgresql \
            postgresql-contrib \
            redis-server \
            python3 \
            python3-reportlab \
            fonts-dejavu-core \
            fonts-dejavu-extra
    else
        log_warn "Дистрибутив не Debian/Ubuntu. Убедитесь, что установлены PostgreSQL, Redis, Rust и ReportLab."
    fi

    # Check/Install Rust
    if ! command -v cargo >/dev/null 2>&1; then
        log_info "Rust не обнаружен. Установка Rust через rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        # shellcheck source=/dev/null
        source "$HOME/.cargo/env"
    fi

    log_info "Настройка локального PostgreSQL..."
    $SUDO systemctl enable --now postgresql redis-server 2>/dev/null || true

    # Create user & database in Postgres if not exists
    $SUDO -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = 'kitsumed'" | grep -q 1 || \
        $SUDO -u postgres psql -c "CREATE USER kitsumed WITH PASSWORD 'kitsumed_secure_pass';"
    $SUDO -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'kitsumed'" | grep -q 1 || \
        $SUDO -u postgres psql -c "CREATE DATABASE kitsumed OWNER kitsumed;"
    $SUDO -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kitsumed TO kitsumed;" 2>/dev/null || true

    log_info "Сборка оптимизированного релизного бинарника Rust (cargo build --release)..."
    cargo build --release

    APP_DIR=$(pwd)
    BINARY_PATH="${APP_DIR}/target/release/kitsumed"

    log_info "Создание файла systemd-службы /etc/systemd/system/kitsumed.service..."
    $SUDO bash -c "cat > /etc/systemd/system/kitsumed.service" << EOF
[Unit]
Description=KitsuMed Rust Telegram Bot
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=simple
User=${USER}
WorkingDirectory=${APP_DIR}
Environment="TELOXIDE_TOKEN=${BOT_TOKEN}"
Environment="TOKEN=${BOT_TOKEN}"
Environment="DATABASE_URL=postgresql://kitsumed:kitsumed_secure_pass@127.0.0.1:5432/kitsumed"
Environment="REDIS_URL=redis://127.0.0.1:6379"
Environment="RUST_LOG=info"
ExecStart=${BINARY_PATH}
Restart=always
RestartSec=3
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF

    $SUDO systemctl daemon-reload
    $SUDO systemctl enable --now kitsumed
    sleep 2

    if systemctl is-active --quiet kitsumed; then
        log_success "Служба kitsumed успешно запущена и добавлена в автозагрузку!"
    else
        log_error "Служба не смогла запуститься. Проверьте: journalctl -u kitsumed -n 30"
        exit 1
    fi

    echo -e "\n  ${FOX}  ${BOLD}${GREEN}Бот KitsuMed готов к работе!${RESET}"
    echo -e "  ${MUTED}─────────────────────────────────────────────────────────────────${RESET}"
    echo -e "  ${ARROW} Просмотр логов:       ${CYAN}journalctl -u kitsumed -f${RESET}"
    echo -e "  ${ARROW} Статус службы:        ${CYAN}systemctl status kitsumed${RESET}"
    echo -e "  ${ARROW} Перезапуск бота:      ${CYAN}systemctl restart kitsumed${RESET}"
    echo -e "  ${MUTED}─────────────────────────────────────────────────────────────────${RESET}\n"
}

# --- Service Diagnostics & Status ---
show_status() {
    log_step "Проверка статуса компонентов"

    echo -e "  ${BOLD}1. Docker статус:${RESET}"
    if command -v docker >/dev/null 2>&1; then
        if docker compose ps 2>/dev/null; then
            :
        elif docker-compose ps 2>/dev/null; then
            :
        else
            echo -e "     ${MUTED}Контейнеры не запущены в текущей директории.${RESET}"
        fi
    else
        echo -e "     ${MUTED}Docker не установлен.${RESET}"
    fi

    echo -e "\n  ${BOLD}2. Systemd статус:${RESET}"
    if command -v systemctl >/dev/null 2>&1; then
        if systemctl list-unit-files | grep -q kitsumed.service 2>/dev/null; then
            systemctl status kitsumed --no-pager || true
        else
            echo -e "     ${MUTED}Служба kitsumed.service не найдена.${RESET}"
        fi
    else
        echo -e "     ${MUTED}Systemctl недоступен (не Linux или нет systemd).${RESET}"
    fi
}

# --- Parse Arguments ---
CLI_MODE=""
CLI_TOKEN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --docker)
            CLI_MODE="docker"
            shift
            ;;
        --systemd)
            CLI_MODE="systemd"
            shift
            ;;
        --status)
            CLI_MODE="status"
            shift
            ;;
        --token)
            CLI_TOKEN="$2"
            shift 2
            ;;
        -h|--help)
            print_banner
            echo -e "Использование: $0 [ОПЦИИ]\n"
            echo -e "Опции:"
            echo -e "  --docker          Развертывание полного стека через Docker Compose (Рекомендуется)"
            echo -e "  --systemd         Установка нативного Systemd-сервиса (Bare-metal Linux)"
            echo -e "  --status          Показать текущий статус сервисов и контейнеров"
            echo -e "  --token <TOKEN>   Указать Telegram Bot Token через командную строку"
            echo -e "  -h, --help        Показать данную справку\n"
            exit 0
            ;;
        *)
            log_error "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
done

# --- Main Entry Point ---
print_banner
check_system_environment

if [ -n "$CLI_MODE" ]; then
    case "$CLI_MODE" in
        docker)  deploy_docker ;;
        systemd) deploy_systemd ;;
        status)  show_status ;;
    esac
    exit 0
fi

# Interactive Menu
echo -e "\n${BOLD}Выберите способ установки / действие:${RESET}"
echo -e "  ${CYAN}[1]${RESET} 🐳 ${BOLD}Docker Compose${RESET} ${GREEN}(Рекомендуется)${RESET} — Бот, PostgreSQL и Redis в изолированных контейнерах"
echo -e "  ${CYAN}[2]${RESET} ⚡ ${BOLD}Native Systemd${RESET} — Прямая компиляция Rust и запуск как службы Linux"
echo -e "  ${CYAN}[3]${RESET} 📊 ${BOLD}Проверить статус${RESET} — Диагностика работающих контейнеров или службы"
echo -e "  ${CYAN}[0]${RESET} 🚪 Выход\n"

read -r -p "  Ваш выбор [1-3, default: 1]: " MENU_CHOICE
MENU_CHOICE=${MENU_CHOICE:-1}

case "$MENU_CHOICE" in
    1) deploy_docker ;;
    2) deploy_systemd ;;
    3) show_status ;;
    0) echo -e "\n  ${FOX} До свидания!\n"; exit 0 ;;
    *) log_error "Неверный выбор!"; exit 1 ;;
esac
