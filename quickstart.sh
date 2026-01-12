#!/bin/bash

echo "🚀 Financial Report Analyzer - Quick Start"
echo "=========================================="
echo ""

# Change to script directory
cd "$(dirname "$0")"

echo "📦 Установка зависимостей..."
echo ""

# Install dependencies
pip3 install --quiet pandas numpy pydantic python-dateutil loguru 2>&1 | grep -v "Requirement already satisfied" || true

echo ""
echo "✓ Зависимости установлены!"
echo ""
echo "🎉 Запуск демо анализа..."
echo "=========================================="
echo ""

# Run main
python3 main.py

echo ""
echo "=========================================="
echo "✓ Готово! Проверьте папку output/"
echo ""
