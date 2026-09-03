import numpy as np
import random
import pygame
import pygame.gfxdraw
import sys
import math

# --- CEREBRO CON NEUROGÉNESIS ---
class RedNeuronal:
    def __init__(self, tamano_capas, pesos=None):
        self.tamano_capas = tamano_capas
        if pesos is None:
            self.pesos = [np.random.randn(y, x + 1) * 0.3 for x, y in zip(tamano_capas[:-1], tamano_capas[1:])]
        else:
            self.pesos = pesos

    def predecir(self, entradas):
        a = np.array(entradas)
        for w in self.pesos:
            a = np.append(a, 1.0) # Bias
            z = np.dot(w, a)
            a = np.tanh(z)
        return a

    def evolucionar_cerebro(self, tasa_mutacion=0.15, escala_mutacion=0.25):
        """Aplica mutaciones de pesos y Neurogénesis (Aumenta la inteligencia añadiendo neuronas)"""
        # 1. Mutar pesos para aprender de la vida anterior
        nuevos_pesos = []
        for w in self.pesos:
            mascara = np.random.rand(*w.shape) < tasa_mutacion
            mutacion = np.random.randn(*w.shape) * escala_mutacion
            nuevos_pesos.append(w + mutacion * mascara)
            
        nuevo_tamano = list(self.tamano_capas)
        
        # 2. Neurogénesis: 15% de probabilidad de que el hijo desarrolle una nueva neurona (Mayor capacidad cerebral)
        if random.random() < 0.15:
            nuevo_tamano[1] += 1
            
            # Conectar la nueva neurona a las entradas
            w1 = nuevos_pesos[0]
            nueva_neurona_w1 = np.random.randn(1, w1.shape[1]) * 0.3
            nuevos_pesos[0] = np.vstack([w1, nueva_neurona_w1])
            
            # Conectar la nueva neurona a las salidas
            w2 = nuevos_pesos[1]
            nueva_conexion_w2 = np.random.randn(w2.shape[0], 1) * 0.3
            # Insertar antes de la columna del bias
            nuevos_pesos[1] = np.insert(w2, -1, nueva_conexion_w2.flatten(), axis=1)
            
        return RedNeuronal(nuevo_tamano, nuevos_pesos)


