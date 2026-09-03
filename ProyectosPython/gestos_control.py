import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
import subprocess
from collections import deque
import logging

# Configurar logging silencioso para ejecución en segundo plano
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class ControladorGestos:
    def __init__(self):
        """Inicializa el modelo de MediaPipe usando la nueva API Tasks requerida para esta versión de Python."""
        
        # En la API Tasks (>=0.10.x), es obligatorio apuntar al archivo de pesos local .task
        # Ya he descargado este archivo previamente en tu sistema para que funcione automáticamente.
        ruta_modelo = '/home/darkdemon/ProyectosPython/hand_landmarker.task'
        
        base_options = python.BaseOptions(model_asset_path=ruta_modelo)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        
        # Historial para detectar deslizamientos (Swipes)
        self.historial_x = deque(maxlen=15)
        
        # Sistema de enfriamiento (Cooldown) para evitar spam de comandos
        self.cooldowns = {
            "palma": 0.0,
            "puno": 0.0,
            "swipe": 0.0
        }
        self.tiempo_cooldown = 1.5 # Segundos de espera entre gestos idénticos

    def ejecutar_comando(self, comando):
        """Ejecuta un comando del sistema de forma asíncrona."""
        try:
            subprocess.Popen(comando, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info(f"Comando ejecutado: {comando}")
        except Exception as e:
            logging.error(f"Error al ejecutar comando: {e}")

    def dedo_levantado(self, hand_landmarks, tip_id, pip_id):
        """Calcula matemáticamente si un dedo está levantado comparando la punta (tip) con su articulación media (pip)."""
        # En la nueva API Tasks, hand_landmarks es directamente una lista de objetos NormalizedLandmark
        return hand_landmarks[tip_id].y < hand_landmarks[pip_id].y

    def procesar_frame(self, frame):
        """Analiza un frame, detecta gestos y dispara comandos usando la nueva API."""
        # Convertir a RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Crear la imagen compatible con el formato requerido por la API Tasks
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Inferencia de red neuronal
        resultados = self.detector.detect(mp_image)
        
        tiempo_actual = time.time()

        if resultados.hand_landmarks:
            for hand_landmarks in resultados.hand_landmarks:
                # Extraer estado de los 4 dedos principales
                indice_abierto = self.dedo_levantado(hand_landmarks, 8, 6)
                medio_abierto = self.dedo_levantado(hand_landmarks, 12, 10)
                anular_abierto = self.dedo_levantado(hand_landmarks, 16, 14)
                menique_abierto = self.dedo_levantado(hand_landmarks, 20, 18)
                
                # 1. LÓGICA: Palma Abierta (Todos los dedos estirados)
                if indice_abierto and medio_abierto and anular_abierto and menique_abierto:
                    if tiempo_actual - self.cooldowns["palma"] > self.tiempo_cooldown:
                        logging.info("Gesto Detectado: Palma Abierta -> Play/Pause")
                        self.ejecutar_comando("playerctl play-pause")
                        self.cooldowns["palma"] = tiempo_actual
                        self.historial_x.clear() 
                        return

                # 2. LÓGICA: Puño Cerrado (Todos los dedos contraídos)
                elif not indice_abierto and not medio_abierto and not anular_abierto and not menique_abierto:
                    if tiempo_actual - self.cooldowns["puno"] > self.tiempo_cooldown:
                        logging.info("Gesto Detectado: Puño Cerrado -> Silenciar Audio")
                        self.ejecutar_comando("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")
                        self.cooldowns["puno"] = tiempo_actual
                        self.historial_x.clear()
                        return

                # 3. LÓGICA: Deslizamiento (Solo dedo índice levantado apuntando hacia arriba)
                # Rastreamos la coordenada X del nudillo central (landmark 9)
                if indice_abierto and not medio_abierto and not anular_abierto and not menique_abierto:
                    x_actual = hand_landmarks[9].x
                    self.historial_x.append(x_actual)
                    
                    if len(self.historial_x) == self.historial_x.maxlen:
                        x_inicial = self.historial_x[0]
                        x_final = self.historial_x[-1]
                        distancia = x_final - x_inicial
                        
                        if tiempo_actual - self.cooldowns["swipe"] > self.tiempo_cooldown:
                            if distancia > 0.20:
                                logging.info("Gesto Detectado: Swipe a la Derecha -> Siguiente Área de Trabajo")
                                self.ejecutar_comando("hyprctl dispatch workspace e+1")
                                self.cooldowns["swipe"] = tiempo_actual
                                self.historial_x.clear()
                            elif distancia < -0.20:
                                logging.info("Gesto Detectado: Swipe a la Izquierda -> Área de Trabajo Anterior")
                                self.ejecutar_comando("hyprctl dispatch workspace e-1")
                                self.cooldowns["swipe"] = tiempo_actual
                                self.historial_x.clear()
        else:
            self.historial_x.clear()

    def iniciar(self):
        """Inicia la captura de video en modo headless."""
        logging.info("Iniciando Motor de Visión por Computadora (Tasks API Headless Mode)...")
        cap = cv2.VideoCapture(0)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15) 

        if not cap.isOpened():
            logging.error("No se pudo acceder a la cámara web.")
            return

        logging.info("Motor iniciado. Detectando gestos en segundo plano...")
        try:
            while True:
                exito, frame = cap.read()
                if not exito:
                    time.sleep(0.1)
                    continue
                
                time.sleep(0.05) 
                frame = cv2.flip(frame, 1)
                self.procesar_frame(frame)
                
        except KeyboardInterrupt:
            logging.info("Deteniendo motor de visión...")
        finally:
            cap.release()

if __name__ == "__main__":
    motor = ControladorGestos()
    motor.iniciar()
