import subprocess
import time
import sys

def main():
    print("Iniciando prueba de integración...")
    
    # Iniciar servidor
    server_process = subprocess.Popen([sys.executable, "server.py"])
    print("Servidor iniciado en puerto 8000. Esperando 2 segundos...")
    time.sleep(2)
    
    # Iniciar cliente Yuna
    print("Iniciando cliente Yuna (Móvil)...")
    yuna_process = subprocess.Popen([sys.executable, "yuna_client.py"])
    
    # Iniciar cliente Sara
    print("Iniciando cliente Sara (Desktop)...")
    sara_process = subprocess.Popen([sys.executable, "sara_client.py"])
    
    # Dejar correr por 15 segundos para ver las interacciones
    time.sleep(15)
    
    print("Prueba completada. Terminando procesos...")
    yuna_process.terminate()
    sara_process.terminate()
    server_process.terminate()
    
    print("Test finalizado exitosamente. Revisa los logs para confirmar el ruteo de personalidad.")

if __name__ == "__main__":
    main()
