import sys
import time
import cv2
import argparse
import psycopg2
import urllib.parse

# Parámetros del detector de marcadores
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
parameters =  cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)

# Filtrado de detecciones
MIN_DETECTION_FRAMES = 10
CLEAR_INTERVAL_SEC = 60

# TODO: Dejar que la DB maneje este caso
VALID_IDS = [1,2,3,4,5]


def draw_bboxes(image, corners, ids):
    for (markerCorner, markerID) in zip(corners, ids):
        # Extract the marker corners (which are always returned in
        # top-left, top-right, bottom-right, and bottom-left order)
        corners = markerCorner.reshape((4, 2))
        (topLeft, topRight, bottomRight, bottomLeft) = corners

        # Convert each of the (x, y)-coordinate pairs to integers
        topRight = (int(topRight[0]), int(topRight[1]))
        bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
        bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
        topLeft = (int(topLeft[0]), int(topLeft[1]))

        # Draw the bounding box of the ArUCo detection
        cv2.line(image, topLeft, topRight, (0, 255, 0), 2)
        cv2.line(image, topRight, bottomRight, (0, 255, 0), 2)
        cv2.line(image, bottomRight, bottomLeft, (0, 255, 0), 2)
        cv2.line(image, bottomLeft, topLeft, (0, 255, 0), 2)

        # Compute and draw the center (x, y)-coordinates of the ArUco
        # marker
        cX = int((topLeft[0] + bottomRight[0]) / 2.0)
        cY = int((topLeft[1] + bottomRight[1]) / 2.0)
        cv2.circle(image, (cX, cY), 4, (0, 0, 255), -1)

        # Draw the ArUco marker ID on the image
        cv2.putText(image, str(markerID),
            (topLeft[0], topLeft[1] - 15), cv2.FONT_HERSHEY_SIMPLEX,
            5, (0, 255, 0), 2)


def main():
    parser = argparse.ArgumentParser(description="Ejecuta el detector de etiquetas de ganado")
    parser.add_argument("device", type=str, 
                        help="el dispositivo de captura de video (ej. /dev/video0)")
    parser.add_argument("--width", type=int, required=False,
                        help="el ancho de la imagen capturada (1920 por defecto)", default=1920)
    parser.add_argument("--height", type=int, required=False,
                        help="el alto de la imagen capturada (1080 por defecto)", default=1080)
    parser.add_argument("--fps", type=int, required=False,
                        help="límite de FPS de procesamiento (30 por defecto)", default=30)
    parser.add_argument("--headless", dest="headless", action="store_true", 
                        help="ejecutar sin abrir una ventana de previsualización")
    parser.add_argument("--db", type=str, required=False,
                        help="string de conexión a la base de datos")
    args = parser.parse_args()

    # Conectarse a la DB
    if args.db:
        conn_str = urllib.parse.urlparse(args.db)
        if conn_str.scheme != "postgresql":
            parser.error("El string de conexión debe ser de la forma postgresql://user:password@hostname:post/dbname")

        conn = psycopg2.connect(
            host=conn_str.hostname,
            port=conn_str.port,
            database=conn_str.path.split("/")[0],
            user=conn_str.username,
            password=conn_str.password
        )

    # Abrir el dispositivo de captura
    cap = cv2.VideoCapture(args.device)
    if not cap.isOpened():
        print(f"Error: Cannot open {args.device}")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

    # Crear la ventana si no se está en modo headless
    if not args.headless:
        cv2.namedWindow("Agrovision", cv2.WINDOW_NORMAL)

    # Filtrado de detecciones
    detections = {}
    last_clear = time.time()

    ti = time.time()

    while True:
        try:
            ret, frame = cap.read()

            tf = time.time()
            if tf-ti < 1.0 / args.fps:
                continue

            # Detectar los marcadores
            corners, ids, _ = detector.detectMarkers(frame)
            if len(corners) > 0:
                ids = ids.flatten()

                # Dibujar los bounding boxes
                draw_bboxes(frame, corners, ids)

                # Filtrar las detecciones
                for idx in ids:
                    d = detections.get(idx, 0)

                    if d == MIN_DETECTION_FRAMES and idx in VALID_IDS:
                        print(f"Animal {idx} detectado")

                        # Insertar en la DB
                        # TODO: Cambiar por MQTT / REST
                        if args.db:
                            success, buffer = cv2.imencode(".jpg", frame)

                            with conn.cursor() as cur:
                                cur.execute("INSERT INTO log (time, animal_id, snapshot) VALUES (current_timestamp, %s, %s);",
                                            (int(idx), psycopg2.Binary(buffer)))
                                conn.commit()


                    detections[idx] = d+1
                            
                if time.time() - last_clear >= CLEAR_INTERVAL_SEC:
                    last_clear = time.time()
                    detections.clear()


            if not args.headless:
                cv2.imshow("Agrovision", frame)

                key = cv2.waitKey(1)
                if key == ord('q'):        
                    break

            ti = time.time()

        except KeyboardInterrupt:
            break

    # Liberar el dispositivo de captura
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()