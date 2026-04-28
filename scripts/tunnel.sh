#!/bin/bash
# SSH tunnel to VPS: SOCKS5 proxy (browser) + local forward (poly-router API)
# Usage: ./tunnel.sh start | stop | status

VPS_IP="45.125.64.244"
VPS_PORT="56777"
VPS_USER="kerothebot"
SOCKS_PORT=1080
API_PORT=8080

PID_FILE="/tmp/polyrouter-tunnel.pid"

start() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Tunnel already running (PID $(cat "$PID_FILE"))"
        return
    fi

    echo "Starting tunnel to $VPS_IP:$VPS_PORT (user: $VPS_USER)..."
    ssh -D "$SOCKS_PORT" -L "$API_PORT:localhost:$API_PORT" -p "$VPS_PORT" -N -f "$VPS_USER@$VPS_IP"

    sleep 1
    PID=$(pgrep -f "ssh -D $SOCKS_PORT -L $API_PORT:localhost:$API_PORT -p $VPS_PORT -N")

    if [ -n "$PID" ]; then
        echo "$PID" > "$PID_FILE"
        echo "Tunnel active (PID $PID)"
        echo ""
        echo "Forwards:"
        echo "  SOCKS5 proxy:    127.0.0.1:$SOCKS_PORT (browser routing)"
        echo "  poly-router API: 127.0.0.1:$API_PORT -> VPS:$API_PORT"
        echo ""
        echo "Run './tunnel.sh stop' when done."
    else
        echo "Failed to start tunnel."
        exit 1
    fi
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill "$PID" 2>/dev/null; then
            echo "Tunnel stopped (PID $PID)"
        else
            echo "Process $PID not found, cleaning up."
        fi
        rm -f "$PID_FILE"
    else
        echo "No tunnel running."
    fi
}

status() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "Tunnel running (PID $(cat "$PID_FILE")) — SOCKS:$SOCKS_PORT, API:$API_PORT"
    else
        echo "Tunnel not running."
        rm -f "$PID_FILE" 2>/dev/null
    fi
}

case "${1:-}" in
    start)  start ;;
    stop)   stop ;;
    status) status ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac
