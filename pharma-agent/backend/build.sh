#!/usr/bin/env bash
# Render build script for PharmaAgent backend

set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads/prescriptions
