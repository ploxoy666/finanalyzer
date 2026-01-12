#!/usr/bin/osascript

# AppleScript to create macOS app launcher
# This creates a clickable application

tell application "Finder"
    set appPath to POSIX file "/Users/light/Desktop/finance report analyzer/launch.sh" as alias
end tell

do shell script "cd '/Users/light/Desktop/finance report analyzer' && ./launch.sh"
