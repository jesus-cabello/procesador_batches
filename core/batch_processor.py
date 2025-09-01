import queue
import threading
from typing import List, Dict, Any
from models.task import Task, TaskStatus
from core.worker import Worker
from config.settings import config
from log_system.logger  import logger
import time

class BatchProcessor:
    def __init__(self, num_workers: int = None):
        self.num_workers = num_workers or config.NUM_WORKERS
        self.task_queue = queue.Queue(maxsize=config.QUEUE_MAX_SIZE)
        self.result_queue = queue.Queue()
        self.workers: List[Worker] = []
        self.stop_event = threading.Event()
        self.results: List[Task] = []
        self.is_running = False

    def start(self):
        """Inicia los workers"""
        if self.is_running:
            logger.warning("Batch processor already running")
            return

        logger.info(f"Starting batch processor with {self.num_workers} workers")

        for i in range(self.num_workers):
            worker = Worker(
                task_queue=self.task_queue,
                result_queue=self.result_queue,
                worker_id=i,
                stop_event=self.stop_event
            )
            worker.start()
            self.workers.append(worker)

        self.is_running = True

        # Thread para recolectar resultados
        self.result_collector = threading.Thread(target=self._collect_results)
        self.result_collector.daemon = True
        self.result_collector.start()

    def stop(self):
        """Detiene los workers"""
        logger.info("Stopping batch processor")

        # Señal de parada
        self.stop_event.set()

        # Añadir None para cada worker para que terminen
        for _ in range(self.num_workers):
            self.task_queue.put(None)

        # Esperar a que terminen
        for worker in self.workers:
            worker.join(timeout=5)

        self.is_running = False
        logger.info("Batch processor stopped")

    def add_task(self, task: Task):
        """Añade una tarea a la cola"""
        if not self.is_running:
            raise RuntimeError("Batch processor is not running")

        self.task_queue.put(task)
        logger.info(f"Added task {task.task_id} to queue")

    def add_batch(self, tasks: List[Task]):
        """Añade un batch de tareas"""
        for task in tasks:
            self.add_task(task)

        logger.info(f"Added batch of {len(tasks)} tasks")

    def process_batch_sync(self, tasks: List[Task]) -> List[Task]:
        """Procesa un batch de manera síncrona (espera a que termine)"""
        if not self.is_running:
            self.start()

        # Añadir tareas
        self.add_batch(tasks)

        # Esperar a que se procesen todas
        self.task_queue.join()

        # Dar tiempo para que se recolecten los resultados
        time.sleep(0.5)

        return self.get_results()

    def _collect_results(self):
        """Thread que recolecta resultados de la cola"""
        while not self.stop_event.is_set() or not self.result_queue.empty():
            try:
                result = self.result_queue.get(timeout=1)
                if result:
                    self.results.append(result)
                    self._process_result(result)
            except queue.Empty:
                continue

    def _process_result(self, task: Task):
        """Procesa un resultado (puede extenderse para guardar en BD, etc.)"""
        if task.status == TaskStatus.COMPLETED:
            logger.info(f"Task {task.task_id} completed successfully")
        else:
            logger.error(f"Task {task.task_id} failed: {task.error_message}")

    def get_results(self) -> List[Task]:
        """Obtiene los resultados procesados"""
        return self.results.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del procesamiento"""
        completed = sum(1 for t in self.results if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.results if t.status == TaskStatus.FAILED)

        return {
            "total_processed": len(self.results),
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / len(self.results) * 100) if self.results else 0,
            "queue_size": self.task_queue.qsize()
        }
