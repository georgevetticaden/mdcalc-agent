#!/bin/bash

# Helper script to manage MDCalc demo browser session

PROFILE_DIR="$HOME/Library/Application Support/MDCalc-Demo-Chrome"

case "$1" in
    "clear")
        echo "🗑️  Clearing MDCalc demo browser session..."
        if [ -d "$PROFILE_DIR" ]; then
            rm -rf "$PROFILE_DIR"
            echo "✅ Session cleared. Next launch will start fresh."
        else
            echo "ℹ️  No session data found."
        fi
        ;;

    "backup")
        echo "💾 Backing up MDCalc demo browser session..."
        if [ -d "$PROFILE_DIR" ]; then
            BACKUP_DIR="$PROFILE_DIR-backup-$(date +%Y%m%d-%H%M%S)"
            cp -r "$PROFILE_DIR" "$BACKUP_DIR"
            echo "✅ Session backed up to: $BACKUP_DIR"
        else
            echo "❌ No session data to backup."
        fi
        ;;

    "restore")
        if [ -z "$2" ]; then
            echo "❌ Please specify backup directory to restore from"
            echo "Usage: $0 restore <backup-directory>"
            exit 1
        fi
        echo "♻️  Restoring MDCalc demo browser session from $2..."
        if [ -d "$2" ]; then
            rm -rf "$PROFILE_DIR"
            cp -r "$2" "$PROFILE_DIR"
            echo "✅ Session restored from backup."
        else
            echo "❌ Backup directory not found: $2"
        fi
        ;;

    "info")
        echo "ℹ️  MDCalc Demo Browser Session Info"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Profile directory: $PROFILE_DIR"
        if [ -d "$PROFILE_DIR" ]; then
            echo "Status: Session data exists"
            echo "Size: $(du -sh "$PROFILE_DIR" | cut -f1)"
            echo ""
            echo "To preserve login:"
            echo "1. Launch browser with ./launch_demo_browser.sh"
            echo "2. Log into MDCalc if needed"
            echo "3. Close browser when done"
            echo "4. Session will be preserved for next launch"
        else
            echo "Status: No session data (will be created on first launch)"
        fi
        ;;

    *)
        echo "MDCalc Demo Browser Session Manager"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Usage: $0 {info|clear|backup|restore <dir>}"
        echo ""
        echo "Commands:"
        echo "  info    - Show session information"
        echo "  clear   - Clear all session data (logout)"
        echo "  backup  - Backup current session"
        echo "  restore - Restore session from backup"
        echo ""
        echo "Example:"
        echo "  $0 info                    # Check session status"
        echo "  $0 backup                  # Save current session"
        echo "  $0 clear                   # Start fresh (logout)"
        echo "  $0 restore ~/backup-dir    # Restore previous session"
        ;;
esac