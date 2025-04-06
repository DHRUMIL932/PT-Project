import cv2
import numpy as np
import mysql.connector
import pickle
from deepface import DeepFace
from mtcnn import MTCNN
from datetime import datetime
from scipy.spatial.distance import cosine

# Connect to MySQL
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host="LocalHost",
            user="root",
            password="Dhrumil332211",
            database="face_recognition"
        )
        cursor = conn.cursor()
        print("[INFO] Connected to MySQL successfully.")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL connection failed: {err}")
        return None, None

# Function to fetch stored face embeddings
def get_registered_faces(cursor):
    cursor.execute("SELECT name, enrollment_no, embedding FROM face_data")
    records = cursor.fetchall()
    
    stored_faces = []
    for name, enrollment_no, embedding_text in records:
        embedding_list = list(map(float, embedding_text.split(',')))
        stored_faces.append((name, enrollment_no, embedding_list))
    
    return stored_faces

# Function to detect face
def detect_face(frame):
    detector = MTCNN()
    faces = detector.detect_faces(frame)
    if faces:
        x, y, w, h = faces[0]['box']
        return frame[y:y+h, x:x+w]
    return None

# Function to mark attendance in MySQL
def mark_attendance(cursor, conn, name, enrollment_no):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO attendance (enrollment_no, name, timestamp) VALUES (%s, %s, %s)", 
                   (enrollment_no, name, timestamp))
    conn.commit()
    print(f"[INFO] Attendance marked for {name} ({enrollment_no}) at {timestamp}")

# Function to recognize and mark attendance
def recognize_face():
    conn, cursor = connect_to_mysql()
    if conn is None or cursor is None:
        return

    stored_faces = get_registered_faces(cursor)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Camera not found.")
        return

    print("[INFO] Capturing face for recognition...")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Camera frame not available.")
            break

        detected_face = detect_face(frame)
        if detected_face is not None:
            detected_face = cv2.resize(detected_face, (160, 160))

            try:
                # Generate embedding for detected face
                embedding = DeepFace.represent(detected_face, model_name="Facenet")[0]['embedding']
                
                # Compare with stored embeddings
                for name, enrollment_no, stored_embedding in stored_faces:
                    similarity = 1 - cosine(embedding, stored_embedding)  # Cosine similarity

                    if similarity > 0.5:  # Threshold for match
                        print(f"[INFO] Recognized: {name} ({enrollment_no}) with confidence {similarity:.2f}")
                        mark_attendance(cursor, conn, name, enrollment_no)
                        break
                else:
                    print("[INFO] No match found.")

            except Exception as e:
                print(f"[ERROR] Error in face recognition: {e}")

        cv2.imshow("Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    cursor.close()
    conn.close()

if __name__ == "_main_":
    recognize_face()