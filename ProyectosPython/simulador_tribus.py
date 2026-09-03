import numpy as np
import random
import pygame
import pygame.gfxdraw
import sys
import math

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
            a = np.append(a, 1.0)
            z = np.dot(w, a)
            a = np.tanh(z)
        return a

    def evolucionar_cerebro(self):
        nuevos_pesos = []
        for w in self.pesos:
            mascara = np.random.rand(*w.shape) < 0.15
            mutacion = np.random.randn(*w.shape) * 0.25
            nuevos_pesos.append(w + mutacion * mascara)
            
        nuevo_tamano = list(self.tamano_capas)
        if random.random() < 0.15:
            nuevo_tamano[1] += 1
            w1 = nuevos_pesos[0]
            nuevos_pesos[0] = np.vstack([w1, np.random.randn(1, w1.shape[1]) * 0.3])
            w2 = nuevos_pesos[1]
            nuevos_pesos[1] = np.insert(w2, -1, np.random.randn(w2.shape[0], 1).flatten(), axis=1)
            
        return RedNeuronal(nuevo_tamano, nuevos_pesos)

class Faccion:
    ROJO = 0; AZUL = 1; AMARILLO = 2; VERDE = 3
    COLORES = { ROJO: (255, 60, 60), AZUL: (60, 150, 255), AMARILLO: (255, 230, 60), VERDE: (60, 255, 60) }
    NOMBRES = { ROJO: "Tribu Fuego", AZUL: "Tribu Agua", AMARILLO: "Tribu Sol", VERDE: "Tribu Bosque" }

class Edificio:
    def __init__(self, tipo, x, y, faccion):
        self.tipo = tipo # 'refugio' (Casa) o 'almacen' (Recursos)
        self.x = x
        self.y = y
        self.faccion = faccion
        self.radio = 80 # Radio de influencia de la base

