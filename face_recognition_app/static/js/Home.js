document.addEventListener("DOMContentLoaded", function () {
    const teacherNameElement = document.getElementById("teacher-name");
    const addSubjectBtn = document.getElementById("add-subject-btn");

    // ✅ Function to refresh teacher's name from Flask
    function refreshTeacherName() {
        fetch('/home')
            .then(response => response.text())
            .then(html => {
                let tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                let newTeacherName = tempDiv.querySelector("#teacher-name").innerText;
                teacherNameElement.innerText = newTeacherName;
            })
            .catch(error => console.error("Error fetching teacher name:", error));
    }

    // ✅ Add Subject Button Click Event
    if (addSubjectBtn) {
        addSubjectBtn.addEventListener("click", function () {
            // ✅ Prevent Multiple Prompts
            if (window.addingSubject) return;  
            window.addingSubject = true;  // Mark process as running

            const subjectName = prompt("Enter Subject Name:");
            if (!subjectName) return window.addingSubject = false; // Stop if cancelled

            const dayOfWeek = prompt("Enter Day (Monday-Sunday):");
            if (!dayOfWeek) return window.addingSubject = false; // Stop if cancelled

            const startTime = prompt("Enter Start Time (e.g., 10:00 AM):");
            if (!startTime) return window.addingSubject = false; // Stop if cancelled

            const endTime = prompt("Enter End Time (e.g., 11:30 AM):");
            if (!endTime) return window.addingSubject = false; // Stop if cancelled

            fetch("/add_subject", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    subject_name: subjectName,
                    day_of_week: dayOfWeek,
                    start_time: startTime,
                    end_time: endTime
                })
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                location.reload(); // ✅ Refresh page to show new subject
            })
            .catch(err => console.error("Error:", err))
            .finally(() => { window.addingSubject = false; });  // ✅ Allow new clicks after finishing
        });
    } else {
        console.error("❌ add-subject-btn not found in the DOM!");
    }

    // ✅ Function to Add Event Listeners to Rows
    function addRowEventListeners(row) {
        let editBtn = row.querySelector(".edit-btn");
        let deleteBtn = row.querySelector(".delete-btn");

        if (editBtn) {
            editBtn.addEventListener("click", function () {
                let subjectId = row.getAttribute("data-id");
                let newSubjectName = prompt("Enter New Subject Name:");

                if (newSubjectName) {
                    fetch(`/edit_subject/${subjectId}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ subject_name: newSubjectName })
                    })
                    .then(res => res.json())
                    .then(data => {
                        alert(data.message);
                        location.reload(); // Refresh page to show updated subject
                    })
                    .catch(err => console.error("Error:", err));
                }
            });
        }

        if (deleteBtn) {
            deleteBtn.addEventListener("click", function () {
                let subjectId = row.getAttribute("data-id");

                if (confirm("Are you sure you want to delete this subject?")) {
                    fetch(`/delete_subject/${subjectId}`, { method: "DELETE" })
                    .then(res => res.json())
                    .then(data => {
                        alert(data.message);
                        location.reload(); // Refresh page after deletion
                    })
                    .catch(err => console.error("Error:", err));
                }
            });
        }
    }

    // ✅ Attach Listeners to Existing Table Rows
    document.querySelectorAll("#timetable tbody tr").forEach(addRowEventListeners);
});
