import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all necessary directories exist."""
    dirs = ["config", "data", "data/conversations"]
    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")

def run_streamlit_app():
    """Run the Streamlit web application."""
    try:
        logger.info("Starting the Streamlit application...")
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app/app.py"], 
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Streamlit app: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Set up directories
    ensure_directories()
    
    # Run the app
    run_streamlit_app() 