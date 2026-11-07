# Multi-stage Dockerfile for KitsuMed
FROM rust:1.85-bookworm AS builder

WORKDIR /app
COPY Cargo.toml Cargo.lock* ./
# Cache dependency build
RUN mkdir src && echo "fn main() {}" > src/main.rs && cargo build --release && rm -rf src

COPY src ./src
COPY locales ./locales
COPY assets ./assets

RUN cargo build --release

# Runtime image
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl3 \
    python3 \
    python3-reportlab \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/kitsumed /app/kitsumed
COPY locales ./locales
COPY assets ./assets
COPY scripts ./scripts

# Symlink so scripts are discoverable both in /app/scripts and /opt/kitsumed/scripts
RUN mkdir -p /opt/kitsumed && ln -s /app/scripts /opt/kitsumed/scripts

ENV RUST_LOG=info

CMD ["/app/kitsumed"]
