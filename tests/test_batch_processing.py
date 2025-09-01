#!/usr/bin/env python
"""
Script de prueba para el sistema de procesamiento por lotes
"""

import sys
import os
from pathlib import Path

# Añadir el directorio padre al path de Python
# Obtener la ruta del directorio actual
current_dir = Path(__file__).resolve().parent
# Ir al directorio padre (procesador_batches)
parent_dir = current_dir.parent
# Añadir al path
sys.path.insert(0, str(parent_dir))

# Ahora sí importar los módulos
from core.batch_processor import BatchProcessor
from models.task import Task, HTTPMethod
from log_system.logger import logger
from config.settings import config
import requests
import time
import json

def check_server():
    """Verifica que el servidor de prueba esté corriendo"""
    try:

        response = requests.get("http://localhost:5000/health", timeout=1)
        
        if response.status_code == 200:
            print("✅ Servidor de prueba funcionando")
            return True
    except:
        print("❌ Error: El servidor de prueba no está corriendo")
        print("Por favor, ejecuta en otra terminal: python test_server.py")
        return False
    return False

def test_basic_operations():
    """Prueba operaciones básicas GET y PATCH"""
    print("\\n" + "="*60)
    print("TEST 1: Operaciones Básicas (GET y PATCH)")
    print("="*60)

    # Actualizar configuración para usar servidor local
    config.API_BASE_URL = "http://localhost:5000"
    config.NUM_WORKERS = 3

    processor = BatchProcessor(num_workers=3)
    processor.start()

    try:
        tasks = []

        # Crear 5 tareas GET
        print("\\n📤 Creando 5 tareas GET...")
        for i in range(5):
            task = Task(
                method=HTTPMethod.GET,
                endpoint=f"/users/{i}",
            )
            tasks.append(task)
            print(f"  - GET /users/{i}")

        # Crear 5 tareas PATCH
        print("\\n📤 Creando 5 tareas PATCH...")
        for i in range(5):
            task = Task(
                method=HTTPMethod.PATCH,
                endpoint=f"/users/{i}",
                data={"status": "active", "updated_by": "batch_processor"}
            )
            tasks.append(task)
            print(f"  - PATCH /users/{i}")

        # Procesar batch
        print(f"\\n⚙️  Procesando {len(tasks)} tareas con {config.NUM_WORKERS} workers...")
        start_time = time.time()

        results = processor.process_batch_sync(tasks)

        elapsed_time = time.time() - start_time

        # Mostrar resultados
        print(f"\\n✅ Procesamiento completado en {elapsed_time:.2f} segundos")

        stats = processor.get_statistics()
        print("\\n📊 Estadísticas:")
        print(f"  - Total procesadas: {stats['total_processed']}")
        print(f"  - Exitosas: {stats['completed']}")
        print(f"  - Fallidas: {stats['failed']}")
        print(f"  - Tasa de éxito: {stats['success_rate']:.1f}%")

        # Mostrar algunos resultados
        print("\\n📋 Primeros 3 resultados:")
        for task in results[:3]:
            status_icon = "✅" if task.status.value == "completed" else "❌"
            print(f"  {status_icon} Task {task.task_id[:8]}... - {task.method.value} {task.endpoint} - {task.status.value}")

    finally:
        processor.stop()
        print("\\n🛑 Procesador detenido")

def test_high_volume():
    """Prueba con alto volumen de tareas"""
    print("\\n" + "="*60)
    print("TEST 2: Alto Volumen de Tareas")
    print("="*60)

    config.API_BASE_URL = "http://localhost:5000"
    config.NUM_WORKERS = 5

    processor = BatchProcessor(num_workers=5)
    processor.start()

    try:
        tasks = []

        # Crear 50 tareas mixtas
        print("\\n📤 Creando 50 tareas mixtas...")
        for i in range(50):
            if i % 3 == 0:
                task = Task(
                    method=HTTPMethod.POST,
                    endpoint="/users",
                    data={"name": f"New User {i}", "email": f"user{i}@test.com"}
                )
            elif i % 2 == 0:
                task = Task(
                    method=HTTPMethod.PATCH,
                    endpoint=f"/users/{i % 10}",
                    data={"counter": i}
                )
            else:
                task = Task(
                    method=HTTPMethod.GET,
                    endpoint=f"/users/{i % 10}"
                )
            tasks.append(task)

        print(f"  - {sum(1 for t in tasks if t.method == HTTPMethod.GET)} GET")
        print(f"  - {sum(1 for t in tasks if t.method == HTTPMethod.PATCH)} PATCH")
        print(f"  - {sum(1 for t in tasks if t.method == HTTPMethod.POST)} POST")

        # Procesar
        print(f"\\n⚙️  Procesando {len(tasks)} tareas con {config.NUM_WORKERS} workers...")
        start_time = time.time()

        results = processor.process_batch_sync(tasks)

        elapsed_time = time.time() - start_time

        # Estadísticas
        stats = processor.get_statistics()
        print(f"\\n✅ Procesamiento completado en {elapsed_time:.2f} segundos")
        print(f"📊 Rendimiento: {len(tasks)/elapsed_time:.1f} tareas/segundo")
        print(f"📊 Tasa de éxito: {stats['success_rate']:.1f}%")

    finally:
        processor.stop()

