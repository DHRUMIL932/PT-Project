document.addEventListener("DOMContentLoaded", function () {
    let addUserBtn = document.getElementById("addUserBtn");
    let markAttendanceBtn = document.getElementById("markAttendanceBtn");
    let addManualUserBtn = document.getElementById("addManualUserBtn");
    let saveAttendanceBtn = document.getElementById("saveAttendanceBtn");
    let clearAttendanceBtn = document.getElementById("clearAttendanceBtn");

    if (addUserBtn) addUserBtn.addEventListener("click", addNewUser);
    if (markAttendanceBtn) markAttendanceBtn.addEventListener("click", markAttendance);
    if (addManualUserBtn) addManualUserBtn.addEventListener("click", addManualUser);
    if (saveAttendanceBtn) saveAttendanceBtn.addEventListener("click", saveAttendance);
    if (clearAttendanceBtn) clearAttendanceBtn.addEventListener("click", clearAttendance);

    loadStudents(); // Load students when the page loads
});

// Clear today's attendance
function clearAttendance() {
    if (!confirm("Are you sure you want to clear today's attendance?")) return;
    
    fetch('/clear_attendance', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            loadAttendanceStatus(); // Refresh attendance status
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Error clearing attendance: " + error);
        });
}

// Show manual attendance section and load students
function showManualAttendance() {
    document.getElementById("manualAttendanceSection").classList.toggle("hidden");
    document.getElementById("faceRecognitionSection").classList.add("hidden"); // Hide other section
    document.getElementById("attendanceStatusSection").classList.remove("hidden");
    loadStudents();
    loadAttendanceStatus();
}

function showFaceRecognition() {
    console.log("Face Recognition button clicked!"); // Debugging log
    document.getElementById("faceRecognitionSection").classList.toggle("hidden");
    document.getElementById("manualAttendanceSection").classList.add("hidden"); // Hide other section
    document.getElementById("attendanceStatusSection").classList.remove("hidden");
    loadAttendanceStatus();
}

// Load attendance status
function loadAttendanceStatus() {
    // Show loading indicators
    document.getElementById("presentStudentsList").innerHTML = "<li>Loading...</li>";
    document.getElementById("absentStudentsList").innerHTML = "<li>Loading...</li>";
    
    fetch('/get_attendance_status')
    .then(response => response.json())
    .then(data => {
        updateAttendanceLists(data.present, data.absent);
    })
    .catch(error => {
        console.error("Error loading attendance status:", error);
        document.getElementById("presentStudentsList").innerHTML = "<li>Error loading data</li>";
        document.getElementById("absentStudentsList").innerHTML = "<li>Error loading data</li>";
    });
}

// Update attendance lists in UI
function updateAttendanceLists(presentStudents, absentStudents) {
    const presentList = document.getElementById("presentStudentsList");
    const absentList = document.getElementById("absentStudentsList");
    
    // Clear existing lists
    presentList.innerHTML = "";
    absentList.innerHTML = "";
    
    // Add present students to list
    if (presentStudents.length === 0) {
        presentList.innerHTML = "<li>No students present</li>";
    } else {
        presentStudents.forEach(student => {
            const listItem = document.createElement("li");
            listItem.textContent = `${student.name} (${student.enrollment_no})`;
            presentList.appendChild(listItem);
        });
    }
    
    // Add absent students to list
    if (absentStudents.length === 0) {
        absentList.innerHTML = "<li>No students absent</li>";
    } else {
        absentStudents.forEach(student => {
            const listItem = document.createElement("li");
            listItem.textContent = `${student.name} (${student.enrollment_no})`;
            absentList.appendChild(listItem);
        });
    }
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
        if (!studentId) return;  // Skip if no student ID
        
        let presentRadio = row.querySelector(`input[name="status${studentId}"][value="Present"]`);
        let absentRadio = row.querySelector(`input[name="status${studentId}"][value="Absent"]`);
        
        if (!presentRadio || !absentRadio) return;  // Skip if radio buttons not found
        
        let presentChecked = presentRadio.checked;
        let absentChecked = absentRadio.checked;

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
        loadAttendanceStatus(); // Refresh attendance status after saving
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
        loadAttendanceStatus(); // Also refresh attendance status
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
    .then(data => {
        alert(data.message);
        loadStudents(); // Refresh student list
    })
    .catch(error => console.error("Error:", error));
}

function markAttendance() {
    console.log("Start Recognition button clicked!");
    
    // Show loading state
    document.getElementById("attendanceStatusSection").classList.remove("hidden");
    document.getElementById("presentStudentsList").innerHTML = "<li>Starting face recognition...</li>";
    document.getElementById("absentStudentsList").innerHTML = "<li>Please wait...</li>";
    
    fetch('/mark_attendance', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log("Server response:", data);
            alert(data.message);
            
            // Set up polling to check for attendance updates
            pollAttendanceUpdates();
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Error: " + error);
        });
}

// Poll for attendance updates every few seconds
function pollAttendanceUpdates() {
    // Update immediately
    loadAttendanceStatus();
    
    // Then update every 3 seconds for 30 seconds
    let count = 0;
    const maxCount = 10;  // 10 x 3 seconds = 30 seconds of polling
    
    const intervalId = setInterval(() => {
        count++;
        loadAttendanceStatus();
        
        if (count >= maxCount) {
            clearInterval(intervalId);
            console.log("Finished polling for attendance updates");
        }
    }, 3000);
}