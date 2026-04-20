#!/usr/bin/env bash
# Render build script for PharmaAgent backend
set -o errexit

echo "🔧 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy agents module from repo root into backend/
# (Render clones the full repo; rootDir just sets the working directory)
if [ -d "../agents" ]; then
    echo "📦 Copying agents module into backend..."
    cp -r ../agents ./agents
    echo "✅ Agents module copied successfully"
else
    echo "⚠️ Warning: ../agents directory not found — chat will use fallback mode"
fi

# Copy data files if not already present
if [ -d "../backend/data" ]; then
    echo "📊 Data directory found at backend/data"
elif [ -d "./data" ]; then
    echo "📊 Data directory found"
else
    echo "⚠️ Warning: data directory not found"
fi

# Create necessary directories
mkdir -p uploads/prescriptions

echo "✅ Build complete!"
