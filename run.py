#!/usr/bin/env python3
"""
Financial Analyzer - Simple Launcher
Запускает GUI или консольную версию в зависимости от доступности Tkinter
"""

import sys
import subprocess
from pathlib import Path

def check_tkinter():
    """Check if Tkinter is available."""
    try:
        import tkinter
        return True
    except ImportError:
        return False

def main():
    """Main launcher."""
    print("🚀 Financial Report Analyzer")
    print("=" * 50)
    print()
    
    # Check Tkinter
    has_tkinter = check_tkinter()
    
    if has_tkinter:
        print("✓ Tkinter доступен - запуск GUI версии")
        print()
        
        # Import and run GUI
        try:
            import app_gui
            app_gui.main()
        except Exception as e:
            print(f"❌ Ошибка запуска GUI: {e}")
            print()
            print("Попробуйте запустить через терминал:")
            print("  ./launch.sh")
            input("\nНажмите Enter для выхода...")
            sys.exit(1)
    else:
        print("⚠️  Tkinter не найден")
        print()
        print("Для GUI версии установите Tkinter:")
        print("  brew install python-tk@3.12")
        print()
        print("Запуск консольной версии...")
        print()
        
        # Run console version
        try:
            import main
            main.main()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            input("\nНажмите Enter для выхода...")
            sys.exit(1)

if __name__ == "__main__":
    main()
