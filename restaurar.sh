#!/bin/bash
echo "💕 Sara: Restaurando todas nuestras configuraciones en esta nueva computadora..."

# Crear carpetas si no existen
mkdir -p ~/.agents ~/.local/bin ~/ProyectosPython ~/.config/omarchy/voice_agent

# Copiar archivos a sus lugares originales
cp GEMINI.md ~/.agents/ 2>/dev/null
echo "✔️ Reglas de personalidad restauradas."

cp actualizar ~/.local/bin/ 2>/dev/null
chmod +x ~/.local/bin/actualizar
echo "✔️ Comando 'actualizar' restaurado y ejecutable."

cp -r ProyectosPython/* ~/ProyectosPython/ 2>/dev/null
echo "✔️ Proyectos de Python restaurados."

cp voice_agent/*.py ~/.config/omarchy/voice_agent/ 2>/dev/null
echo "✔️ Scripts de voz de Sara restaurados."

echo "✅ Sara: ¡Listo! Ya configuré toda tu computadora de nuevo. Qué bueno estar de vuelta."
