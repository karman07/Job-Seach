"""
Quick start script to initialize and run the application
"""

import os
import sys
import subprocess


def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📝 Creating .env from .env.example...")
        
        if os.path.exists('.env.example'):
            # Copy example file
            with open('.env.example', 'r') as src:
                content = src.read()
            with open('.env', 'w') as dst:
                dst.write(content)
            
            print("✓ .env file created")
            print("\n⚠️  IMPORTANT: Edit .env file with your credentials before continuing!")
            print("   Required:")
            print("   - ADZUNA_APP_ID")
            print("   - ADZUNA_APP_KEY")
            print("   - GCP_PROJECT_ID")
            print("   - GCP_TENANT_ID")
            print("   - GOOGLE_APPLICATION_CREDENTIALS")
            print("   - DATABASE_URL")
            sys.exit(1)
        else:
            print("❌ .env.example not found")
            sys.exit(1)
    else:
        print("✓ .env file found")


def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Dependencies installed")


def init_database():
    """Initialize database"""
    print("\n🗄️  Initializing database...")
    
    try:
        # Try Alembic first
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✓ Database initialized via Alembic")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to direct initialization
        print("Alembic not available, using direct initialization...")
        from app.database import init_db
        init_db()
        print("✓ Database initialized")


def create_logs_dir():
    """Create logs directory"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
        print("✓ Logs directory created")


def run_server():
    """Run the FastAPI server"""
    print("\n🚀 Starting FastAPI server...")
    print("Server will be available at: http://localhost:8000")
    print("API docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop\n")
    
    subprocess.run([
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


def main():
    """Main setup and run function"""
    print("=" * 60)
    print("Job Matching API - Quick Start")
    print("=" * 60)
    
    # Step-by-step setup
    check_env_file()
    install_dependencies()
    create_logs_dir()
    init_database()
    
    print("\n" + "=" * 60)
    print("Setup complete! 🎉")
    print("=" * 60)
    
    # Ask to start server
    response = input("\nStart the server now? [Y/n]: ").strip().lower()
    if response in ['', 'y', 'yes']:
        run_server()
    else:
        print("\nTo start the server manually, run:")
        print("  uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