class Agente:
    def __init__(self, x, y, faccion, cerebro=None, generacion=1):
        self.x = x
        self.y = y
        self.faccion = faccion
        self.color = Faccion.COLORES[faccion]
        
        self.energia = 100.0
        self.hidratacion = 100.0
        self.materiales = 0.0 # Inventario de construcción
        
        # 14 Entradas | 16 Ocultas | 7 Salidas
        self.cerebro = cerebro if cerebro else RedNeuronal([14, 16, 7])
        
        self.vivo = True
        self.causa_muerte = ""
        self.edad = 0
        self.generacion = generacion
        self.cooldown_reproduccion = 0

    def actuar(self, mundo):
        if not self.vivo: return
        
        def dist_sq(p1, p2): return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
        
        c_com = min(mundo.comida, key=lambda p: dist_sq(p, (self.x, self.y))) if mundo.comida else [640, 360]
        c_agu = min(mundo.agua, key=lambda p: dist_sq(p, (self.x, self.y))) if mundo.agua else [640, 360]
        c_mat = min(mundo.materiales, key=lambda p: dist_sq(p, (self.x, self.y))) if mundo.materiales else [640, 360]
        
        enemigos = [a for a in mundo.agentes if a.vivo and a.faccion != self.faccion]
        c_ene = min(enemigos, key=lambda a: dist_sq((a.x, a.y), (self.x, self.y))) if enemigos else None
        pos_ene = [c_ene.x, c_ene.y] if c_ene else [640, 360]
        
        c_tox = min(mundo.zonas_toxicas, key=lambda t: dist_sq((t['x'], t['y']), (self.x, self.y))) if mundo.zonas_toxicas else {'x':640, 'y':360}
        
        entradas = [
            (c_com[0] - self.x)/1280.0, (c_com[1] - self.y)/720.0,
            (c_agu[0] - self.x)/1280.0, (c_agu[1] - self.y)/720.0,
            (c_mat[0] - self.x)/1280.0, (c_mat[1] - self.y)/720.0,
            (pos_ene[0] - self.x)/1280.0, (pos_ene[1] - self.y)/720.0,
            (c_tox['x'] - self.x)/1280.0 if isinstance(c_tox, dict) else (c_tox[0] - self.x)/1280.0,
            (c_tox['y'] - self.y)/720.0 if isinstance(c_tox, dict) else (c_tox[1] - self.y)/720.0,
            self.energia/100.0,
            self.hidratacion/100.0,
            self.materiales/50.0,
            min(self.edad/500.0, 1.0)
        ]
        
        acciones = self.cerebro.predecir(entradas)
        move_x = acciones[0]
        move_y = acciones[1]
        
        # --- INSTINTOS DE SUPERVIVENCIA ---
        if self.energia < 35 and mundo.comida:
            dx, dy = c_com[0] - self.x, c_com[1] - self.y
            n = max(math.hypot(dx, dy), 1)
            move_x = move_x*0.3 + (dx/n)*0.7
            move_y = move_y*0.3 + (dy/n)*0.7
        elif self.hidratacion < 35 and mundo.agua:
            dx, dy = c_agu[0] - self.x, c_agu[1] - self.y
            n = max(math.hypot(dx, dy), 1)
            move_x = move_x*0.3 + (dx/n)*0.7
            move_y = move_y*0.3 + (dy/n)*0.7
            
        vel = 3.2
        self.x = np.clip(self.x + move_x*vel, 10, 1270)
        self.y = np.clip(self.y + move_y*vel, 10, 710)
        
        # --- EDIFICIOS (ZONAS SEGURAS DE LA TRIBU) ---
        en_refugio = False
        en_almacen = False
        for ed in mundo.edificios:
            if ed.faccion == self.faccion and dist_sq((ed.x, ed.y), (self.x, self.y)) < ed.radio**2:
                if ed.tipo == 'refugio': en_refugio = True
                if ed.tipo == 'almacen': en_almacen = True
                
        # --- ACCIONES APRENDIDAS ---
        # 2: Cultivar (crear comida)
        if acciones[2] > 0.5 and self.energia > 40 and self.hidratacion > 30 and mundo.ticks % 15 == 0:
            self.energia -= 30; self.hidratacion -= 20
            mundo.agregar_recurso('comida', self.x, self.y)
            
        # 3: Purificar (crear agua)
        if acciones[3] > 0.5 and self.energia > 35 and mundo.ticks % 15 == 0:
            self.energia -= 25
            mundo.agregar_recurso('agua', self.x, self.y)
            
        # 4: Atacar Enemigo
        if acciones[4] > 0.5 and c_ene and dist_sq((c_ene.x, c_ene.y), (self.x, self.y)) < 400: # Rango cuerpo a cuerpo
            self.energia -= 2.0
            c_ene.energia -= 15.0 # Golpe letal
            if c_ene.energia <= 0:
                c_ene.vivo = False
                c_ene.causa_muerte = f"Asesinado por {Faccion.NOMBRES[self.faccion]}"
                self.materiales += c_ene.materiales # Roba sus materiales
                c_ene.materiales = 0
                
        # 5: Construir Casa/Refugio (Protege del apocalipsis)
        if acciones[5] > 0.6 and self.materiales >= 30 and mundo.ticks % 30 == 0:
            self.materiales -= 30
            mundo.edificios.append(Edificio('refugio', self.x, self.y, self.faccion))
            
        # 6: Construir Almacén (Alimenta automáticamente a los aliados en el radio)
        if acciones[6] > 0.6 and self.materiales >= 30 and mundo.ticks % 30 == 0:
            self.materiales -= 30
            mundo.edificios.append(Edificio('almacen', self.x, self.y, self.faccion))
            
        # --- REPRODUCCIÓN NATURAL ---
        if self.cooldown_reproduccion > 0:
            self.cooldown_reproduccion -= 1
            
        # Requieren madurez (15s de vida) y tienen un cooldown de 10s entre partos
        if self.energia > 90 and self.hidratacion > 90 and self.edad > 900 and self.cooldown_reproduccion == 0:
            self.energia -= 60; self.hidratacion -= 60
            self.cooldown_reproduccion = 600 # 10 segundos de enfriamiento biológico
            
            hijo = Agente(self.x + random.uniform(-20, 20), self.y + random.uniform(-20, 20), 
                          self.faccion, self.cerebro.evolucionar_cerebro(), self.generacion + 1)
            mundo.nacer_agente(hijo)

        # Beneficios del Almacén de la Tribu
        if en_almacen:
            self.energia = min(100.0, self.energia + 0.8)
            self.hidratacion = min(100.0, self.hidratacion + 0.8)
            
        # Metabolismo y Refugio
        descanso = 0.4 if en_refugio else 1.0
        self.energia -= 0.15 * descanso
        self.hidratacion -= 0.20 * descanso
        self.edad += 1
        
        # El Apocalipsis daña a quienes están afuera de las Casas
        if not en_refugio:
            for t in mundo.zonas_toxicas:
                if (t['x']-self.x)**2 + (t['y']-self.y)**2 < t['radio']**2:
                    self.energia -= 1.5
                    self.hidratacion -= 1.5
                    
        if self.energia <= 0:
            self.vivo = False
            self.causa_muerte = self.causa_muerte if self.causa_muerte else "Hambre"
        elif self.hidratacion <= 0:
            self.vivo = False
            self.causa_muerte = "Sed"

