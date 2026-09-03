import numpy as np
import random
import math
import time

class RedNeuronal:
    """Cerebro del agente basado en un Perceptrón Multicapa."""
    def __init__(self, tamano_capas, pesos=None):
        self.tamano_capas = tamano_capas
        if pesos is None:
            # Inicialización de pesos aleatorios con distribución normal
            self.pesos = [np.random.randn(y, x + 1) * 0.1 for x, y in zip(tamano_capas[:-1], tamano_capas[1:])]
        else:
            self.pesos = pesos

    def predecir(self, entradas):
        """Pase hacia adelante (Forward pass)."""
        a = np.array(entradas)
        for w in self.pesos:
            a = np.append(a, 1.0) # Añadir bias de 1.0
            z = np.dot(w, a)
            a = np.tanh(z) # Función de activación para salidas entre -1 y 1
        return a

    def mutar(self, tasa_mutacion=0.15, escala_mutacion=0.3):
        """Aplica mutaciones aleatorias a los pesos (Evolución)."""
        nuevos_pesos = []
        for w in self.pesos:
            mascara_mutacion = np.random.rand(*w.shape) < tasa_mutacion
            mutacion = np.random.randn(*w.shape) * escala_mutacion
            nuevos_pesos.append(w + mutacion * mascara_mutacion)
        return RedNeuronal(self.tamano_capas, nuevos_pesos)

    def cruzar(self, otro):
        """Cruza los genes (pesos) con otro agente (Reproducción)."""
        nuevos_pesos = []
        for w1, w2 in zip(self.pesos, otro.pesos):
            # 50% de probabilidad de heredar el gen (peso) de cada padre
            mascara = np.random.rand(*w1.shape) < 0.5
            nuevo_w = np.where(mascara, w1, w2)
            nuevos_pesos.append(nuevo_w)
        return RedNeuronal(self.tamano_capas, nuevos_pesos)


class Agente:
    """Sobreviviente en el mundo post-apocalíptico."""
    def __init__(self, cerebro=None):
        self.x = random.uniform(0, 100)
        self.y = random.uniform(0, 100)
        self.energia = 100.0
        self.hidratacion = 100.0
        
        # Arquitectura de la red:
        # Entradas: 8 sentidos | Ocultas: 12 neuronas | Salidas: 2 acciones (dx, dy)
        self.cerebro = cerebro if cerebro else RedNeuronal([8, 12, 2])
        
        self.vivo = True
        self.fitness = 0.0 # Métrica de éxito general
        self.edad = 0

    def actuar(self, estado_entorno):
        if not self.vivo: return
        
        c_comida = estado_entorno['comida_cercana']
        c_agua = estado_entorno['agua_cercana']
        c_toxico = estado_entorno['toxico_cercano']
        
        # Los 'sentidos' son normalizados para la red neuronal
        entradas = [
            (c_comida[0] - self.x) / 100.0, (c_comida[1] - self.y) / 100.0,
            (c_agua[0] - self.x) / 100.0, (c_agua[1] - self.y) / 100.0,
            (c_toxico[0] - self.x) / 100.0, (c_toxico[1] - self.y) / 100.0,
            self.energia / 100.0,
            self.hidratacion / 100.0
        ]
        
        # La red neuronal toma la decisión (Motor de inferencia)
        acciones = self.cerebro.predecir(entradas)
        
        # Interpretar las salidas para el movimiento
        velocidad_maxima = 2.5
        self.x += acciones[0] * velocidad_maxima
        self.y += acciones[1] * velocidad_maxima
        
        # Restricciones físicas (Muros del mundo de 100x100)
        self.x = np.clip(self.x, 0, 100)
        self.y = np.clip(self.y, 0, 100)
        
        # Metabolismo y envejecimiento
        self.energia -= 0.6
        self.hidratacion -= 0.9
        self.edad += 1
        
        # Sobrevivir suma puntos pasivamente
        self.fitness += 1.0 
        
        if self.energia <= 0 or self.hidratacion <= 0:
            self.vivo = False


