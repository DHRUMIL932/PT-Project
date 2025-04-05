import cv2
import os
import numpy as np
import pyttsx3
import mysql.connector
from deepface import DeepFace
from mtcnn import MTCNN
import sys
import time

# Initialize Text-to-Speech
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

face_dir = "captured_faces"
os.makedirs(face_dir, exist_ok=True)

detector = MTCNN()

# Get arguments from Flask
if len(sys.argv) < 3:
    print("Usage: python register_face.py <name> <enrollment_no>")
    sys.exit(1)

name = sys.argv[1]
enrollment_no = sys.argv[2]

def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host="LocalHost",
            user="root",
            password="Dhrumil332211",
            database="face_recognition"
        )
        cursor = conn.cursor()
        print("[INFO] Connected to MySQL database successfully.")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL connection failed: {err}")
        return None, None

def detect_faces(frame):
    results = detector.detect_faces(frame)
    if results:
        x, y, w, h = results[0]['box']
        return frame[y:y+h, x:x+w], (x, y, w, h)
    return None, None

def register_face():
    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Camera not found.")
        return

    angles = ["Front", "Left", "Right", "Up", "Down", "Chin Up", "Chin Down", "Tilt Left", "Tilt Right", "Smile", "Neutral"]
    captured_faces = []
    captured_count = 0
    frame_count = 0  

    while captured_count < len(angles):
        ret, frame = cap.read()
        if not ret:
            break

        face, bbox = detect_faces(frame)
        if face is not None:
            face_resized = cv2.resize(face, (160, 160))

            if frame_count % 5 == 0:  # Capture every 5 frames to speed up
                engine.say(f"Move to {angles[captured_count]}")
                engine.runAndWait()

                face_path = os.path.join(face_dir, f"{name}_{enrollment_no}_{angles[captured_count].replace(' ', '_')}.jpg")
                cv2.imwrite(face_path, face_resized)
                captured_faces.append(face_resized)

                captured_count += 1  

            frame_count += 1

        cv2.imshow("Register Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if not captured_faces:
        print("[ERROR] No faces were captured.")
        return

    try:
        embeddings = []
        for face in captured_faces:
            embedding = DeepFace.represent(face, model_name="Facenet", enforce_detection=False)[0]['embedding']
            embeddings.append(embedding)

        avg_embedding = np.mean(embeddings, axis=0)  # Average embedding
        embedding_str = ",".join(map(str, avg_embedding))

        cursor.execute("INSERT INTO face_data (name, enrollment_no, embedding) VALUES (%s, %s, %s)", 
                       (name, enrollment_no, embedding_str))
        conn.commit()
        print("[INFO] User registered successfully.")
    except Exception as e:
        print(f"[ERROR] Error saving embedding: {e}")

    cursor.close()
    conn.close()

register_face()
