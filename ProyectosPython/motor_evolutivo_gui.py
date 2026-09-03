import numpy as np
import random
import pygame
import sys

# --- RED NEURONAL Y CEREBRO ---
class RedNeuronal:
    def __init__(self, tamano_capas, pesos=None):
        self.tamano_capas = tamano_capas
        if pesos is None:
            self.pesos = [np.random.randn(y, x + 1) * 0.1 for x, y in zip(tamano_capas[:-1], tamano_capas[1:])]
        else:
            self.pesos = pesos

    def predecir(self, entradas):
        a = np.array(entradas)
        for w in self.pesos:
            a = np.append(a, 1.0)
            z = np.dot(w, a)
            a = np.tanh(z)
        return a

    def mutar(self, tasa_mutacion=0.15, escala_mutacion=0.3):
        nuevos_pesos = []
        for w in self.pesos:
            mascara_mutacion = np.random.rand(*w.shape) < tasa_mutacion
            mutacion = np.random.randn(*w.shape) * escala_mutacion
            nuevos_pesos.append(w + mutacion * mascara_mutacion)
        return RedNeuronal(self.tamano_capas, nuevos_pesos)

    def cruzar(self, otro):
        nuevos_pesos = []
        for w1, w2 in zip(self.pesos, otro.pesos):
            mascara = np.random.rand(*w1.shape) < 0.5
            nuevo_w = np.where(mascara, w1, w2)
            nuevos_pesos.append(nuevo_w)
        return RedNeuronal(self.tamano_capas, nuevos_pesos)


# --- AGENTE Y LÓGICA DE SUPERVIVENCIA ---
class Agente:
    def __init__(self, cerebro=None):
        self.x = random.uniform(5, 95)
        self.y = random.uniform(5, 95)
        self.energia = 100.0
        self.hidratacion = 100.0
        
        self.cerebro = cerebro if cerebro else RedNeuronal([8, 12, 2])
        
        self.vivo = True
        self.causa_muerte = ""
        self.fitness = 0.0
        self.edad = 0
        self.color = (200, 200, 200) # Color normal

    def actuar(self, estado_entorno):
        if not self.vivo: return
        
        c_comida = estado_entorno['comida_cercana']
        c_agua = estado_entorno['agua_cercana']
        c_toxico = estado_entorno['toxico_cercano']
        
        entradas = [
            (c_comida[0] - self.x) / 100.0, (c_comida[1] - self.y) / 100.0,
            (c_agua[0] - self.x) / 100.0, (c_agua[1] - self.y) / 100.0,
            (c_toxico[0] - self.x) / 100.0, (c_toxico[1] - self.y) / 100.0,
            self.energia / 100.0,
            self.hidratacion / 100.0
        ]
        
        acciones = self.cerebro.predecir(entradas)
        
        velocidad_maxima = 1.5
        self.x += acciones[0] * velocidad_maxima
        self.y += acciones[1] * velocidad_maxima
        
        self.x = np.clip(self.x, 0, 100)
        self.y = np.clip(self.y, 0, 100)
        
        # Gasto de energía por existir y moverse
        self.energia -= 0.3
        self.hidratacion -= 0.5
        self.edad += 1
        self.fitness += 1.0 
        
        if self.energia <= 0:
            self.vivo = False
            self.causa_muerte = "Hambre"
        elif self.hidratacion <= 0:
            self.vivo = False
            self.causa_muerte = "Sed"


