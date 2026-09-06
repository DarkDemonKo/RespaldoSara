#!/bin/bash
URL=$1
wget -q -P ~/Descargas/ "$URL"
notify-send -a "Sara" "Sara" "Descarga completada en ~/Descargas/"
