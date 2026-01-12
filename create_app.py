#!/usr/bin/env python3
"""
Create macOS Application Bundle
Creates a clickable .app for Financial Report Analyzer
"""

import os
import shutil
from pathlib import Path

def create_app_bundle():
    """Create macOS .app bundle."""
    
    # Paths
    project_dir = Path(__file__).parent
    app_name = "Financial Analyzer.app"
    app_path = project_dir / app_name
    
    # Remove existing app
    if app_path.exists():
        shutil.rmtree(app_path)
    
    # Create app structure
    contents_dir = app_path / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    # Create Info.plist
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Financial Analyzer</string>
    <key>CFBundleDisplayName</key>
    <string>Financial Report Analyzer</string>
    <key>CFBundleIdentifier</key>
    <string>com.financialanalyzer.app</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
"""
    
    (contents_dir / "Info.plist").write_text(info_plist)
    
    # Create launcher script
    launcher_script = f"""#!/bin/bash

# Get the directory of the app bundle
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && cd ../../../ && pwd )"

# Change to project directory
cd "$DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    # Create venv if it doesn't exist
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Launch GUI
python app_gui.py 2>&1 | tee logs/app.log

# Keep window open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "Error occurred. Check logs/app.log for details."
    echo "Press any key to exit..."
    read -n 1
fi
"""
    
    launcher_path = macos_dir / "launcher"
    launcher_path.write_text(launcher_script)
    launcher_path.chmod(0o755)
    
    print(f"✓ Created {app_name}")
    print(f"  Location: {app_path}")
    print(f"\nTo use:")
    print(f"  1. Double-click '{app_name}' to launch")
    print(f"  2. Or drag to Applications folder")
    print(f"\nNote: On first launch, you may need to:")
    print(f"  - Right-click → Open (to bypass Gatekeeper)")
    print(f"  - Allow in System Preferences → Security & Privacy")


if __name__ == "__main__":
    create_app_bundle()
