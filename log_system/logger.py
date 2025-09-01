import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from config.settings import config

class TransactionLogger:
    def __init__(self):
        self.setup_loggers()

    def setup_loggers(self):
        # Crear directorio de logs si no existe
        Path(config.LOG_DIR).mkdir(parents=True, exist_ok=True)
        Path(f"{config.LOG_DIR}/transactions").mkdir(parents=True, exist_ok=True)

        # Logger principal
        self.app_logger = logging.getLogger("app")
        self.app_logger.setLevel(getattr(logging, config.LOG_LEVEL))

        # Handler para archivo
        app_handler = logging.FileHandler(f"{config.LOG_DIR}/app.log")
        app_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.app_logger.addHandler(app_handler)

        # Logger de errores
        self.error_logger = logging.getLogger("errors")
        self.error_logger.setLevel(logging.ERROR)

        error_handler = logging.FileHandler(f"{config.LOG_DIR}/errors.log")
        error_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - %(exc_info)s')
        )
        self.error_logger.addHandler(error_handler)

    def log_transaction(self, task_id: str, transaction_data: Dict[str, Any]):
        """Guarda log detallado de cada transacción"""
        if not config.ENABLE_TRANSACTION_LOGS:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{config.LOG_DIR}/transactions/{task_id}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id,
                **transaction_data
            }, f, indent=2, default=str)

    def info(self, message: str):
        self.app_logger.info(message)

    def error(self, message: str, exc_info=None):
        self.error_logger.error(message, exc_info=exc_info)
        self.app_logger.error(message)

logger = TransactionLogger()