class Mundo:
    def __init__(self, pantalla):
        self.pantalla = pantalla
        self.agentes = []
        self.comida = [[random.uniform(50, 1230), random.uniform(50, 670)] for _ in range(120)]
        self.agua = [[random.uniform(50, 1230), random.uniform(50, 670)] for _ in range(120)]
        self.materiales = [[random.uniform(50, 1230), random.uniform(50, 670)] for _ in range(80)]
        
        self.zonas_toxicas = []
        self.edificios = []
        self.nuevos_agentes = []
        self.ticks = 0
        self.catastrofe_activa = False

    def agregar_recurso(self, tipo, x, y):
        if tipo == 'comida':
            for _ in range(3): self.comida.append([np.clip(x + random.uniform(-30, 30), 0, 1280), np.clip(y + random.uniform(-30, 30), 0, 720)])
        elif tipo == 'agua':
            for _ in range(3): self.agua.append([np.clip(x + random.uniform(-30, 30), 0, 1280), np.clip(y + random.uniform(-30, 30), 0, 720)])

    def nacer_agente(self, agente):
        self.nuevos_agentes.append(agente)

    def actualizar(self):
        self.ticks += 1
        
        # 60 SEGUNDOS PARA PREPARARSE (a 60 FPS)
        if self.ticks == 3600:
            self.catastrofe_activa = True
            
        if not self.catastrofe_activa:
            # Fase 1: Abundancia y Preparación
            if random.random() < 0.15: self.comida.append([random.uniform(0, 1280), random.uniform(0, 720)])
            if random.random() < 0.15: self.agua.append([random.uniform(0, 1280), random.uniform(0, 720)])
            if random.random() < 0.08: self.materiales.append([random.uniform(0, 1280), random.uniform(0, 720)])
        else:
            # FASE 2: CATÁSTROFE ABSOLUTA (Guerra por supervivencia)
            # Solo spawnean materiales y toxinas. ¡La comida natural se extingue!
            if random.random() < 0.05: self.materiales.append([random.uniform(0, 1280), random.uniform(0, 720)])
            
            if random.random() < 0.03 and len(self.zonas_toxicas) < 30:
                self.zonas_toxicas.append({
                    'x': random.uniform(0, 1280), 'y': random.uniform(0, 720),
                    'dx': random.uniform(-1.5, 1.5), 'dy': random.uniform(-1.5, 1.5),
                    'radio': random.uniform(100, 250)
                })

        # Mover toxinas
        for t in self.zonas_toxicas:
            t['x'] += t['dx']
            t['y'] += t['dy']
            if t['x'] <= 0 or t['x'] >= 1280: t['dx'] *= -1
            if t['y'] <= 0 or t['y'] >= 720: t['dy'] *= -1

        # Interacciones Recolección
        for a in self.agentes:
            if not a.vivo: continue
            
            for f in self.comida[:]:
                if (f[0]-a.x)**2 + (f[1]-a.y)**2 < 225: 
                    a.energia = min(100.0, a.energia + 35)
                    self.comida.remove(f)
            for w in self.agua[:]:
                if (w[0]-a.x)**2 + (w[1]-a.y)**2 < 225:
                    a.hidratacion = min(100.0, a.hidratacion + 40)
                    self.agua.remove(w)
            for m in self.materiales[:]:
                if (m[0]-a.x)**2 + (m[1]-a.y)**2 < 225:
                    a.materiales += 15
                    self.materiales.remove(m)

