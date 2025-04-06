document.addEventListener("DOMContentLoaded", function () {
    let addUserBtn = document.getElementById("addUserBtn");
    let markAttendanceBtn = document.getElementById("markAttendanceBtn");
    let addManualUserBtn = document.getElementById("addManualUserBtn");
    let saveAttendanceBtn = document.getElementById("saveAttendanceBtn");

    if (addUserBtn) addUserBtn.addEventListener("click", addNewUser);
    if (markAttendanceBtn) markAttendanceBtn.addEventListener("click", markAttendance);
    if (addManualUserBtn) addManualUserBtn.addEventListener("click", addManualUser);
    if (saveAttendanceBtn) saveAttendanceBtn.addEventListener("click", saveAttendance);

    loadStudents(); // Load students when the page loads
});

// Show manual attendance section and load students
function showManualAttendance() {
    document.getElementById("manualAttendanceSection").classList.toggle("hidden");
    loadStudents();  
}

function showFaceRecognition() {
    console.log("Face Recognition button clicked!"); // Debugging log
    document.getElementById("faceRecognitionSection").classList.toggle("hidden");
}

// Load students and prevent duplicate names
function loadStudents() {
    fetch('/get_students')
    .then(response => response.json())
    .then(students => {
        let tableBody = document.getElementById("attendanceTable");
        let existingStudentIds = new Set();  // Track existing students

        // Store already displayed student IDs
        document.querySelectorAll("#attendanceTable tr").forEach(row => {
            let studentId = row.getAttribute("data-student-id");
            if (studentId) existingStudentIds.add(studentId);
        });

        students.forEach(student => {
            if (!existingStudentIds.has(student.id.toString())) {  // Prevent duplicates
                let row = document.createElement("tr");
                row.setAttribute("data-student-id", student.id);  

                row.innerHTML = `
                    <td>${student.enrollment_no}</td>
                    <td>${student.name}</td>
                    <td><input type="radio" name="status${student.id}" value="Present"></td>
                    <td><input type="radio" name="status${student.id}" value="Absent"></td>
                    <td><button onclick="removeStudent(${student.id})">Remove</button></td>
                `;
                tableBody.appendChild(row);
            }
        });
    })
    .catch(error => console.error("Error loading students:", error));
}

// Add a new student manually
function addManualUser() {
    let name = prompt("Enter Full Name:");
    let enrollmentNo = prompt("Enter Enrollment Number:");

    if (!name || !enrollmentNo) {
        alert("Name and Enrollment Number are required!");
        return;
    }

    fetch('/add_manual_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, enrollment_no: enrollmentNo })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadStudents();  // Refresh student list
    })
    .catch(error => {
        console.error("Fetch error:", error);
        alert("Error: " + error.message);
    });
}

// Save manual attendance to MySQL
function saveAttendance() {
    let tableRows = document.querySelectorAll("#attendanceTable tr");
    let attendanceData = [];

    tableRows.forEach(row => {
        let studentId = row.getAttribute("data-student-id");
        let presentChecked = row.querySelector(`input[name="status${studentId}"][value="Present"]`).checked;
        let absentChecked = row.querySelector(`input[name="status${studentId}"][value="Absent"]`).checked;

        let status = presentChecked ? "Present" : absentChecked ? "Absent" : null;
        if (status) {
            attendanceData.push({ id: studentId, status: status });
        }
    });

    if (attendanceData.length === 0) {
        alert("No attendance marked!");
        return;
    }

    console.log("Submitting Attendance Data:", attendanceData); // Debugging log

    fetch('/submit_attendance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attendance: attendanceData })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        console.log("Server Response:", data);
    })
    .catch(error => {
        console.error("Fetch error:", error);
        alert("Error: " + error.message);
    });
}

// Remove a student from the list and MySQL
function removeStudent(studentId) {
    if (!confirm("Are you sure you want to remove this student?")) return;

    fetch(`/remove_student/${studentId}`, { method: 'DELETE' })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        loadStudents();  // Refresh student list after deletion
    })
    .catch(error => {
        console.error("Fetch error:", error);
        alert("Error: " + error.message);
    });
}

// Face recognition functions
function addNewUser() {
    let name = prompt("Enter Full Name:");
    let enrollmentNo = prompt("Enter Enrollment Number:");
    
    if (!name || !enrollmentNo) {
        alert("Both name and enrollment number are required!");
        return;
    }

    fetch('/add_new_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, enrollment_no: enrollmentNo })
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error("Error:", error));
}
function markAttendance() {
    console.log("Start Recognition button clicked!");  // Check if button is working

    fetch('/mark_attendance', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log("Server response:", data);  // Debug Flask response
            alert(data.message);
        })
        .catch(error => console.error("Error:", error));
}
