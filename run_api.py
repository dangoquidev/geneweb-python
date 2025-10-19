#!/usr/bin/env python3
"""
Run the GenEWeb FastAPI server.

Usage:
    python run_api.py [--host HOST] [--port PORT] [--db DATABASE_PATH] [--debug] [--reload]

Examples:
    python run_api.py
    python run_api.py --port 8080 --debug
    python run_api.py --db data/ma_famille.pickle --reload
"""

import argparse
import os
import uvicorn


def main():
    """Run the FastAPI server."""
    parser = argparse.ArgumentParser(description="Run GenEWeb API server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--db",
        "--database",
        default="data/showcase.pickle",
        help="Path to database file (default: data/showcase.pickle)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed errors",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes",
    )

    args = parser.parse_args()

    # Set environment variables for the app factory
    os.environ["GENEWEB_DATABASE_PATH"] = args.db
    os.environ["GENEWEB_DEBUG"] = str(args.debug)

    print(f"🚀 Starting GenEWeb API server...")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"💾 Database: {args.db}")
    print(f"🐛 Debug: {args.debug}")
    print(f"🔄 Reload: {args.reload}")
    print(f"📚 API Docs: http://{args.host}:{args.port}/api/docs")
    print(f"📖 ReDoc: http://{args.host}:{args.port}/api/redoc")
    print()

    # Run server
    # When reload=True, use import string; otherwise use app instance
    if args.reload:
        uvicorn.run(
            "backend.api.app:app",  # Import string for reload
            host=args.host,
            port=args.port,
            reload=True,
            log_level="debug" if args.debug else "info",
        )
    else:
        # Import only when not reloading to avoid issues
        from backend.api.app import create_app

        app_instance = create_app(database_path=args.db, debug=args.debug)
        uvicorn.run(
            app_instance,
            host=args.host,
            port=args.port,
            log_level="debug" if args.debug else "info",
        )


if __name__ == "__main__":
    main()