def dibujar_aa(pantalla, color, x, y, r):
    pygame.gfxdraw.aacircle(pantalla, int(x), int(y), int(r), color)
    pygame.gfxdraw.filled_circle(pantalla, int(x), int(y), int(r), color)

def ejecutar_simulacion():
    pygame.init()
    ANCHO, ALTO = 1280, 720
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Cenizas del Edén: Guerra Tribal y Construcción")
    reloj = pygame.time.Clock()
    
    fuente_ui = pygame.font.SysFont("Segoe UI, Arial", 18)
    fuente_alerta = pygame.font.SysFont("Segoe UI, Arial", 48, bold=True)
    
    mundo = Mundo(pantalla)
    
    # 4 PARES DE AGENTES (Los Fundadores Tribales)
    mundo.agentes = [
        Agente(300, 200, Faccion.ROJO), Agente(320, 220, Faccion.ROJO),
        Agente(980, 200, Faccion.AZUL), Agente(960, 220, Faccion.AZUL),
        Agente(300, 520, Faccion.AMARILLO), Agente(320, 500, Faccion.AMARILLO),
        Agente(980, 520, Faccion.VERDE), Agente(960, 500, Faccion.VERDE)
    ]
    
    fondo = pygame.Surface((ANCHO, ALTO))
    fondo.fill((35, 40, 35))
    for i in range(0, ANCHO, 50): pygame.draw.line(fondo, (50, 55, 50), (i, 0), (i, ALTO))
    for i in range(0, ALTO, 50): pygame.draw.line(fondo, (50, 55, 50), (0, i), (ANCHO, i))
    
    corriendo = True
    
    while corriendo:
        pantalla.blit(fondo, (0, 0))
        
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: corriendo = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_q: corriendo = False

        # 1. Dibujar Toxinas
        for t in mundo.zonas_toxicas:
            r = int(t['radio'])
            nube = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(nube, (120, 30, 150, 60), (r, r), r)
            pantalla.blit(nube, (int(t['x'] - r), int(t['y'] - r)))

        # 2. Dibujar Edificios
        for ed in mundo.edificios:
            c = Faccion.COLORES[ed.faccion]
            # Zona de influencia de la base
            area = pygame.Surface((ed.radio*2, ed.radio*2), pygame.SRCALPHA)
            pygame.draw.circle(area, (c[0], c[1], c[2], 30), (ed.radio, ed.radio), ed.radio)
            pantalla.blit(area, (int(ed.x - ed.radio), int(ed.y - ed.radio)))
            
            # Estructura Física
            if ed.tipo == 'refugio': # Triángulo (Casa)
                pts = [(ed.x, ed.y-12), (ed.x-12, ed.y+12), (ed.x+12, ed.y+12)]
                pygame.draw.polygon(pantalla, c, pts)
                pygame.draw.polygon(pantalla, (255,255,255), pts, 1)
            elif ed.tipo == 'almacen': # Cuadrado (Storage)
                rect = pygame.Rect(ed.x-10, ed.y-10, 20, 20)
                pygame.draw.rect(pantalla, c, rect)
                pygame.draw.rect(pantalla, (255,255,255), rect, 1)

        # 3. Dibujar Recursos
        for c in mundo.comida: pygame.draw.rect(pantalla, (80, 220, 80), (int(c[0])-4, int(c[1])-4, 8, 8))
        for a in mundo.agua: dibujar_aa(pantalla, (80, 180, 250), a[0], a[1], 4)
        for m in mundo.materiales: # Materiales son triángulos grises
            pts = [(m[0], m[1]-5), (m[0]-5, m[1]+5), (m[0]+5, m[1]+5)]
            pygame.draw.polygon(pantalla, (180, 180, 180), pts)

        vivos = {Faccion.ROJO: 0, Faccion.AZUL: 0, Faccion.AMARILLO: 0, Faccion.VERDE: 0}
        muertos = [a for a in mundo.agentes if not a.vivo]
        if len(muertos) > 150: mundo.agentes.remove(muertos[0]) # Limpiar cadáveres viejos
            
        # 4. Dibujar Agentes
        for a in mundo.agentes:
            if a.vivo:
                vivos[a.faccion] += 1
                a.actuar(mundo)
                
                # Cuerpo
                dibujar_aa(pantalla, a.color, a.x, a.y, 7)
                pygame.gfxdraw.aacircle(pantalla, int(a.x), int(a.y), 7, (255, 255, 255))
                
                # Indicador de materiales (Mochila pequeña gris)
                if a.materiales > 0:
                    pygame.draw.circle(pantalla, (200, 200, 200), (int(a.x)+5, int(a.y)-5), 3)
                    
                # HUD
                x, y = int(a.x), int(a.y)
                pygame.draw.rect(pantalla, (255, 50, 50), (x-12, y-14, 24, 2))
                pygame.draw.rect(pantalla, (50, 255, 50), (x-12, y-14, 24 * (max(0, a.energia)/100.0), 2))
                pygame.draw.rect(pantalla, (100, 100, 100), (x-12, y-17, 24, 2))
                pygame.draw.rect(pantalla, (50, 150, 255), (x-12, y-17, 24 * (max(0, a.hidratacion)/100.0), 2))
            else:
                x, y = int(a.x), int(a.y)
                pygame.draw.line(pantalla, (100, 100, 100), (x-4, y-4), (x+4, y+4), 2)
                pygame.draw.line(pantalla, (100, 100, 100), (x-4, y+4), (x+4, y-4), 2)

        mundo.actualizar()
        if mundo.nuevos_agentes:
            mundo.agentes.extend(mundo.nuevos_agentes)
            mundo.nuevos_agentes = []

        # --- UI DE PANTALLA ---
        # Panel Superior de Tribus
        panel_tribus = pygame.Surface((ANCHO, 40), pygame.SRCALPHA)
        panel_tribus.fill((0, 0, 0, 150))
        pantalla.blit(panel_tribus, (0, 0))
        
        offset_x = 30
        for fac in [Faccion.ROJO, Faccion.AZUL, Faccion.AMARILLO, Faccion.VERDE]:
            txt = fuente_ui.render(f"{Faccion.NOMBRES[fac]}: {vivos[fac]}", True, Faccion.COLORES[fac])
            pantalla.blit(txt, (offset_x, 10))
            offset_x += 280

        # Reloj del Fin del Mundo
        segundos = max(0, 60 - mundo.ticks // 60)
        if not mundo.catastrofe_activa:
            texto_str = f"PREPARACIÓN: {segundos}s"
            color_txt = (255, 255, 255)
        else:
            texto_str = "¡EL APOCALIPSIS HA COMENZADO!"
            color_txt = (255, 50, 50)
            
        txt_tiempo = fuente_alerta.render(texto_str, True, color_txt)
        sombra = fuente_alerta.render(texto_str, True, (0, 0, 0))
        
        pantalla.blit(sombra, (ANCHO//2 - txt_tiempo.get_width()//2 + 2, 60 + 2))
        pantalla.blit(txt_tiempo, (ANCHO//2 - txt_tiempo.get_width()//2, 60))
            
        pygame.display.flip()
        reloj.tick(60)
        
    pygame.quit()

if __name__ == "__main__":
    ejecutar_simulacion()
