#!/usr/bin/env python3
"""
AI Agent System CLI
ELK loglarını analiz edip otomatik fix oluşturur
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

from orchestrator import Orchestrator
from elk_connector import create_elk_connector


def load_file_contents(file_paths: list) -> dict:
    """Loads file contents"""
    contents = {}
    
    for path in file_paths:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                contents[path] = f.read()
            print(f"✓ Loaded: {path}")
        else:
            print(f"⚠ File not found: {path}")
    
    return contents


async def run_analysis(args):
    """Runs the main analysis workflow"""
    
    # Connect to ELK
    print("\n🔌 Connecting to ELK...")
    elk = create_elk_connector(
        use_mock=args.mock,
        host=args.elk_host,
        port=args.elk_port,
        username=args.elk_user,
        password=args.elk_password
    )
    
    if not elk.connect():
        print("❌ Could not connect to ELK!")
        return 1
    
    # Fetch logs
    print(f"\n📥 Fetching logs from the last {args.time_range} minutes...")
    elk_logs = elk.get_recent_errors(minutes=args.time_range)
    
    if not elk_logs or elk_logs.strip() == "":
        print("ℹ️  No error logs found.")
        return 0
    
    print(f"✓ Logs received ({len(elk_logs)} characters)")
    
    # Load file contents
    file_contents = {}
    if args.files:
        print(f"\n📂 Loading files...")
        file_contents = load_file_contents(args.files)
    
    # Start the orchestrator
    orchestrator = Orchestrator(repo_path=args.repo_path)
    
    # Run the analysis
    result = await orchestrator.process_logs(elk_logs, file_contents)
    
    if result.success:
        print(f"\n✅ Fix created successfully!")
        print(f"\nNext steps:")
        print(f"  1. git checkout {result.branch_name}")
        print(f"  2. Review the changes")
        print(f"  3. Run the tests")
        print(f"  4. git push origin {result.branch_name}")
        print(f"  5. Create a pull request")
        return 0
    else:
        print(f"\n❌ Could not create fix!")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description='AI Agent System - ELK Log Analyzer and Auto-Fix',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in mock mode (for testing)
  python cli.py --mock
  
  # Fetch logs from real ELK
  python cli.py --elk-host localhost --elk-port 9200
  
  # Analyze specific files
  python cli.py --mock --files UserController.java UserService.java
  
  # Fetch logs from the last 120 minutes
  python cli.py --elk-host elk.example.com --time-range 120
        """
    )
    
    # ELK settings
    elk_group = parser.add_argument_group('ELK Settings')
    elk_group.add_argument('--mock', action='store_true',
                          help='Use mock ELK (test mode)')
    elk_group.add_argument('--elk-host', default='localhost',
                          help='Elasticsearch host (default: localhost)')
    elk_group.add_argument('--elk-port', type=int, default=9200,
                          help='Elasticsearch port (default: 9200)')
    elk_group.add_argument('--elk-user', help='Elasticsearch username')
    elk_group.add_argument('--elk-password', help='Elasticsearch password')
    elk_group.add_argument('--time-range', type=int, default=60,
                          help='Fetch logs from the last N minutes (default: 60)')
    
    # File settings
    file_group = parser.add_argument_group('File Settings')
    file_group.add_argument('--files', nargs='+',
                           help='Files to analyze')
    file_group.add_argument('--repo-path', default='.',
                           help='Git repository path (default: .)')
    
    args = parser.parse_args()
    
    # Run asynchronously
    try:
        exit_code = asyncio.run(run_analysis(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
