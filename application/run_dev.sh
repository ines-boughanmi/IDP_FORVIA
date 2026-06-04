#!/bin/bash
# Quick Start Script for IDP Monitoring Django Application
# This script sets up and runs the Django development server

echo "========================================"
echo "IDP Monitoring - Django Application"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo ""

# Run migrations
echo "Applying database migrations..."
python manage.py migrate --noinput > /dev/null
echo ""

# Start development server
echo "========================================"
echo "Starting Django development server..."
echo "========================================"
echo ""
echo "Server will be available at: http://127.0.0.1:8000/"
echo "Admin panel available at: http://127.0.0.1:8000/admin/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py runserver
