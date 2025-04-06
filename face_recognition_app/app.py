import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from werkzeug.security import generate_password_hash
from flask_bcrypt import Bcrypt  # For password hashing
import mysql.connector
from datetime import datetime
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this for security
CORS(app)
bcrypt = Bcrypt(app)  # Initialize bcrypt for password hashing

# MySQL Connection Function
def connect_to_mysql():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Dhrumil332211",
            database="face_recognition"
        )
        cursor = conn.cursor(dictionary=True, buffered=True)  # ✅ Buffered cursor
        print("[INFO] Connected to MySQL successfully.")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"[ERROR] MySQL connection failed: {err}")
        return None, None


# Get DB connection
conn, cursor = connect_to_mysql()

# Hash the password
username = "admin"
plain_password = "admin123"

# Use bcrypt to hash the password
hashed_password = bcrypt.generate_password_hash(plain_password).decode('utf-8')

# Insert user into MySQL table
try:
    cursor.execute("INSERT INTO LoginIDPass (username, password) VALUES (%s, %s)", (username, hashed_password))
    conn.commit()
    print("[INFO] User added successfully!")
except mysql.connector.Error as err:
    print(f"[ERROR] MySQL error: {err}")

# 🔹 LOGIN PAGE ROUTE
@app.route('/')
def login_page():
    session.clear()
    if 'user_id' in session:
        return redirect(url_for('home'))  # Redirect to home if already logged in
    return render_template('Loginpage.html')

# 🔹 LOGIN AUTHENTICATION
@app.route('/login', methods=['POST'])
def login():
    # ✅ Check for JSON or form data
    if request.content_type == 'application/json':
        data = request.get_json()
    else:
        data = request.form

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return jsonify({"message": "Database connection failed"}), 500

    try:
        cursor.execute("SELECT * FROM LoginIDPass WHERE username = %s", (username,))
        user = cursor.fetchone()  # ✅ Fetch result BEFORE closing cursor

        # ✅ Close cursor before returning data
        cursor.close()
        conn.close()

        if user:
            if bcrypt.check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                return jsonify({"message": "Login successful!", "redirect": "/home"}), 200
            else:
                return jsonify({"message": "Invalid username or password"}), 401
        else:
            return jsonify({"message": "Invalid username or password"}), 401

    except mysql.connector.Error as err:
        return jsonify({"message": f"Database error: {err}"}), 500

# 🔹 PROTECTED ROUTE (Requires Login)
@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))  # Redirect to login if not authenticated

    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return "Database connection failed", 500

    # Fetch subjects from MySQL
    cursor.execute("SELECT id, subject, day_of_week, start_time, end_time FROM teacher_timetable")
    subjects = cursor.fetchall()

    cursor.execute("SELECT first_name, last_name FROM teachers WHERE id = %s", (session['user_id'],))
    teacher = cursor.fetchone()

    cursor.close()
    conn.close()

    teacher_name = f"{teacher['first_name']} {teacher['last_name']}" if teacher else "Unknown"

    # ✅ Pass subjects to the template
    return render_template('Home.html', teacher_name=teacher_name, subjects=subjects)

# 🔹 LOGOUT ROUTE
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login_page'))

@app.route('/setting')
def setting():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))  # Redirect to login if not authenticated

    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return "Database connection failed", 500

    # Fetch teacher's name from database using session user_id
    cursor.execute("SELECT first_name, last_name FROM teachers WHERE id = %s", (session['user_id'],))
    teacher = cursor.fetchone()

    cursor.close()
    conn.close()

    # Pass teacher's name to the HTML template
    if teacher:
        teacher_name = f"{teacher['first_name']} {teacher['last_name']}"
    else:
        teacher_name = "Unknown"  # Default fallback
        
    return render_template('Setting.html', teacher_name=teacher_name)

