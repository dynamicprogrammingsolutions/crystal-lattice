FROM elixir:1.15-alpine AS builder

RUN apk add --no-cache build-base git

WORKDIR /app

ENV MIX_ENV=prod

RUN mix local.hex --force && \
    mix local.rebar --force

COPY mix.exs mix.lock ./
RUN mix deps.get --only prod

COPY config ./config
COPY lib ./lib

RUN mix deps.compile && \
    mix compile && \
    mix release

FROM alpine:3.20

RUN apk add --no-cache bash libstdc++ ncurses-libs openssl docker-cli openssh-client ca-certificates

WORKDIR /app

ENV MIX_ENV=prod
ENV PORT=4100

COPY --from=builder /app/_build/prod/rel/cloud_orchestrator ./
COPY docker-entrypoint.sh /usr/local/bin/cloud-orchestrator-entrypoint
RUN chmod +x /usr/local/bin/cloud-orchestrator-entrypoint

EXPOSE 4100

ENTRYPOINT ["cloud-orchestrator-entrypoint"]