# --- ENTORNO ---
class Mundo:
    def __init__(self, generacion):
        num_comida = max(10, 40 - int(generacion * 0.5))
        num_agua = max(10, 40 - int(generacion * 0.5))
        
        self.comida = [(random.uniform(2, 98), random.uniform(2, 98)) for _ in range(num_comida)]
        self.agua = [(random.uniform(2, 98), random.uniform(2, 98)) for _ in range(num_agua)]
        
        num_toxicos = generacion // 4 + 1
        self.zonas_toxicas = [(random.uniform(5, 95), random.uniform(5, 95)) for _ in range(num_toxicos)]
        self.radio_toxico = 4.0 + (generacion * 0.3)

    def obtener_estado_para(self, agente):
        def mas_cercano(items):
            if not items: return (50.0, 50.0)
            return min(items, key=lambda p: (p[0]-agente.x)**2 + (p[1]-agente.y)**2)
            
        return {
            'comida_cercana': mas_cercano(self.comida),
            'agua_cercana': mas_cercano(self.agua),
            'toxico_cercano': mas_cercano(self.zonas_toxicas)
        }

    def actualizar(self, agentes):
        for agente in agentes:
            if not agente.vivo: continue
            
            # Resetear color a blanco (normal)
            agente.color = (255, 255, 255)

            # Colisión con Comida
            for f in self.comida[:]:
                if (f[0]-agente.x)**2 + (f[1]-agente.y)**2 < 4:
                    agente.energia = min(100.0, agente.energia + 40)
                    agente.fitness += 20
                    self.comida.remove(f)
                    agente.color = (50, 255, 50) # Brillar verde al comer
                    
            # Colisión con Agua
            for w in self.agua[:]:
                if (w[0]-agente.x)**2 + (w[1]-agente.y)**2 < 4:
                    agente.hidratacion = min(100.0, agente.hidratacion + 50)
                    agente.fitness += 20
                    self.agua.remove(w)
                    agente.color = (50, 150, 255) # Brillar azul al beber
                    
            # Colisión con Tormentas Tóxicas
            for t in self.zonas_toxicas:
                if (t[0]-agente.x)**2 + (t[1]-agente.y)**2 < self.radio_toxico**2:
                    agente.energia -= 2.0
                    agente.hidratacion -= 2.0
                    agente.fitness -= 2.0
                    agente.color = (200, 50, 200) # Brillar violeta por el daño
                    
                    if agente.energia <= 0 or agente.hidratacion <= 0:
                        agente.vivo = False
                        agente.causa_muerte = "Toxina"


