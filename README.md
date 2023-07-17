# Prototipo 1

Este script detecta markers ArUco para animales e inserta detecciones en la base de datos especificada.

Dependencias:

- ```opencv-python``` 
- ```psycopg2```

La dependencias pueden ser instaladas con:

```
pip install -r requirements.txt
```

Uso:

```
usage: main.py [-h] [--width WIDTH] [--height HEIGHT] [--headless] [--db DB] device

Ejecuta el detector de etiquetas de ganado

positional arguments:
  device           el dispositivo de captura de video (ej. /dev/video0)

options:
  -h, --help       show this help message and exit
  --width WIDTH    el ancho de la imagen capturada (1920 por defecto)
  --height HEIGHT  el alto de la imagen capturada (1080 por defecto)
  --headless       ejecutar sin abrir una ventana de previsualización
  --db DB          string de conexión a la base de datos
```