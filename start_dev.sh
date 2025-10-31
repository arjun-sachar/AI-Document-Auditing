#!/bin/bash

# AI Document Auditing System - Development Startup Script
# This script starts both the backend and frontend servers for development

set -e

echo "🚀 Starting AI Document Auditing System Development Environment"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down development servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Check if Python dependencies are installed
echo -e "${BLUE}🔍 Checking Python dependencies...${NC}"
if ! python -c "import fastapi, spacy" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Python dependencies not found. Installing...${NC}"
    python install_dependencies.py
fi

# Check if frontend dependencies are installed
echo -e "${BLUE}🔍 Checking frontend dependencies...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not found. Installing...${NC}"
    cd frontend && npm install && cd ..
fi

# Start backend server
echo -e "${BLUE}🚀 Starting FastAPI backend server on port 8000...${NC}"
python backend_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start backend server${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend server started (PID: $BACKEND_PID)${NC}"

# Start frontend development server
echo -e "${BLUE}🚀 Starting Next.js frontend development server on port 3000...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Failed to start frontend server${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo -e "${GREEN}✅ Frontend server started (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${GREEN}🎉 Development environment is ready!${NC}"
echo "======================================"
echo -e "${BLUE}🌐 Frontend: http://localhost:3000${NC}"
echo -e "${BLUE}🔗 Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}📚 API Docs: http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"

# Wait for user to stop
wait