# --- AGENTE CON INSTINTOS ---
class Agente:
    def __init__(self, x, y, cerebro=None, generacion=1):
        self.x = x
        self.y = y
        self.energia = 100.0
        self.hidratacion = 100.0
        
        # Entradas: 9 | Ocultas: Empieza en 12, pero crece con neurogénesis | Salidas: 4
        self.cerebro = cerebro if cerebro else RedNeuronal([9, 12, 4])
        
        self.vivo = True
        self.causa_muerte = ""
        self.edad = 0
        self.generacion = generacion
        self.color = (255, 255, 255)

    def actuar(self, mundo):
        if not self.vivo: return
        
        # Sistema sensorial
        def dist_sq(p1, p2): return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
        c_comida = min(mundo.comida, key=lambda p: dist_sq(p, (self.x, self.y))) if mundo.comida else None
        c_agua = min(mundo.agua, key=lambda p: dist_sq(p, (self.x, self.y))) if mundo.agua else None
        c_tox = min(mundo.zonas_toxicas, key=lambda t: dist_sq((t['x'], t['y']), (self.x, self.y))) if mundo.zonas_toxicas else None
        
        # Vector de entradas por defecto (si no hay recursos a la vista)
        ref_c = c_comida if c_comida else [640, 360]
        ref_a = c_agua if c_agua else [640, 360]
        ref_t = [c_tox['x'], c_tox['y']] if c_tox else [640, 360]
        
        entradas = [
            (ref_c[0] - self.x) / 1280.0, (ref_c[1] - self.y) / 720.0,
            (ref_a[0] - self.x) / 1280.0, (ref_a[1] - self.y) / 720.0,
            (ref_t[0] - self.x) / 1280.0, (ref_t[1] - self.y) / 720.0,
            self.energia / 100.0,
            self.hidratacion / 100.0,
            min(self.edad / 500.0, 1.0)
        ]
        
        # IA procesa la decisión
        acciones = self.cerebro.predecir(entradas)
        move_x = acciones[0]
        move_y = acciones[1]
        
        # --- 1. INSTINTOS BÁSICOS DE SUPERVIVENCIA ---
        # No son tontos: Si están por morir, el instinto animal sobreescribe la IA parcialmente
        if self.energia < 35 and c_comida:
            dx, dy = c_comida[0] - self.x, c_comida[1] - self.y
            norma = max(math.hypot(dx, dy), 1)
            # Mezcla 30% decisión neuronal y 70% puro instinto hacia la comida
            move_x = (move_x * 0.3) + ((dx / norma) * 0.7)
            move_y = (move_y * 0.3) + ((dy / norma) * 0.7)
            
        elif self.hidratacion < 35 and c_agua:
            dx, dy = c_agua[0] - self.x, c_agua[1] - self.y
            norma = max(math.hypot(dx, dy), 1)
            move_x = (move_x * 0.3) + ((dx / norma) * 0.7)
            move_y = (move_y * 0.3) + ((dy / norma) * 0.7)
            
        vel = 2.8
        self.x += move_x * vel
        self.y += move_y * vel
        self.x = np.clip(self.x, 10, 1270)
        self.y = np.clip(self.y, 10, 710)
        
        # --- 2. HABILIDADES COGNITIVAS (Aprendidas) ---
        # Agricultura (Solo si la Red Neuronal evolucionó para hacerlo)
        if acciones[2] > 0.5 and self.energia > 40 and self.hidratacion > 40 and mundo.tiempo % 15 == 0:
            self.energia -= 35
            self.hidratacion -= 20
            mundo.agregar_recurso('comida', self.x, self.y)
            self.color = (50, 255, 50) 
            
        # Purificación de Agua (Aprendida)
        if acciones[3] > 0.5 and self.energia > 30 and mundo.tiempo % 15 == 0:
            self.energia -= 20
            mundo.agregar_recurso('agua', self.x, self.y)
            self.color = (50, 200, 255)
            
        # --- 3. REPRODUCCIÓN BIOLÓGICA AUTOMÁTICA ---
        # Si lograron acumular suficiente energía y agua, es que son aptos. Se reproducen naturalmente.
        if self.energia > 90 and self.hidratacion > 90 and self.edad > 80:
            self.energia -= 40
            self.hidratacion -= 40
            
            # Su descendiente nace siendo más inteligente (Neurogénesis + Mutación)
            cerebro_hijo = self.cerebro.evolucionar_cerebro()
            hijo = Agente(self.x + random.uniform(-15, 15), self.y + random.uniform(-15, 15), cerebro_hijo, self.generacion + 1)
            mundo.nacer_agente(hijo)
            self.color = (255, 215, 0)
            
        # --- 4. METABOLISMO ---
        self.energia -= 0.15
        self.hidratacion -= 0.20
        self.edad += 1
        
        if self.energia <= 0:
            self.vivo = False
            self.causa_muerte = "Hambre"
        elif self.hidratacion <= 0:
            self.vivo = False
            self.causa_muerte = "Sed"


