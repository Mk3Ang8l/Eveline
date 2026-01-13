"""
TERMINAL_OS Development Launcher
Starts both frontend (Vite) and backend (FastAPI) simultaneously
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def print_banner():
    print("""
╔════════════════════════════════════════╗
║       TERMINAL_OS DEV LAUNCHER         ║
║     Starting Frontend + Backend...     ║
╚════════════════════════════════════════╝
    """)

def check_dependencies():
    """Check if required dependencies are installed"""
    print("[1/3] Checking dependencies...")
    
    # Check if backend requirements are installed
    backend_dir = Path(__file__).parent / "backend"
    if not (backend_dir / "requirements.txt").exists():
        print("❌ Backend requirements.txt not found!")
        return False
    
    # Check if node_modules exists
    if not (Path(__file__).parent / "node_modules").exists():
        print("⚠️  Frontend dependencies not installed. Run 'npm install' first.")
        return False
    
    print("✅ Dependencies check passed")
    return True

def install_playwright():
    """Install Playwright browsers if needed"""
    print("[2/3] Installing Playwright browsers...")
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            cwd=Path(__file__).parent / "backend"
        )
        print("✅ Playwright browsers installed")
    except subprocess.CalledProcessError:
        print("⚠️  Playwright installation skipped (may already be installed)")

def start_backend():
    """Start FastAPI backend"""
    print("[3/3] Starting backend on http://localhost:8000...")
    backend_dir = Path(__file__).parent / "backend"
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=env
    )

def start_frontend():
    """Start Vite frontend"""
    print("[3/3] Starting frontend on http://localhost:5173...")
    
    # Windows requires shell=True for npm or using npm.cmd
    cmd = ["npm.cmd", "run", "dev"] if os.name == 'nt' else ["npm", "run", "dev"]
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    return subprocess.Popen(
        cmd,
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
        shell=True if os.name == 'nt' else False,
        env=env
    )

def start_discord():
    """Start Standalone Discord Service"""
    print("[3/3] Starting Discord service...")
    backend_dir = Path(__file__).parent / "backend"
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    return subprocess.Popen(
        [sys.executable, "run_discord.py"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
        env=env
    )

def start_playwright_service():
    """Start Node.js Playwright service"""
    print("[3/3] Starting Playwright service on http://localhost:3001...")
    playwright_dir = Path(__file__).parent / "playwright-service"
    
    # Check if service exists
    if not playwright_dir.exists():
        print("⚠️  Playwright service not found, skipping...")
        return None
    
    # Check if node_modules exists
    if not (playwright_dir / "node_modules").exists():
        print("⚠️  Installing Playwright service dependencies...")
        try:
            subprocess.run(
                ["npm.cmd", "install"] if os.name == 'nt' else ["npm", "install"],
                cwd=playwright_dir,
                check=True,
                shell=True if os.name == 'nt' else False
            )
        except subprocess.CalledProcessError:
            print("❌ Failed to install Playwright service dependencies")
            return None

    # Install Playwright browsers for Node.js
    print("Checking Node.js Playwright browsers...")
    try:
        subprocess.run(
            ["npx.cmd", "playwright", "install", "chromium"] if os.name == 'nt' else ["npx", "playwright", "install", "chromium"],
            cwd=playwright_dir,
            check=True,
            shell=True if os.name == 'nt' else False
        )
    except subprocess.CalledProcessError:
        print("⚠️  Failed to install Node.js Playwright browsers")
    
    cmd = ["npm.cmd", "start"] if os.name == 'nt' else ["npm", "start"]
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    
    return subprocess.Popen(
        cmd,
        cwd=playwright_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        bufsize=1,
        shell=True if os.name == 'nt' else False,
        env=env
    )

def main():
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install dependencies first.")
        print("   Backend: cd backend && pip install -r requirements.txt")
        print("   Frontend: npm install")
        sys.exit(1)
    
    # Install Playwright browsers
    install_playwright()
    
    # Start all processes
    playwright_process = start_playwright_service()
    time.sleep(1)  # Give Playwright service time to start
    backend_process = start_backend()
    discord_process = start_discord()
    time.sleep(2)  # Give backend time to start
    frontend_process = start_frontend()
    
    print("\n" + "="*50)
    print("🚀 TERMINAL_OS is running!")
    print("="*50)
    if playwright_process:
        print("Playwright: http://localhost:3001")
    print("Frontend: http://localhost:5173")
    print("Backend:  http://localhost:8000")
    print("Discord:  [Standalone Process]")
    print("API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop all servers")
    print("="*50 + "\n")
    
    try:
        # Stream output from all processes
        while True:
            # Read Playwright service output
            if playwright_process and playwright_process.poll() is None:
                line = playwright_process.stdout.readline()
                if line:
                    print(f"[PLAYWRIGHT] {line.strip()}")
            
            # Read backend output
            if backend_process.poll() is None:
                line = backend_process.stdout.readline()
                if line:
                    print(f"[BACKEND] {line.strip()}")
            
            # Read frontend output
            if frontend_process.poll() is None:
                line = frontend_process.stdout.readline()
                if line:
                    print(f"[FRONTEND] {line.strip()}")
            
            # Read discord output
            if discord_process.poll() is None:
                line = discord_process.stdout.readline()
                if line:
                    print(f"[DISCORD] {line.strip()}")
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down TERMINAL_OS...")
        if playwright_process:
            playwright_process.terminate()
        backend_process.terminate()
        discord_process.terminate()
        frontend_process.terminate()
        if playwright_process:
            playwright_process.wait()
        backend_process.wait()
        discord_process.wait()
        frontend_process.wait()
        print("✅ Shutdown complete")

if __name__ == "__main__":
    main()
