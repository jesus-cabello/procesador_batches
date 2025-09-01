import threading
import queue
from typing import Optional
from models.task import Task, TaskStatus
from services.api_client import APIClient
from logging.logger import logger
from datetime import datetime

class Worker(threading.Thread):
    def __init__(self, task_queue: queue.Queue, result_queue: queue.Queue,
                 worker_id: int, stop_event: threading.Event):
        super().__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.worker_id = worker_id
        self.stop_event = stop_event
        self.api_client = APIClient()
        self.daemon = True

    def run(self):
        """Método principal del worker"""
        logger.info(f"Worker {self.worker_id} started")

        while not self.stop_event.is_set():
            try:
                # Obtener tarea de la cola (timeout para permitir chequeo de stop_event)
                task: Task = self.task_queue.get(timeout=1)

                if task is None:  # Señal de parada
                    break

                # Procesar tarea
                self.process_task(task)

                # Marcar tarea como completada
                self.task_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {str(e)}", exc_info=True)

        logger.info(f"Worker {self.worker_id} stopped")

    def process_task(self, task: Task):
        """Procesa una tarea individual"""
        try:
            task.status = TaskStatus.PROCESSING
            logger.info(f"Worker {self.worker_id} processing task {task.task_id}")

            # Ejecutar la petición
            result = self.api_client.execute_request(task)

            # Actualizar tarea con resultado
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.response_data = result

            # Añadir a cola de resultados
            self.result_queue.put(task)

            logger.info(f"Worker {self.worker_id} completed task {task.task_id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error_message = str(e)

            self.result_queue.put(task)

            logger.error(f"Worker {self.worker_id} failed task {task.task_id}: {str(e)}")
