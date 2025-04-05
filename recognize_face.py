import cv2
import numpy as np
import face_recognition
import os
import mysql.connector
from datetime import datetime

def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Dhrumil332211",
            database="face_recognition"
        )
        cursor = conn.cursor(dictionary=True, buffered=True)
        print("[INFO] Connected to MySQL successfully.")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL connection failed: {err}")
        return None, None

def mark_attendance(enrollment_no, name):
    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        print("[ERROR] Database connection failed")
        return False
    
    try:
        # Check if already marked present today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT id FROM attendance_records 
            WHERE enrollment_no = %s AND DATE(timestamp) = %s AND status = 'Present'
        """, (enrollment_no, today))
        
        if cursor.fetchone():
            print(f"[INFO] {name} already marked present today")
            cursor.close()
            conn.close()
            return False
            
        # Mark attendance
        cursor.execute("""
            INSERT INTO attendance_records (enrollment_no, name, status, timestamp) 
            VALUES (%s, %s, %s, NOW())
        """, (enrollment_no, name, "Present"))
        conn.commit()
        print(f"[INFO] {name} marked present successfully!")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to mark attendance: {e}")
        if conn:
            conn.close()
        return False

def recognize_faces():
    # Path to the directory containing face encodings
    path = 'face_encodings'
    known_face_encodings = []
    known_names = []
    known_enrollment_nos = []
    
    # Load known faces
    try:
        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            print("[ERROR] Database connection failed")
            return
            
        cursor.execute("SELECT enrollment_no, name FROM manual_attendance")
        students = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Load encodings for each student if they exist
        for student in students:
            encoding_file = os.path.join(path, f"{student['enrollment_no']}.npy")
            if os.path.exists(encoding_file):
                face_encoding = np.load(encoding_file)
                known_face_encodings.append(face_encoding)
                known_names.append(student['name'])
                known_enrollment_nos.append(student['enrollment_no'])
                print(f"[INFO] Loaded encoding for {student['name']}")
    except Exception as e:
        print(f"[ERROR] Failed to load encodings: {e}")
        return
    
    # Start video capture
    cap = cv2.VideoCapture(0)
    
    # Set timeout for attendance (30 seconds)
    start_time = datetime.now()
    timeout_seconds = 30
    marked_students = set()
    
    print("[INFO] Starting face recognition. Press 'q' to quit.")
    
    while True:
        # Check for timeout
        elapsed = (datetime.now() - start_time).total_seconds()
        if elapsed > timeout_seconds:
            print(f"[INFO] Timeout after {timeout_seconds} seconds")
            break
            
        # Capture frame
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame")
            break
            
        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        
        # Convert from BGR to RGB
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        
        # Find faces in current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        
        for face_encoding in face_encodings:
            # Compare with known faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
            
            if True in matches:
                # Get index of matching face
                match_index = matches.index(True)
                name = known_names[match_index]
                enrollment_no = known_enrollment_nos[match_index]
                
                # Skip if already marked
                if enrollment_no in marked_students:
                    continue
                    
                # Mark attendance
                if mark_attendance(enrollment_no, name):
                    print(f"[INFO] Marked attendance for {name} ({enrollment_no})")
                    marked_students.add(enrollment_no)
                    
                    # Display text on frame
                    cv2.putText(frame, f"Marked: {name}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                # Unknown face
                cv2.putText(frame, "Unknown", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Display frame
        cv2.imshow('Face Recognition', frame)
        
        # Exit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"[INFO] Attendance marked for {len(marked_students)} students")
    
if __name__ == "__main__":
    recognize_faces()