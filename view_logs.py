#!/usr/bin/env python3
"""
Simple script to view Django logs
Usage: python view_logs.py [log_type] [lines]
Examples:
    python view_logs.py email 50    # Show last 50 lines of email log
    python view_logs.py django 100  # Show last 100 lines of django log
    python view_logs.py email       # Show all email log
"""

import sys
import os
from pathlib import Path

def view_log(log_type, lines=None):
    """View log file with optional line limit"""
    log_file = Path('logs') / f'{log_type}.log'
    
    if not log_file.exists():
        print(f"Log file {log_file} does not exist.")
        return
    
    try:
        with open(log_file, 'r') as f:
            log_lines = f.readlines()
        
        if lines:
            # Show last N lines
            log_lines = log_lines[-lines:]
        
        print(f"\n=== {log_type.upper()} LOG ===")
        print(f"File: {log_file}")
        print(f"Total lines: {len(log_lines)}")
        print("=" * 50)
        
        for line in log_lines:
            print(line.rstrip())
            
    except Exception as e:
        print(f"Error reading log file: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python view_logs.py [email|django] [lines]")
        print("Examples:")
        print("  python view_logs.py email 50    # Show last 50 lines of email log")
        print("  python view_logs.py django 100  # Show last 100 lines of django log")
        print("  python view_logs.py email       # Show all email log")
        return
    
    log_type = sys.argv[1]
    lines = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if log_type not in ['email', 'django']:
        print("Log type must be 'email' or 'django'")
        return
    
    view_log(log_type, lines)

if __name__ == '__main__':
    main() 