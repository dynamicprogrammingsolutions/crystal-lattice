FROM elixir:1.15-alpine AS builder

RUN apk add --no-cache build-base git

WORKDIR /app

ENV MIX_ENV=prod

RUN mix local.hex --force && \
    mix local.rebar --force

COPY mix.exs mix.lock ./
RUN mix deps.get

COPY config ./config
COPY lib ./lib

RUN mix deps.compile && \
    mix compile

FROM elixir:1.15-alpine

RUN apk add --no-cache openssl ncurses-libs libstdc++ build-base git bash

WORKDIR /app

ENV MIX_ENV=prod
ENV PORT=4000

RUN mix local.hex --force && \
    mix local.rebar --force

COPY --from=builder /app/_build/prod /app/_build/prod
COPY --from=builder /app/deps /app/deps
COPY --from=builder /app/config /app/config
COPY --from=builder /app/lib /app/lib
COPY --from=builder /app/mix.exs /app/mix.lock ./

COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 4000 4369 9100-9155

ENTRYPOINT ["docker-entrypoint.sh"]
