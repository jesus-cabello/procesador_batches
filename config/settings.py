import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "<https://api.example.com>")
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1

    # Queue Configuration
    QUEUE_MAX_SIZE: int = 1000
    NUM_WORKERS: int = 5
    BATCH_SIZE: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    ENABLE_TRANSACTION_LOGS: bool = True

config = Config()
