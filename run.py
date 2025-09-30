#!/usr/bin/env python3
"""
Kasal - Simple startup script for local development on Mac/Linux

This script simplifies running Kasal locally by:
1. Checking prerequisites (Python version, dependencies)
2. Building the frontend (if needed)
3. Starting the backend server with frontend served

Usage:
    python run.py              # Run with default settings (SQLite)
    python run.py --db-type postgres --db-url "postgresql://..."
    python run.py --help       # Show all options
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

def print_banner():
    """Print Kasal startup banner."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                         KASAL                                ║
║       AI Agent Workflow Orchestration Platform              ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Check if Python version is 3.9 or higher."""
    if sys.version_info < (3, 9):
        print(f"❌ Error: Python 3.9+ required. You have {sys.version_info.major}.{sys.version_info.minor}")
        print("   Please upgrade Python: https://www.python.org/downloads/")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def check_node():
    """Check if Node.js is installed."""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  Node.js not found - frontend build will be skipped")
    print("   Install Node.js from: https://nodejs.org/")
    return False

def check_npm():
    """Check if npm is installed."""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  npm not found - frontend build will be skipped")
    return False

def install_backend_dependencies():
    """Install backend Python dependencies."""
    print("\n📦 Installing backend dependencies...")
    
    requirements_file = Path(__file__).parent / "src" / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    try:
        # Use pip to install requirements
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True
        )
        print("✅ Backend dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install backend dependencies: {e}")
        return False

def build_frontend(force=False):
    """Build the frontend React application."""
    print("\n🏗️  Building frontend...")
    
    src_dir = Path(__file__).parent / "src"
    frontend_static_dir = src_dir / "frontend_static"
    
    # Check if frontend_static already exists and has content
    if not force and frontend_static_dir.exists():
        index_html = frontend_static_dir / "index.html"
        if index_html.exists():
            print("ℹ️  Frontend already built. Use --rebuild to force rebuild.")
            return True
    
    # Use the existing build.py script
    build_script = src_dir / "build.py"
    
    if not build_script.exists():
        print(f"❌ Build script not found: {build_script}")
        return False
    
    try:
        # Run the build script
        subprocess.run([sys.executable, str(build_script)], check=True, cwd=str(src_dir))
        print("✅ Frontend built successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Frontend build failed: {e}")
        print("   You can still run the backend without the frontend UI")
        return False

def start_backend(args):
    """Start the backend server."""
    print("\n🚀 Starting Kasal backend server...")
    
    src_dir = Path(__file__).parent / "src"
    entrypoint = src_dir / "entrypoint.py"
    
    if not entrypoint.exists():
        print(f"❌ Entrypoint not found: {entrypoint}")
        return False
    
    # Set environment variables
    env = os.environ.copy()
    
    # Disable telemetry
    env['OTEL_SDK_DISABLED'] = 'true'
    env['CREWAI_DISABLE_TELEMETRY'] = 'true'
    env['USE_NULLPOOL'] = 'true'
    
    # Database configuration
    if args.db_type == 'sqlite':
        db_path = args.db_path or str(src_dir / "kasal.db")
        env['DATABASE_URL'] = f"sqlite:///{db_path}"
        env['DATABASE_URI'] = f"sqlite+aiosqlite:///{db_path}"
        env['SQLITE_DB_PATH'] = db_path
        print(f"📊 Using SQLite database: {db_path}")
    else:
        if not args.db_url:
            print("❌ PostgreSQL requires --db-url parameter")
            return False
        env['DATABASE_URL'] = args.db_url
        env['DATABASE_URI'] = args.db_url
        print(f"📊 Using PostgreSQL database")
    
    # Build the command
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "entrypoint:app",
        "--host", args.host,
        "--port", str(args.port)
    ]
    
    if args.reload:
        cmd.append("--reload")
    
    print(f"\n✨ Kasal will be available at: http://{args.host}:{args.port}")
    print(f"📚 API documentation: http://{args.host}:{args.port}/api-docs")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    try:
        # Start the server
        subprocess.run(cmd, cwd=str(src_dir), env=env)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down Kasal...")
        return True
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    return True

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Kasal - AI Agent Workflow Orchestration Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                          # Run with SQLite (default)
  python run.py --skip-deps              # Skip dependency installation
  python run.py --rebuild                # Force rebuild frontend
  python run.py --reload                 # Enable auto-reload for development
  python run.py --port 9000              # Run on custom port
  python run.py --db-type postgres --db-url "postgresql://user:pass@localhost/kasal"
        """
    )
    
    parser.add_argument(
        '--db-type',
        choices=['sqlite', 'postgres'],
        default='sqlite',
        help='Database type (default: sqlite)'
    )
    
    parser.add_argument(
        '--db-url',
        help='Database URL (required for postgres)'
    )
    
    parser.add_argument(
        '--db-path',
        help='SQLite database file path (default: src/kasal.db)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind to (default: 8000)'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )
    
    parser.add_argument(
        '--skip-deps',
        action='store_true',
        help='Skip dependency installation'
    )
    
    parser.add_argument(
        '--skip-build',
        action='store_true',
        help='Skip frontend build'
    )
    
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Force rebuild frontend even if it exists'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check prerequisites
    print("🔍 Checking prerequisites...\n")
    
    if not check_python_version():
        sys.exit(1)
    
    has_node = check_node()
    has_npm = check_npm()
    
    # Install dependencies
    if not args.skip_deps:
        if not install_backend_dependencies():
            print("\n⚠️  Some dependencies failed to install. Continuing anyway...")
    
    # Build frontend
    if not args.skip_build and has_node and has_npm:
        if not build_frontend(force=args.rebuild):
            print("\n⚠️  Frontend build failed. Backend will run without UI.")
    elif args.skip_build:
        print("\nℹ️  Skipping frontend build (--skip-build)")
    else:
        print("\nℹ️  Skipping frontend build (Node.js/npm not available)")
    
    # Start backend
    if not start_backend(args):
        sys.exit(1)

if __name__ == "__main__":
    main()
