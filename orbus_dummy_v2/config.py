"""
Configuration module for OrbusSim Dummy V2.

This module handles:
- Project root determination
- .env loading
- Workspace path resolution
- Directory definitions
- Timing and noise constants
- Automatic directory creation

NO simulation logic, station logic, physics, file watchers, or writers.
Only configuration and path management.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


def resolve_workspace_root() -> Path:
    """
    Resolve the workspace root path based on environment variables.
    
    Priority:
    1. WORKSPACE_ROOT - if set, use this path
    2. EXTERNAL_WORKSPACE_PATH - if set and WORKSPACE_ROOT not set, use this
    3. Local workspace folder - if neither is set
    
    Returns:
        Path: The resolved workspace root path
    """
    workspace_root = os.getenv("WORKSPACE_ROOT")
    external_path = os.getenv("EXTERNAL_WORKSPACE_PATH")
    
    if workspace_root:
        return Path(workspace_root)
    elif external_path:
        return Path(external_path)
    else:
        # Use a local workspace folder relative to this config file
        return Path(__file__).parent.parent / "workspace"


# Resolve workspace root
WORKSPACE_ROOT = resolve_workspace_root()

# Define directory paths
HARDWARE_QUEUE_DIR = WORKSPACE_ROOT / "03_Hardware_Queue"
RESEARCH_CYCLES_DIR = WORKSPACE_ROOT / "02_Research_Cycles"
SYSTEM_DIR = WORKSPACE_ROOT / "00_System"
STATIC_DIR = Path(__file__).parent.parent / "static"

# Define special files
ESTOP_FLAG_FILE = SYSTEM_DIR / "ESTOP.flag"

# Calibration file path (within project directory)
CALIBRATION_FILE = Path(__file__).parent / "calibration" / "calibration_data.json"

# Queue subdirectories
PROCESSED_QUEUE_DIR = HARDWARE_QUEUE_DIR / "_processed"
FAILED_QUEUE_DIR = HARDWARE_QUEUE_DIR / "_failed"

# Timing constants (in seconds unless noted)
QUEUE_POLL_INTERVAL_S = float(os.getenv("QUEUE_POLL_INTERVAL_S", "1.0"))
STATION_PAUSE_S = float(os.getenv("STATION_PAUSE_S", "0.5"))
MEASUREMENT_INTERVAL_MS = int(os.getenv("MEASUREMENT_INTERVAL_MS", "100"))
FLUORESCENCE_DURATION_S = float(os.getenv("FLUORESCENCE_DURATION_S", "5.0"))

# Noise constants
TEMP_NOISE_STD_C = float(os.getenv("TEMP_NOISE_STD_C", "0.1"))
FLUORESCENCE_NOISE_STD_AU = float(os.getenv("FLUORESCENCE_NOISE_STD_AU", "0.01"))
DOSING_NOISE_PERCENT = float(os.getenv("DOSING_NOISE_PERCENT", "1.0"))

# Optional simulation seed
SIMULATION_SEED = os.getenv("SIMULATION_SEED")
if SIMULATION_SEED is not None:
    SIMULATION_SEED = int(SIMULATION_SEED)


def create_required_directories():
    """
    Create all required directories if they do not exist.
    
    This includes:
    - Workspace root
    - Hardware queue directory
    - Research cycles directory
    - System directory
    - Processed queue directory
    - Failed queue directory
    """
    directories = [
        WORKSPACE_ROOT,
        HARDWARE_QUEUE_DIR,
        RESEARCH_CYCLES_DIR,
        SYSTEM_DIR,
        PROCESSED_QUEUE_DIR,
        FAILED_QUEUE_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Auto-create directories on module import
create_required_directories()
