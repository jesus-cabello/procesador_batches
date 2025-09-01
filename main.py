from core.batch_processor import BatchProcessor
from models.task import Task, HTTPMethod
from logging.logger import logger
import json

def main():
    # Inicializar procesador
    processor = BatchProcessor(num_workers=5)
    processor.start()

    try:
        # Ejemplo: Crear batch de tareas
        tasks = []

        # Tareas GET
        for i in range(10):
            task = Task(
                method=HTTPMethod.GET,
                endpoint=f"/users/{i}",
                headers={"Authorization": "Bearer token123"}
            )
            tasks.append(task)

        # Tareas PATCH
        for i in range(5):
            task = Task(
                method=HTTPMethod.PATCH,
                endpoint=f"/users/{i}",
                data={"status": "active", "updated": True},
                headers={"Authorization": "Bearer token123"}
            )
            tasks.append(task)

        # Procesar batch
        logger.info(f"Processing batch of {len(tasks)} tasks")
        results = processor.process_batch_sync(tasks)

        # Mostrar estadísticas
        stats = processor.get_statistics()
        logger.info(f"Processing statistics: {json.dumps(stats, indent=2)}")

        # Guardar resumen de resultados
        summary = {
            "statistics": stats,
            "results": [task.to_dict() for task in results]
        }

        with open("logs/batch_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)

    finally:
        processor.stop()

if __name__ == "__main__":
    main()
