#!/bin/bash

echo "🔍 Verifying Bridge Implementation Setup"
echo "=========================================="
echo ""

errors=0
warnings=0

check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ $1 - MISSING"
        ((errors++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $1/"
    else
        echo "❌ $1/ - MISSING"
        ((errors++))
    fi
}

check_command() {
    if command -v $1 &> /dev/null; then
        echo "✅ $1 - $(command -v $1)"
    else
        echo "⚠️  $1 - Not found (optional)"
        ((warnings++))
    fi
}

echo "📂 Checking Directory Structure..."
check_dir "lib/bridge"
check_dir "config"
check_dir "test/bridge"
check_dir "test/support"
check_dir "scripts"
echo ""

echo "📄 Checking Core Files..."
check_file "mix.exs"
check_file "lib/bridge/application.ex"
check_file "lib/bridge/endpoint.ex"
check_file "lib/bridge/router.ex"
check_file "lib/bridge/socket.ex"
echo ""

echo "🔧 Checking Core Modules..."
check_file "lib/bridge/server_registry.ex"
check_file "lib/bridge/pairing_manager.ex"
check_file "lib/bridge/session_manager.ex"
check_file "lib/bridge/server_channel.ex"
check_file "lib/bridge/app_channel.ex"
echo ""

echo "⚙️  Checking Configuration..."
check_file "config/config.exs"
check_file "config/dev.exs"
check_file "config/prod.exs"
check_file "config/test.exs"
check_file "config/runtime.exs"
echo ""

echo "🐳 Checking Docker Files..."
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file "haproxy.cfg"
check_file ".dockerignore"
echo ""

echo "🧪 Checking Test Files..."
check_file "test/test_helper.exs"
check_file "test/bridge/server_registry_test.exs"
check_file "test/bridge/pairing_manager_test.exs"
check_file "test/bridge/session_manager_test.exs"
check_file "test/bridge/integration_test.exs"
check_file "test/bridge/websocket_test.exs"
check_file "test/support/test_client.ex"
check_file "test_docker.py"
check_file "requirements.txt"
echo ""

echo "📚 Checking Documentation..."
check_file "README.md"
check_file "QUICKSTART.md"
check_file "TESTING.md"
check_file "IMPLEMENTATION_STATUS.md"
echo ""

echo "🛠️  Checking Build Tools..."
check_file "Makefile"
check_file ".gitignore"
echo ""

echo "💻 Checking System Dependencies..."
check_command "elixir"
check_command "mix"
check_command "docker"
check_command "docker-compose"
check_command "python3"
check_command "make"
echo ""

echo "=========================================="
if [ $errors -eq 0 ]; then
    echo "✅ All required files present!"
    echo ""
    if [ $warnings -gt 0 ]; then
        echo "⚠️  $warnings optional dependencies missing"
        echo "   (Install for full functionality)"
    fi
    echo ""
    echo "🚀 Ready to run:"
    echo "   make deps      - Install dependencies"
    echo "   make compile   - Compile project"
    echo "   make test      - Run tests"
    echo "   make docker-up - Start cluster"
    echo ""
    exit 0
else
    echo "❌ $errors files missing!"
    echo ""
    echo "Please ensure all files are present before continuing."
    exit 1
fi