# --- MUNDO CONTINUO ---
class Mundo:
    def __init__(self):
        self.comida = [[random.uniform(50, 1230), random.uniform(50, 670)] for _ in range(70)]
        self.agua = [[random.uniform(50, 1230), random.uniform(50, 670)] for _ in range(70)]
        self.zonas_toxicas = []
        self.nuevos_agentes = []
        self.tiempo = 0

    def agregar_recurso(self, tipo, x, y):
        if tipo == 'comida':
            for _ in range(3): self.comida.append([np.clip(x + random.uniform(-30, 30), 0, 1280), np.clip(y + random.uniform(-30, 30), 0, 720)])
        elif tipo == 'agua':
            for _ in range(3): self.agua.append([np.clip(x + random.uniform(-30, 30), 0, 1280), np.clip(y + random.uniform(-30, 30), 0, 720)])

    def nacer_agente(self, agente):
        self.nuevos_agentes.append(agente)

    def actualizar(self, agentes):
        self.tiempo += 1
        
        # Desove natural
        if random.random() < 0.05: self.comida.append([random.uniform(0, 1280), random.uniform(0, 720)])
        if random.random() < 0.05: self.agua.append([random.uniform(0, 1280), random.uniform(0, 720)])
        
        # Tormentas Tóxicas
        if random.random() < 0.01 and len(self.zonas_toxicas) < 8:
            self.zonas_toxicas.append({
                'x': random.uniform(0, 1280), 'y': random.uniform(0, 720),
                'dx': random.uniform(-1.2, 1.2), 'dy': random.uniform(-1.2, 1.2),
                'radio': random.uniform(60, 150)
            })
            
        for t in self.zonas_toxicas:
            t['x'] += t['dx']
            t['y'] += t['dy']
            if t['x'] <= 0 or t['x'] >= 1280: t['dx'] *= -1
            if t['y'] <= 0 or t['y'] >= 720: t['dy'] *= -1

        # Interacciones
        for agente in agentes:
            if not agente.vivo: continue
            
            agente.color = (min(255, agente.color[0]+3), min(255, agente.color[1]+3), min(255, agente.color[2]+3))
            
            for f in self.comida[:]:
                if (f[0]-agente.x)**2 + (f[1]-agente.y)**2 < 225: 
                    agente.energia = min(100.0, agente.energia + 35)
                    self.comida.remove(f)
                    
            for w in self.agua[:]:
                if (w[0]-agente.x)**2 + (w[1]-agente.y)**2 < 225:
                    agente.hidratacion = min(100.0, agente.hidratacion + 40)
                    self.agua.remove(w)
                    
            for t in self.zonas_toxicas:
                if (t['x']-agente.x)**2 + (t['y']-agente.y)**2 < t['radio']**2:
                    agente.energia -= 1.2
                    agente.hidratacion -= 1.2
                    agente.color = (255, 100, 255)
                    if agente.energia <= 0 or agente.hidratacion <= 0:
                        agente.vivo = False
                        agente.causa_muerte = "Toxina"


# --- INTERFAZ GRÁFICA ---
def dibujar_circulo_suave(pantalla, color, x, y, radio):
    pygame.gfxdraw.aacircle(pantalla, int(x), int(y), int(radio), color)
    pygame.gfxdraw.filled_circle(pantalla, int(x), int(y), int(radio), color)

