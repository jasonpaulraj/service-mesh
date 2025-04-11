#!/bin/bash

# Check if venv directory exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
source venv/Scripts/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -e .
else
    echo "Dependencies already installed"
fi

# Start the FastAPI server
echo "Starting FastAPI server..."
uvicorn app.main:app --reload --port 6001