@app.route('/attendancesystem')
def attendancesystem():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))  # Redirect to login if not authenticated

    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return "Database connection failed", 500

    # Fetch teacher's name from database using session user_id
    cursor.execute("SELECT first_name, last_name FROM teachers WHERE id = %s", (session['user_id'],))
    teacher = cursor.fetchone()

    cursor.close()
    conn.close()

    # Pass teacher's name to the HTML template
    if teacher:
        teacher_name = f"{teacher['first_name']} {teacher['last_name']}"
    else:
        teacher_name = "Unknown"  # Default fallback

    return render_template('AttendanceSystem.html', teacher_name=teacher_name) 

@app.route('/add_timetable', methods=['POST'])
def add_timetable():
    try:
        data = request.get_json()
        teacher_id = data.get("teacher_id")
        subject = data.get("subject")
        day_of_week = data.get("day_of_week")
        start_time = data.get("start_time")
        end_time = data.get("end_time")

        if not teacher_id or not subject or not day_of_week or not start_time or not end_time:
            return jsonify({"message": "All fields are required"}), 400

        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        cursor.execute("""
            INSERT INTO teacher_timetable (teacher_id, subject, day_of_week, start_time, end_time) 
            VALUES (%s, %s, %s, %s, %s)
        """, (teacher_id, subject, day_of_week, start_time, end_time))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Timetable entry added successfully!"})

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/add_subject', methods=['POST'])
def add_subject():
    try:
        data = request.get_json()
        teacher_id = session.get('user_id')  # Ensure session contains user ID
        subject_name = data.get("subject_name")
        day_of_week = "Monday"  # Default day
        start_time = "10:00 AM"
        end_time = "11:00 AM"

        # ✅ Convert time format to HH:MM:SS (24-hour format)
        start_time = datetime.strptime(start_time, "%I:%M %p").strftime("%H:%M:%S")
        end_time = datetime.strptime(end_time, "%I:%M %p").strftime("%H:%M:%S")

        if not teacher_id or not subject_name:
            return jsonify({"message": "Teacher ID and Subject Name required"}), 400

        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        cursor.execute("""
            INSERT INTO teacher_timetable (teacher_id, subject, day_of_week, start_time, end_time) 
            VALUES (%s, %s, %s, %s, %s)
        """, (teacher_id, subject_name, day_of_week, start_time, end_time))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Subject added successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/edit_subject/<int:subject_id>', methods=['PUT'])
