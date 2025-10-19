#!/bin/bash

# Test Monitoring Script
# Run this in a separate terminal while testing

echo "🔍 AI Financial Advisor - Test Monitor"
echo "======================================"
echo ""
echo "This will show:"
echo "  ✅ Successful operations"
echo "  ❌ Errors"
echo "  🔧 Tool calls"
echo "  📊 RAG searches"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "======================================"
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend not running!"
    echo "Start it with: cd backend && source venv/bin/activate && uvicorn main:app --reload"
    exit 1
fi

echo "✅ Backend is running"
echo ""
echo "📡 Live Monitoring (showing last 20 lines, updating in real-time):"
echo ""

# Monitor backend logs with color coding
tail -f /Users/vinaybadhan/Desktop/jump/backend/logs/*.log 2>/dev/null | grep --line-buffered -E "(INFO|ERROR|WARNING|Tool|RAG|Hubspot|Gmail|Calendar)" | while read line; do
    if [[ $line == *"ERROR"* ]]; then
        echo "❌ $line"
    elif [[ $line == *"Tool"* ]] || [[ $line == *"function"* ]]; then
        echo "🔧 $line"
    elif [[ $line == *"RAG"* ]] || [[ $line == *"search"* ]]; then
        echo "📊 $line"
    elif [[ $line == *"sync"* ]]; then
        echo "🔄 $line"
    elif [[ $line == *"INFO"* ]]; then
        echo "✅ $line"
    else
        echo "   $line"
    fi
done