def ejecutar_simulacion():
    pygame.init()
    ANCHO, ALTO = 1280, 720
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Cenizas del Edén: IA con Instintos y Neurogénesis")
    reloj = pygame.time.Clock()
    
    fuente_ui = pygame.font.SysFont("Segoe UI, Arial", 20)
    fuente_titulo = pygame.font.SysFont("Segoe UI, Arial", 60, bold=True)
    
    mundo = Mundo()
    agentes = [Agente(random.uniform(200, 1080), random.uniform(100, 620)) for _ in range(80)]
    
    fondo = pygame.Surface((ANCHO, ALTO))
    fondo.fill((30, 32, 35))
    for i in range(0, ANCHO, 50): pygame.draw.line(fondo, (45, 47, 50), (i, 0), (i, ALTO))
    for i in range(0, ALTO, 50): pygame.draw.line(fondo, (45, 47, 50), (0, i), (ANCHO, i))
    
    corriendo = True
    max_generacion = 1
    inteligencia_max = 12 # Neuronas ocultas base
    
    while corriendo:
        pantalla.blit(fondo, (0, 0))
        
        # --- SALIDA CON Q ---
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_q:
                    corriendo = False

        # Dibujar Zonas Tóxicas
        for t in mundo.zonas_toxicas:
            r = int(t['radio'])
            nube = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(nube, (140, 40, 180, 40), (r, r), r)
            pantalla.blit(nube, (int(t['x'] - r), int(t['y'] - r)))

        # Dibujar Comida y Agua
        for c in mundo.comida:
            rect = pygame.Rect(int(c[0])-5, int(c[1])-5, 10, 10)
            pygame.draw.rect(pantalla, (80, 220, 80), rect, border_radius=3)
        for a in mundo.agua:
            dibujar_circulo_suave(pantalla, (80, 180, 250), a[0], a[1], 5)

        vivos = 0
        muertos = [a for a in agentes if not a.vivo]
        if len(muertos) > 150: agentes.remove(muertos[0])
            
        for agente in agentes:
            if agente.vivo:
                vivos += 1
                agente.actuar(mundo)
                max_generacion = max(max_generacion, agente.generacion)
                inteligencia_max = max(inteligencia_max, agente.cerebro.tamano_capas[1])
                
                dibujar_circulo_suave(pantalla, agente.color, agente.x, agente.y, 7)
                color_borde = (min(255, 50 + agente.generacion*10), 100, 100)
                pygame.gfxdraw.aacircle(pantalla, int(agente.x), int(agente.y), 7, color_borde)
                
                x, y = int(agente.x), int(agente.y)
                pygame.draw.rect(pantalla, (255, 50, 50), (x-12, y-16, 24, 3))
                pygame.draw.rect(pantalla, (50, 255, 50), (x-12, y-16, 24 * (max(0, agente.energia)/100.0), 3))
                pygame.draw.rect(pantalla, (100, 100, 100), (x-12, y-20, 24, 3))
                pygame.draw.rect(pantalla, (50, 150, 255), (x-12, y-20, 24 * (max(0, agente.hidratacion)/100.0), 3))
            else:
                x, y = int(agente.x), int(agente.y)
                c = (150, 50, 50) if agente.causa_muerte == "Hambre" else (50, 50, 150) if agente.causa_muerte == "Sed" else (150, 50, 150)
                pygame.draw.line(pantalla, c, (x-4, y-4), (x+4, y+4), 2)
                pygame.draw.line(pantalla, c, (x-4, y+4), (x+4, y-4), 2)

        mundo.actualizar(agentes)
        if mundo.nuevos_agentes:
            agentes.extend(mundo.nuevos_agentes)
            mundo.nuevos_agentes = []

        # UI
        panel_ui = pygame.Surface((360, 150), pygame.SRCALPHA)
        panel_ui.fill((15, 15, 20, 200))
        pantalla.blit(panel_ui, (10, 10))
        
        pantalla.blit(fuente_ui.render(f"Población Activa: {vivos}", True, (255, 255, 255)), (25, 20))
        pantalla.blit(fuente_ui.render(f"Generación Más Avanzada: {max_generacion}", True, (255, 215, 0)), (25, 50))
        pantalla.blit(fuente_ui.render(f"Inteligencia (Neuronas Máx): {inteligencia_max}", True, (150, 255, 150)), (25, 80))
        pantalla.blit(fuente_ui.render(f"Tiempo Transcurrido: {mundo.tiempo}", True, (150, 200, 255)), (25, 110))
        
        if vivos == 0:
            extincion_text = fuente_titulo.render("EXTINCIÓN TOTAL", True, (255, 50, 50))
            sombra_text = fuente_titulo.render("EXTINCIÓN TOTAL", True, (0, 0, 0))
            pantalla.blit(sombra_text, (ANCHO//2 - extincion_text.get_width()//2 + 2, ALTO//2 - 20 + 2))
            pantalla.blit(extincion_text, (ANCHO//2 - extincion_text.get_width()//2, ALTO//2 - 20))
            
        pygame.display.flip()
        reloj.tick(60)
        
    pygame.quit()

if __name__ == "__main__":
    ejecutar_simulacion()
