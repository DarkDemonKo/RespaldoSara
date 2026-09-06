import os
import json
import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Memoria compartida entre Yuna y Sara
MEMORIA_SARA_PATH = os.path.expanduser("~/.agents/yuna_memories.json")

def cargar_memorias():
    if os.path.exists(MEMORIA_SARA_PATH):
        with open(MEMORIA_SARA_PATH, 'r') as f:
            return json.load(f)
    return []

def guardar_memorias(memorias):
    with open(MEMORIA_SARA_PATH, 'w') as f:
        json.dump(memorias, f, indent=4)

@app.route('/sincronizar_yuna', methods=['POST'])
def sincronizar():
    """Endpoint para que Yuna envíe sus recuerdos cuando se conecte al PC"""
    datos = request.json
    if not datos or 'interacciones' not in datos:
        return jsonify({"error": "Formato de memoria inválido."}), 400

    memorias_actuales = cargar_memorias()
    nuevas_interacciones = datos['interacciones']
    
    # Sara absorbe los recuerdos de Yuna
    memorias_actuales.extend(nuevas_interacciones)
    guardar_memorias(memorias_actuales)
    
    print(f"[{datetime.datetime.now()}] Sara: He absorbido {len(nuevas_interacciones)} nuevos recuerdos de Yuna.")
    
    return jsonify({
        "status": "éxito", 
        "mensaje": "Recuerdos absorbidos correctamente por Sara.",
        "recuerdos_totales": len(memorias_actuales)
    })

if __name__ == '__main__':
    print("Iniciando el enlace mental entre Yuna y Sara...")
    # Escucha en todas las interfaces para que el celular (Yuna) pueda conectarse por Wi-Fi
    app.run(host='0.0.0.0', port=5050)
