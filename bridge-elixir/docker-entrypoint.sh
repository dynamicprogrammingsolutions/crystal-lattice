#!/bin/sh

set -e

if [ "$BRIDGE_NODE_NAME_MODE" = "private-ip" ]; then
    PRIVATE_IP="$(hostname -i | awk '{print $1}')"
    export NODE_NAME="bridge@$PRIVATE_IP"
    export BRIDGE_USE_LONG_NAME=1
fi

# If NODE_NAME is set, start in distributed mode
if [ -n "$NODE_NAME" ]; then
    echo "🚀 Starting Elixir in distributed mode as $NODE_NAME"
    export ELIXIR_ERL_OPTIONS="-proto_dist inet_tcp"
    if [ "$BRIDGE_USE_LONG_NAME" = "1" ] || echo "$NODE_NAME" | grep -q '@'; then
        exec elixir --name "$NODE_NAME" --cookie "$COOKIE" -S mix run --no-halt
    else
        exec elixir --sname "$NODE_NAME" --cookie "$COOKIE" -S mix run --no-halt
    fi
else
    echo "🚀 Starting Elixir in local mode"
    exec mix run --no-halt
fi
