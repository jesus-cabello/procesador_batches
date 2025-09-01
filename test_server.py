from flask import Flask, jsonify, request
import random
import time
from datetime import datetime

app = Flask(__name__)

# Almacén en memoria para simular base de datos
users_db = {str(i): {"id": i, "name": f"User {i}", "status": "inactive"} for i in range(100)}
request_log = []

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """Endpoint GET de prueba"""
    # Simular latencia
    time.sleep(random.uniform(0.1, 0.3))

    # Log de request
    request_log.append({
        "timestamp": datetime.now().isoformat(),
        "method": "GET",
        "endpoint": f"/users/{user_id}"
    })

    # Simular error ocasional (10% de probabilidad)
    if random.random() < 0.1:
        return jsonify({"error": "Service temporarily unavailable"}), 503

    if user_id in users_db:
        return jsonify(users_db[user_id]), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/users/<user_id>', methods=['PATCH'])
def patch_user(user_id):
    """Endpoint PATCH de prueba"""
    time.sleep(random.uniform(0.1, 0.3))

    data = request.get_json()

    request_log.append({
        "timestamp": datetime.now().isoformat(),
        "method": "PATCH",
        "endpoint": f"/users/{user_id}",
        "data": data
    })

    # Simular error ocasional
    if random.random() < 0.1:
        return jsonify({"error": "Service temporarily unavailable"}), 503

    if user_id in users_db:
        users_db[user_id].update(data)
        return jsonify(users_db[user_id]), 200
    return jsonify({"error": "User not found"}), 404

@app.route('/users', methods=['POST'])
def create_user():
    """Endpoint POST de prueba"""
    time.sleep(random.uniform(0.1, 0.3))

    data = request.get_json()
    user_id = str(len(users_db))

    request_log.append({
        "timestamp": datetime.now().isoformat(),
        "method": "POST",
        "endpoint": "/users",
        "data": data
    })

    users_db[user_id] = {
        "id": user_id,
        **data
    }

    return jsonify(users_db[user_id]), 201

@app.route('/stats', methods=['GET'])
def get_stats():
    """Endpoint para ver estadísticas del servidor"""
    return jsonify({
        "total_users": len(users_db),
        "total_requests": len(request_log),
        "last_requests": request_log[-10:]
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    print("🚀 Starting test server on <http://localhost:5000>")
    print("📊 Check stats at <http://localhost:5000/stats>")
    app.run(debug=True, port=5000)