def test_error_handling():
    """Prueba manejo de errores y reintentos"""
    print("\\n" + "="*60)
    print("TEST 3: Manejo de Errores y Reintentos")
    print("="*60)

    config.API_BASE_URL = "http://localhost:5000"
    config.MAX_RETRIES = 3
    config.RETRY_DELAY = 1

    processor = BatchProcessor(num_workers=2)
    processor.start()

    try:
        tasks = []

        # Crear tareas que incluyen endpoints que fallarán
        print("\\n📤 Creando tareas con algunos endpoints inválidos...")

        # Tareas que deberían funcionar
        for i in range(3):
            task = Task(
                method=HTTPMethod.GET,
                endpoint=f"/users/{i}"
            )
            tasks.append(task)

        # Tareas que fallarán (usuarios no existentes)
        for i in range(1000, 1003):
            task = Task(
                method=HTTPMethod.GET,
                endpoint=f"/users/{i}"
            )
            tasks.append(task)

        print(f"  - {len(tasks)} tareas creadas (algunas fallarán)")

        # Procesar
        print(f"\\n⚙️  Procesando con reintentos (max {config.MAX_RETRIES})...")
        results = processor.process_batch_sync(tasks)

        # Analizar resultados
        successful = [t for t in results if t.status.value == "completed"]
        failed = [t for t in results if t.status.value == "failed"]

        print(f"\\n📊 Resultados:")
        print(f"  - Exitosas: {len(successful)}")
        print(f"  - Fallidas: {len(failed)}")

        if failed:
            print("\\n❌ Tareas fallidas:")
            for task in failed[:3]:
                print(f"  - {task.method.value} {task.endpoint}: {task.error_message[:50]}...")

    finally:
        processor.stop()

def check_logs():
    """Verifica que los logs se estén generando correctamente"""
    print("\\n" + "="*60)
    print("TEST 4: Verificación de Logs")
    print("="*60)

    log_dir = Path("logs")

    if log_dir.exists():
        print("\\n📁 Contenido del directorio de logs:")

        # Verificar app.log
        app_log = log_dir / "app.log"
        if app_log.exists():
            lines = app_log.read_text().splitlines()
            print(f"\\n  📄 app.log: {len(lines)} líneas")
            if lines:
                print(f"     Última entrada: {lines[-1][:100]}...")

        # Verificar errors.log
        error_log = log_dir / "errors.log"
        if error_log.exists():
            lines = error_log.read_text().splitlines()
            print(f"\\n  📄 errors.log: {len(lines)} líneas")

        # Verificar transacciones
        trans_dir = log_dir / "transactions"
        if trans_dir.exists():
            trans_files = list(trans_dir.glob("*.json"))
            print(f"\\n  📁 transactions/: {len(trans_files)} archivos")

            if trans_files:
                # Mostrar una transacción de ejemplo
                with open(trans_files[-1]) as f:
                    transaction = json.load(f)
                print(f"\\n  📋 Ejemplo de transacción ({trans_files[-1].name}):")
                print(f"     - Task ID: {transaction.get('task_id', 'N/A')[:8]}...")
                print(f"     - Status: {transaction.get('status', 'N/A')}")
                print(f"     - Timestamp: {transaction.get('timestamp', 'N/A')}")
    else:
        print("❌ El directorio de logs no existe")

def main():
    """Función principal de pruebas"""
    print("\\n")
    print("🚀 SISTEMA DE PRUEBAS - BATCH PROCESSOR")
    print("="*60)

    # Verificar servidor
    if not check_server():
        return

    try:
        # Ejecutar pruebas
        test_basic_operations()
        time.sleep(2)

        test_high_volume()
        time.sleep(2)

        test_error_handling()
        time.sleep(2)

        check_logs()

        # Ver estadísticas del servidor
        print("\\n" + "="*60)
        print("📊 ESTADÍSTICAS DEL SERVIDOR DE PRUEBA")
        print("="*60)

        response = requests.get("http://localhost:5000/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"\\n  - Total de requests procesados: {stats['total_requests']}")
            print(f"  - Usuarios en base de datos: {stats['total_users']}")

            if stats.get('last_requests'):
                print(f"\\n  📋 Últimos 3 requests:")
                for req in stats['last_requests'][-3:]:
                    print(f"     - {req['method']} {req['endpoint']} at {req['timestamp'][-8:]}")

        print("\\n✅ TODAS LAS PRUEBAS COMPLETADAS")

    except Exception as e:
        print(f"\\n❌ Error durante las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
