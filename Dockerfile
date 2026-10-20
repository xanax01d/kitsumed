# Multi-stage Dockerfile for KitsuMed Rust
FROM rust:1.85-bookworm AS builder

WORKDIR /app
COPY Cargo.toml Cargo.lock* ./
# Cache dependencies
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
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/kitsumed /app/kitsumed
COPY --from=builder /app/locales /app/locales
COPY --from=builder /app/assets /app/assets

ENV RUST_LOG=info

CMD ["/app/kitsumed"]
