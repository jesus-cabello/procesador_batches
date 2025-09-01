import requests
from typing import Dict, Any, Optional
from models.task import Task, HTTPMethod
from config.settings import config
from log_system.logger import logger
import time

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = config.API_BASE_URL

    def execute_request(self, task: Task) -> Dict[str, Any]:
        """Ejecuta una solicitud HTTP con reintentos"""
        url = f"{self.base_url}{task.endpoint}"

        for attempt in range(config.MAX_RETRIES):
            try:
                task.attempts = attempt + 1

                # Log del intento
                logger.info(f"Task {task.task_id}: Attempt {task.attempts} - {task.method.value} {url}")

                # Ejecutar request según el método
                response = self._make_request(
                    method=task.method,
                    url=url,
                    data=task.data,
                    headers=task.headers
                )

                response.raise_for_status()

                # Log de éxito
                result = {
                    "status_code": response.status_code,
                    "response": response.json() if response.content else None
                }

                logger.log_transaction(task.task_id, {
                    "request": {
                        "method": task.method.value,
                        "url": url,
                        "data": task.data,
                        "headers": task.headers
                    },
                    "response": result,
                    "attempt": task.attempts,
                    "status": "success"
                })

                return result

            except requests.exceptions.RequestException as e:
                logger.error(f"Task {task.task_id}: Attempt {task.attempts} failed - {str(e)}")

                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY * (attempt + 1))  # Backoff exponencial
                else:
                    logger.log_transaction(task.task_id, {
                        "request": {
                            "method": task.method.value,
                            "url": url,
                            "data": task.data
                        },
                        "error": str(e),
                        "attempts": task.attempts,
                        "status": "failed"
                    })
                    raise

    def _make_request(self, method: HTTPMethod, url: str,
                     data: Optional[Dict] = None,
                     headers: Optional[Dict] = None) -> requests.Response:
        """Realiza la petición HTTP"""
        request_kwargs = {
            "timeout": config.API_TIMEOUT,
            "headers": headers or {}
        }

        if method == HTTPMethod.GET:
            return self.session.get(url, params=data, **request_kwargs)
        elif method == HTTPMethod.POST:
            return self.session.post(url, json=data, **request_kwargs)
        elif method == HTTPMethod.PATCH:
            return self.session.patch(url, json=data, **request_kwargs)
        elif method == HTTPMethod.PUT:
            return self.session.put(url, json=data, **request_kwargs)
        elif method == HTTPMethod.DELETE:
            return self.session.delete(url, **request_kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
