#!/bin/bash
MENSAJE=$1
echo "[$(date)] NUEVO COMANDO PARA SARA: $MENSAJE" >> ~/ProyectosPython/sara_urgente.txt
notify-send -u critical -a "Sara" "Sara" "Yuna me avisa: $MENSAJE"
