#!/bin/bash

# Development script for Enterprise Search Telegram Bot
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if service is running
check_service() {
    if pgrep -f "$1" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Parse command line arguments
case "${1:-run}" in
    "setup")
        print_status "Running setup script..."
        ./setup.sh
        ;;
    
    "install")
        print_status "Installing dependencies..."
        source venv/bin/activate
        pip install -r requirements.txt
        print_success "Dependencies installed"
        ;;
    
    "test")
        print_status "Running tests..."
        source venv/bin/activate
        pytest tests/ -v
        print_success "Tests completed"
        ;;
    
    "lint")
        print_status "Running linting..."
        source venv/bin/activate
        
        echo "Running black..."
        black --check src/ tests/ || black src/ tests/
        
        echo "Running isort..."
        isort --check-only src/ tests/ || isort src/ tests/
        
        echo "Running flake8..."
        flake8 src/ tests/
        
        print_success "Linting completed"
        ;;
    
    "format")
        print_status "Formatting code..."
        source venv/bin/activate
        black src/ tests/
        isort src/ tests/
        print_success "Code formatted"
        ;;
    
    "redis")
        print_status "Starting Redis..."
        if check_service "redis"; then
            print_warning "Redis is already running"
        else
            if command -v systemctl &> /dev/null; then
                sudo systemctl start redis
            elif command -v brew &> /dev/null; then
                brew services start redis
            else
                redis-server &
            fi
            sleep 2
            if check_service "redis"; then
                print_success "Redis started"
            else
                print_error "Failed to start Redis"
                exit 1
            fi
        fi
        ;;
    
    "ngrok")
        if ! command -v ngrok &> /dev/null; then
            print_error "ngrok not found. Please install it from https://ngrok.com/"
            exit 1
        fi
        
        print_status "Starting ngrok tunnel..."
        print_warning "Update TELEGRAM_WEBHOOK_URL in .env with the ngrok URL"
        ngrok http 8000
        ;;
    
    "webhook")
        print_status "Starting bot in webhook mode..."
        source venv/bin/activate
        export WEBHOOK_MODE=true
        python main.py
        ;;
    
    "polling")
        print_status "Starting bot in polling mode..."
        source venv/bin/activate
        export WEBHOOK_MODE=false
        python main.py
        ;;
    
    "run"|"start")
        print_status "Starting Enterprise Search Telegram Bot..."
        
        # Check if Redis is running
        if ! check_service "redis"; then
            print_warning "Redis not running, starting it..."
            $0 redis
        fi
        
        # Activate virtual environment
        if [ ! -f "venv/bin/activate" ]; then
            print_error "Virtual environment not found. Run: $0 setup"
            exit 1
        fi
        
        source venv/bin/activate
        
        # Check if .env exists
        if [ ! -f ".env" ]; then
            print_error ".env file not found. Run: $0 setup"
            exit 1
        fi
        
        # Start the bot
        python main.py
        ;;
    
    "docker")
        print_status "Building and running with Docker..."
        docker-compose up --build
        ;;
    
    "docker-dev")
        print_status "Running development environment with Docker..."
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
        ;;
    
    "logs")
        print_status "Showing application logs..."
        if [ -f "logs/bot.log" ]; then
            tail -f logs/bot.log
        else
            print_warning "No log file found"
        fi
        ;;
    
    "status")
        print_status "Checking service status..."
        
        # Check Redis
        if check_service "redis"; then
            print_success "Redis: Running"
        else
            print_error "Redis: Not running"
        fi
        
        # Check bot process
        if check_service "main.py"; then
            print_success "Bot: Running"
        else
            print_warning "Bot: Not running"
        fi
        
        # Check backend connection (if configured)
        if [ -f ".env" ]; then
            source .env
            if [ ! -z "$BACKEND_BASE_URL" ]; then
                if curl -s "$BACKEND_BASE_URL/health" > /dev/null 2>&1; then
                    print_success "Backend: Reachable"
                else
                    print_error "Backend: Not reachable"
                fi
            fi
        fi
        ;;
    
    "clean")
        print_status "Cleaning up..."
        
        # Stop services
        pkill -f "main.py" || true
        
        # Clean Python cache
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        
        # Clean test artifacts
        rm -rf .pytest_cache/ .coverage htmlcov/ 2>/dev/null || true
        
        print_success "Cleanup completed"
        ;;
    
    "help"|*)
        echo "Enterprise Search Telegram Bot Development Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup      - Initial project setup"
        echo "  install    - Install Python dependencies"
        echo "  test       - Run test suite"
        echo "  lint       - Run code linting"
        echo "  format     - Format code with black and isort"
        echo "  redis      - Start Redis server"
        echo "  ngrok      - Start ngrok tunnel for webhooks"
        echo "  webhook    - Start bot in webhook mode"
        echo "  polling    - Start bot in polling mode"
        echo "  run/start  - Start the bot (default)"
        echo "  docker     - Run with Docker Compose"
        echo "  docker-dev - Run development environment with Docker"
        echo "  logs       - Show application logs"
        echo "  status     - Check service status"
        echo "  clean      - Clean up temporary files"
        echo "  help       - Show this help message"
        echo ""
        ;;
esac