class Mundo:
    """El entorno hostil, dinámico y en degradación."""
    def __init__(self, generacion):
        # Escasez progresiva: Menos recursos a medida que avanzan las generaciones
        num_comida = max(5, 50 - int(generacion * 0.8))
        num_agua = max(5, 50 - int(generacion * 0.8))
        
        self.comida = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(num_comida)]
        self.agua = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(num_agua)]
        
        # Peligro progresivo: Tormentas de esporas tóxicas crecen en tamaño y cantidad
        num_toxicos = generacion // 3 + 1
        self.zonas_toxicas = [(random.uniform(0, 100), random.uniform(0, 100)) for _ in range(num_toxicos)]
        self.radio_toxico = 4.0 + (generacion * 0.4)

    def obtener_estado_para(self, agente):
        """Genera el 'cono de visión/olfato' para un agente en particular."""
        def mas_cercano(items):
            if not items: return (50.0, 50.0) # Si se acaba, apuntan al centro
            return min(items, key=lambda p: (p[0]-agente.x)**2 + (p[1]-agente.y)**2)
            
        return {
            'comida_cercana': mas_cercano(self.comida),
            'agua_cercana': mas_cercano(self.agua),
            'toxico_cercano': mas_cercano(self.zonas_toxicas)
        }

    def actualizar(self, agentes):
        """Evalúa las colisiones e interacciones físicas en el entorno."""
        for agente in agentes:
            if not agente.vivo: continue
            
            # Recolección de comida (Radio de recolección = 2 unidades)
            for f in self.comida[:]:
                if (f[0]-agente.x)**2 + (f[1]-agente.y)**2 < 4:
                    agente.energia = min(100.0, agente.energia + 40)
                    agente.fitness += 25 # Recompensa evolutiva por comer
                    self.comida.remove(f)
                    
            # Recolección de agua
            for w in self.agua[:]:
                if (w[0]-agente.x)**2 + (w[1]-agente.y)**2 < 4:
                    agente.hidratacion = min(100.0, agente.hidratacion + 50)
                    agente.fitness += 25
                    self.agua.remove(w)
                    
            # Daño ambiental: Entrar a una tormenta de esporas tóxicas
            for t in self.zonas_toxicas:
                if (t[0]-agente.x)**2 + (t[1]-agente.y)**2 < self.radio_toxico**2:
                    agente.energia -= 8.0
                    agente.hidratacion -= 8.0
                    agente.fitness -= 3.0 # Castigo genético


class MotorEvolutivo:
    """Núcleo del algoritmo genético que coordina el ecosistema."""
    def __init__(self, tamano_poblacion=150):
        self.tamano_poblacion = tamano_poblacion
        self.agentes = [Agente() for _ in range(tamano_poblacion)]
        self.generacion = 0
        
    def simular_generacion(self):
        mundo = Mundo(self.generacion)
        ticks = 0
        
        # Simulamos hasta que mueren todos o hasta un máximo de ticks (Día de ciclo)
        while any(a.vivo for a in self.agentes) and ticks < 600:
            for agente in self.agentes:
                if agente.vivo:
                    estado = mundo.obtener_estado_para(agente)
                    agente.actuar(estado)
            mundo.actualizar(self.agentes)
            ticks += 1
            
        self.evolucionar()
        
    def evolucionar(self):
        # Clasificar a los agentes por su adaptabilidad (Fitness)
        self.agentes.sort(key=lambda a: a.fitness, reverse=True)
        
        mejor_fitness = self.agentes[0].fitness
        fitness_promedio = sum(a.fitness for a in self.agentes) / self.tamano_poblacion
        supervivencia_max = max(a.edad for a in self.agentes)
        
        print(f"Gen {self.generacion:03d} | Ticks Sobrevividos: {supervivencia_max:03d} | "
              f"Fitness Máx: {mejor_fitness:>7.1f} | Fitness Prom: {fitness_promedio:>7.1f}")
        
        nuevos_agentes = []
        
        # 1. Elitismo: Los campeones de la generación pasan intactos a la siguiente
        elite = int(self.tamano_poblacion * 0.1)
        nuevos_agentes.extend([Agente(a.cerebro) for a in self.agentes[:elite]])
        
        # 2. Selección Natural y Crossover
        while len(nuevos_agentes) < self.tamano_poblacion:
            # Torneo simple: elegir padres sesgados hacia los que tienen mejor fitness (mitad superior)
            padre1 = random.choice(self.agentes[:self.tamano_poblacion // 2])
            padre2 = random.choice(self.agentes[:self.tamano_poblacion // 2])
            
            # Cruzar y mutar su genoma neuronal
            cerebro_hijo = padre1.cerebro.cruzar(padre2.cerebro).mutar()
            nuevos_agentes.append(Agente(cerebro_hijo))
            
        self.agentes = nuevos_agentes
        self.generacion += 1

if __name__ == "__main__":
    print("=====================================================")
    print("=== INICIANDO MOTOR EVOLUTIVO: CENIZAS DEL EDÉN ===")
    print("=====================================================")
    print("- Mecánicas: Escasez estacional y Tormentas de Esporas.")
    print("- IA: Neuroevolución (MLP propagación + Genética)")
    print("-----------------------------------------------------")
    
    simulacion = MotorEvolutivo(tamano_poblacion=150)
    try:
        while True: # Bucle infinito (El apocalipsis no tiene fin)
            simulacion.simular_generacion()
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n\nSimulación abortada por el usuario. La humanidad se ha extinguido.")
