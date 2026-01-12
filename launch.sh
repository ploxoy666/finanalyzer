#!/bin/bash

# Financial Analyzer - Simple Launcher
# Автоматическая установка и запуск

echo "🚀 Financial Report Analyzer"
echo "================================"
echo ""

# Get directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Check Python version
echo "Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден!"
    echo "Установите Python 3.9+ с https://www.python.org/downloads/"
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION найден"

# Check if Tkinter is available
echo ""
echo "Проверка Tkinter..."
if python3 -c "import tkinter" 2>/dev/null; then
    echo "✓ Tkinter доступен"
    USE_GUI=true
else
    echo "⚠️  Tkinter не найден"
    echo ""
    echo "Tkinter требует установки Python с поддержкой Tk."
    echo ""
    echo "Варианты решения:"
    echo "1. Установить Python с Homebrew: brew install python-tk@3.12"
    echo "2. Переустановить Python с python.org (включает Tkinter)"
    echo "3. Использовать консольную версию (без GUI)"
    echo ""
    read -p "Запустить консольную версию? (y/n): " choice
    
    if [[ $choice == "y" || $choice == "Y" ]]; then
        USE_GUI=false
    else
        echo "Установите Tkinter и попробуйте снова"
        read -p "Нажмите Enter для выхода..."
        exit 1
    fi
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo ""
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Ошибка создания venv"
        read -p "Нажмите Enter для выхода..."
        exit 1
    fi
    echo "✓ Виртуальное окружение создано"
fi

# Activate venv
echo ""
echo "Активация виртуального окружения..."
source venv/bin/activate

# Check if dependencies installed
if [ ! -f "venv/.installed" ]; then
    echo ""
    echo "Установка зависимостей (это может занять 1-2 минуты)..."
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        touch venv/.installed
        echo "✓ Зависимости установлены"
    else
        echo "⚠️  Некоторые зависимости могут быть не установлены"
        echo "Продолжаем..."
    fi
else
    echo "✓ Зависимости уже установлены"
fi

# Launch
echo ""
echo "================================"
echo "🎉 Запуск приложения..."
echo "================================"
echo ""

if [ "$USE_GUI" = true ]; then
    # Launch GUI
    python app_gui.py
else
    # Launch console version
    python main.py
fi

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Произошла ошибка"
    echo ""
    echo "Проверьте:"
    echo "1. Логи выше"
    echo "2. Файл logs/app.log"
    echo ""
    read -p "Нажмите Enter для выхода..."
    exit 1
fi

echo ""
echo "✓ Готово!"
