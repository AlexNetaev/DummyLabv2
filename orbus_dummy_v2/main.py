# OrbusSim Dummy V2 - Main Daemon Entry Point
"""Main entry point for OrbusSim Dummy V2 Daemon."""
import time
import logging
from pathlib import Path

from . import config
from .orchestrator import execute_job

logger = logging.getLogger("orbus_dummy_v2.main")


def main():
    """Haupt-Daemon-Schleife für OrbusSim Dummy V2."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.info("OrbusSim Dummy V2 Daemon gestartet.")
    logger.info("Warte auf experiment.json in %s", config.HARDWARE_QUEUE_DIR)
    
    while True:
        # E-Stop prüfen
        if config.ESTOP_FLAG_FILE.exists():
            logger.critical("E-Stop aktiv - Daemon pausiert.")
            time.sleep(5.0)
            continue
        
        # Auf neues Experiment warten
        experiment_path = config.HARDWARE_QUEUE_DIR / "experiment.json"
        if not experiment_path.exists():
            time.sleep(config.QUEUE_POLL_INTERVAL_S)
            continue
        
        # Job ausführen
        try:
            execute_job(experiment_path)
        except Exception as e:
            logger.error(f"Unerwarteter Fehler in der Daemon-Schleife: {e}", exc_info=True)
            time.sleep(config.QUEUE_POLL_INTERVAL_S)


if __name__ == "__main__":
    main()
