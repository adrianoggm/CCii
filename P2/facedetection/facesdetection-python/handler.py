#!/usr/bin/env python
import cv2
import numpy as np
import requests
import base64
import sys

def download_image(url):
    """Descarga la imagen y la decodifica con OpenCV."""
    print("[DEBUG] Descargando imagen desde URL:", url, file=sys.stderr)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image_array = np.frombuffer(response.content, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("No se pudo decodificar la imagen; revisa el formato.")
        print("[DEBUG] Imagen descargada y decodificada correctamente", file=sys.stderr)
        return image
    except Exception as e:
        raise Exception(f"Error descargando la imagen: {e}")

def detect_faces(image):
    """Detecta rostros en la imagen usando el clasificador Haar de OpenCV."""
    print("[DEBUG] Iniciando detección de rostros", file=sys.stderr)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    print(f"[DEBUG] Detección finalizada, rostros encontrados: {len(faces)}", file=sys.stderr)
    return faces

def draw_faces(image, faces):
    """Dibuja rectángulos en los rostros detectados."""
    print("[DEBUG] Dibujando recuadros en los rostros", file=sys.stderr)
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    print("[DEBUG] Recuadros dibujados correctamente", file=sys.stderr)
    return image

def image_to_base64(image):
    """Convierte la imagen procesada a una cadena en Base64."""
    print("[DEBUG] Codificando imagen a Base64", file=sys.stderr)
    ret, buffer = cv2.imencode('.png', image)
    if not ret:
        raise Exception("Error al codificar la imagen.")
    encoded = base64.b64encode(buffer).decode('utf-8')
    print(f"[DEBUG] Imagen codificada a Base64, longitud: {len(encoded)} caracteres", file=sys.stderr)
    return encoded

def handle(event, context):
    """Función que se invoca con el evento y el contexto.
    
    Se espera que el body del evento contenga la URL de la imagen.
    """
    try:
        print("[DEBUG] Iniciando handle en handler.py", file=sys.stderr)
        
        # Convertir el cuerpo a string si es bytes
        if isinstance(event.body, bytes):
            body_str = event.body.decode('utf-8')
        else:
            body_str = event.body

        url = body_str.strip()
        print(f"[DEBUG] Contenido del body: {url}", file=sys.stderr)
        
        if not url:
            return { "statusCode": 400, "body": "No se proporcionó una URL en la solicitud." }
        
        image = download_image(url)
        faces = detect_faces(image)
        image_with_faces = draw_faces(image, faces)
        encoded_image = image_to_base64(image_with_faces)
        
        print("[DEBUG] Handler finalizando correctamente", file=sys.stderr)
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": encoded_image
        }
    except Exception as e:
        error_message = f"Error durante la detección de rostros: {str(e)}"
        print(f"[DEBUG] {error_message}", file=sys.stderr)
        return { "statusCode": 500, "body": error_message }