# --- MOTOR GRÁFICO (PYGAME) ---
class MotorVisual:
    def __init__(self, tamano_poblacion=100):
        pygame.init()
        self.ANCHO = 800
        self.ALTO = 800
        self.escala = self.ANCHO / 100.0 # Escalamos de 100x100 a 800x800 píxeles
        self.pantalla = pygame.display.set_mode((self.ANCHO, self.ALTO))
        pygame.display.set_caption("Cenizas del Edén - IA Evolutiva")
        self.reloj = pygame.time.Clock()
        
        self.fuente = pygame.font.SysFont("Arial", 16)
        self.fuente_grande = pygame.font.SysFont("Arial", 22, bold=True)
        
        self.tamano_poblacion = tamano_poblacion
        self.agentes = [Agente() for _ in range(tamano_poblacion)]
        self.generacion = 0

    def dibujar_mundo(self, mundo, ticks, generacion):
        self.pantalla.fill((25, 25, 30)) # Fondo sombrío
        
        # 1. Dibujar Tormentas Tóxicas (con transparencia)
        for t in mundo.zonas_toxicas:
            x = int(t[0] * self.escala)
            y = int(t[1] * self.escala)
            radio = int(mundo.radio_toxico * self.escala)
            nube = pygame.Surface((radio*2, radio*2), pygame.SRCALPHA)
            pygame.draw.circle(nube, (150, 50, 200, 70), (radio, radio), radio)
            self.pantalla.blit(nube, (x - radio, y - radio))

        # 2. Dibujar Comida (Verde)
        for c in mundo.comida:
            x = int(c[0] * self.escala)
            y = int(c[1] * self.escala)
            pygame.draw.rect(self.pantalla, (50, 200, 50), (x-4, y-4, 8, 8))

        # 3. Dibujar Agua (Azul Celeste)
        for a in mundo.agua:
            x = int(a[0] * self.escala)
            y = int(a[1] * self.escala)
            pygame.draw.circle(self.pantalla, (50, 150, 250), (x, y), 5)

        # 4. Dibujar Agentes
        vivos = 0
        muertos_hambre = 0
        muertos_sed = 0
        muertos_toxina = 0
        
        for agente in self.agentes:
            x = int(agente.x * self.escala)
            y = int(agente.y * self.escala)
            
            if agente.vivo:
                vivos += 1
                # Cuerpo del agente
                pygame.draw.circle(self.pantalla, agente.color, (x, y), 7)
                
                # Barras de estado visual (Salud y Agua)
                # Barra Energía (Verde)
                pygame.draw.rect(self.pantalla, (255, 0, 0), (x-12, y-16, 24, 4))
                pygame.draw.rect(self.pantalla, (0, 255, 0), (x-12, y-16, 24 * (max(0, agente.energia)/100.0), 4))
                
                # Barra Hidratación (Azul)
                pygame.draw.rect(self.pantalla, (255, 0, 0), (x-12, y-21, 24, 4))
                pygame.draw.rect(self.pantalla, (0, 150, 255), (x-12, y-21, 24 * (max(0, agente.hidratacion)/100.0), 4))
            else:
                # Agente Muerto (Dibujar una 'X' del color de la causa de muerte)
                if agente.causa_muerte == "Hambre":
                    color_muerte = (180, 50, 50)
                    muertos_hambre += 1
                elif agente.causa_muerte == "Sed":
                    color_muerte = (50, 50, 180)
                    muertos_sed += 1
                elif agente.causa_muerte == "Toxina":
                    color_muerte = (150, 50, 150)
                    muertos_toxina += 1
                else:
                    color_muerte = (100, 100, 100)
                
                # Dibujar la cruz
                pygame.draw.line(self.pantalla, color_muerte, (x-5, y-5), (x+5, y+5), 3)
                pygame.draw.line(self.pantalla, color_muerte, (x-5, y+5), (x+5, y-5), 3)

        # 5. UI de Información en Pantalla
        textos = [
            self.fuente_grande.render(f"GENERACIÓN: {generacion}", True, (255, 255, 255)),
            self.fuente.render(f"Supervivientes: {vivos} / {self.tamano_poblacion}", True, (200, 200, 200)),
            self.fuente.render(f"Día (Ticks): {ticks}/600", True, (200, 200, 200))
        ]
        
        for i, texto in enumerate(textos):
            self.pantalla.blit(texto, (15, 15 + (i * 25)))
        
        # 6. Estadísticas de Decesos
        y_muertes = self.ALTO - 90
        self.pantalla.blit(self.fuente.render(f"X Muertos por Hambre: {muertos_hambre}", True, (180, 50, 50)), (15, y_muertes))
        self.pantalla.blit(self.fuente.render(f"X Muertos por Sed: {muertos_sed}", True, (50, 50, 180)), (15, y_muertes + 25))
        self.pantalla.blit(self.fuente.render(f"X Muertos por Toxinas: {muertos_toxina}", True, (150, 50, 150)), (15, y_muertes + 50))

        pygame.display.flip()
        return vivos

    def evolucionar(self):
        self.agentes.sort(key=lambda a: a.fitness, reverse=True)
        
        nuevos_agentes = []
        elite = int(self.tamano_poblacion * 0.1) # 10% mejores
        nuevos_agentes.extend([Agente(a.cerebro) for a in self.agentes[:elite]])
        
        while len(nuevos_agentes) < self.tamano_poblacion:
            padre1 = random.choice(self.agentes[:self.tamano_poblacion // 2])
            padre2 = random.choice(self.agentes[:self.tamano_poblacion // 2])
            cerebro_hijo = padre1.cerebro.cruzar(padre2.cerebro).mutar()
            nuevos_agentes.append(Agente(cerebro_hijo))
            
        self.agentes = nuevos_agentes
        self.generacion += 1

    def ejecutar(self):
        corriendo = True
        
        while corriendo:
            mundo = Mundo(self.generacion)
            ticks = 0
            
            while ticks < 600:
                # Eventos del sistema (cerrar la ventana con la X)
                for evento in pygame.event.get():
                    if evento.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                        
                vivos = 0
                for agente in self.agentes:
                    if agente.vivo:
                        vivos += 1
                        estado = mundo.obtener_estado_para(agente)
                        agente.actuar(estado)
                
                mundo.actualizar(self.agentes)
                self.dibujar_mundo(mundo, ticks, self.generacion)
                
                # Controlar la velocidad de la simulación (FPS)
                self.reloj.tick(60) 
                
                ticks += 1
                if vivos == 0: # Si todos mueren, forzar siguiente generación
                    break 
                    
            self.evolucionar()

if __name__ == "__main__":
    motor = MotorVisual(tamano_poblacion=100)
    motor.ejecutar()
