import psutil
import logging

logger = logging.getLogger(__name__)

def check_chrome_running():
    """Check if Chrome is running and warn user"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def startup_checks():
    """Run startup checks and display warnings"""
    print("\n" + "="*60)
    print("🔍 TERMINAL_OS - Startup Checks")
    print("="*60)
    
    if check_chrome_running():
        print("⚠️  WARNING: Chrome is currently running!")
        print("   For optimal scraping/search functionality:")
        print("   → Please close Chrome before using web tools")
        print("   → This allows Eveline to use your Chrome profile")
        print("="*60 + "\n")
    else:
        print("✅ Chrome is not running - Ready for web scraping")
        print("="*60 + "\n")