def edit_subject(subject_id):
    try:
        data = request.get_json()
        new_name = data.get("subject_name")

        if not new_name:
            return jsonify({"message": "New subject name is required"}), 400

        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        cursor.execute("UPDATE teacher_timetable SET subject = %s WHERE id = %s", (new_name, subject_id))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Subject updated successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/delete_subject/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    try:
        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        cursor.execute("DELETE FROM teacher_timetable WHERE id = %s", (subject_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Subject deleted successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# 🔹 USER REGISTRATION WITH PASSWORD HASHING
@app.route('/register', methods=['POST'])
def register():
    if request.content_type == 'application/json':
        data = request.get_json()
    else:
        data = request.form

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')  # ✅ Hash password before storing

    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return jsonify({"message": "Database connection failed"}), 500

    try:
        cursor.execute("INSERT INTO LoginIDPass (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "User registered successfully!"}), 201
    except mysql.connector.Error as err:
        return jsonify({"message": f"Error: {err}"}), 500

# Route to fetch all students for manual attendance
@app.route('/get_students', methods=['GET'])
def get_students():
    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return jsonify({"message": "Database connection failed"}), 500

    cursor.execute("SELECT id, enrollment_no, name FROM manual_attendance")
    students = cursor.fetchall()

    cursor.close()
    conn.close()
    return jsonify(students)

# Route to add a new student manually
@app.route('/add_manual_user', methods=['POST'])
def add_manual_user():
    try:
        data = request.get_json()
        name = data.get("name")
        enrollment_no = data.get("enrollment_no")

        if not name or not enrollment_no:
            return jsonify({"message": "Missing name or enrollment number"}), 400

        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        cursor.execute("INSERT INTO manual_attendance (enrollment_no, name) VALUES (%s, %s)", (enrollment_no, name))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"message": f"User {name} added manually!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

# Route to submit attendance manually
@app.route('/submit_attendance', methods=['POST'])
def submit_attendance():
    try:
        data = request.get_json()
        attendance_list = data.get("attendance")

        if not attendance_list:
            return jsonify({"message": "No attendance data received"}), 400

        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        for student in attendance_list:
            student_id = student["id"]
            status = student["status"]

            print(f"Saving attendance for ID: {student_id}, Status: {status}")  # Debugging log

            cursor.execute("""
                INSERT INTO attendance_records (enrollment_no, name, status, timestamp) 
                SELECT enrollment_no, name, %s, NOW() 
                FROM manual_attendance WHERE id = %s
            """, (status, student_id))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Attendance saved successfully!"})
    except Exception as e:
        print(f"[ERROR] Attendance insert failed: {e}")
        return jsonify({"message": f"Error: {str(e)}"}), 500

# Route for face recognition-based user registration
@app.route('/add_new_user', methods=['POST'])
def add_new_user():
    try:
        data = request.get_json()
        name = data.get("name")
        enrollment_no = data.get("enrollment_no")

        if not name or not enrollment_no:
            return jsonify({"message": "Missing name or enrollment number"}), 400

        subprocess.Popen(["python", ("register_face.py"), name, enrollment_no])
        return jsonify({"message": "Face registration started!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

# Route for marking attendance via face recognition
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        subprocess.Popen(["python", ("recognize_face.py")])
        return jsonify({"message": "Face recognition started!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/remove_student/<int:student_id>', methods=['DELETE'])
def remove_student(student_id):
    try:
        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        cursor.execute("DELETE FROM manual_attendance WHERE id = %s", (student_id,))
        conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"message": "Student removed successfully!"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

    # Update Security Settings (Username & Password)
@app.route('/update_security_settings', methods=['POST'])
def update_security_settings():
    try:
        data = request.get_json()
        username = data.get("username")
        current_password = data.get("current_password")
        new_password = data.get("new_password")
        security_question = data.get("security_question")
        security_answer = data.get("security_answer")

        if not username or not current_password or not new_password:
            return jsonify({"message": "All security fields are required"}), 400

        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        # Fetch the user from the database
        cursor.execute("SELECT * FROM LoginIDPass WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "Wrong username or password"}), 401

        # Verify current password
        if not bcrypt.check_password_hash(user['password'], current_password):
            return jsonify({"message": "Wrong username or password"}), 401

        # Hash the new password
        hashed_new_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        # Update password in the database
        cursor.execute("UPDATE LoginIDPass SET password = %s WHERE username = %s", (hashed_new_password, username))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Password updated successfully!"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

# Update Account Settings
@app.route('/update_account_settings', methods=['POST'])
def update_account_settings():
    try:
        data = request.get_json()
        user_id = session.get("user_id")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")
        city = data.get("city")
        country = data.get("country")
        address = data.get("address")

        if not user_id or not first_name or not last_name or not email or not city or not country or not address:
            return jsonify({"message": "All fields are required"}), 400

        conn, cursor = connect_to_mysql()
        if not conn or not cursor:
            return jsonify({"message": "Database connection failed"}), 500

        # Update teacher details
        cursor.execute("""
            UPDATE teachers 
            SET first_name = %s, last_name = %s, email = %s, city = %s, country = %s, address = %s 
            WHERE id = %s
        """, (first_name, last_name, email, city, country, address, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        # Update session so UI reflects the changes
        session["first_name"] = first_name
        session["last_name"] = last_name
        return jsonify({"message": "Profile updated successfully!", "first_name": first_name, "last_name": last_name})

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

#Update teachers information
@app.route('/update_teacher', methods=['POST'])
def update_teacher():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))

    new_first_name = request.form.get('first_name')
    new_last_name = request.form.get('last_name')

    conn, cursor = connect_to_mysql()
    if not conn or not cursor:
        return "Database connection failed", 500

    # Update the teacher's name in the database
    cursor.execute("UPDATE teachers SET first_name = %s, last_name = %s WHERE id = %s",
                   (new_first_name, new_last_name, session['user_id']))
    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('home'))  # Redirect to refresh the homepage with updated info

if __name__ == '__main__':
    app.run(debug=True)