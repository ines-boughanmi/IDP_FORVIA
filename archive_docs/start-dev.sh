#!/bin/bash
# IDP Analytics Platform - Development Start Script
# Run both backend and frontend servers with one command

echo "🚀 IDP Analytics Platform - Starting..."
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.8+"
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

echo "✅ Python found: $(python --version)"
echo "✅ Node found: $(node --version)"
echo ""

# Start backend
echo "📦 Starting Django backend..."
cd backend
python manage.py runserver &
BACKEND_PID=$!
cd ..
echo "✅ Backend running on http://localhost:8000 (PID: $BACKEND_PID)"
echo ""

# Start frontend
echo "⚛️  Starting React frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)"
echo ""

echo "🎉 Both services are running!"
echo ""
echo "📍 Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000/api"
echo "   Admin: http://localhost:8000/admin"
echo ""
echo "To stop: Press Ctrl+C or kill processes:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Wait for both processes
wait
