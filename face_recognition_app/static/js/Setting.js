// Save Security Settings
function saveSecuritySettings() {
    const username = document.getElementById("username").value;
    const currentPassword = document.getElementById("current-password").value;
    const newPassword = document.getElementById("new-password").value;

    if (username === "" || currentPassword === "" || newPassword === "") {
        alert("Please fill out all security fields.");
        return;
    }

    fetch("http://127.0.0.1:5000/update_security_settings", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: username,
            current_password: currentPassword,
            new_password: newPassword
        })
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error("Error:", error));
}

// Save Account Settings
function saveAccountSettings() {
    const firstName = document.getElementById("first-name").value;
    const lastName = document.getElementById("last-name").value;
    const city = document.getElementById("city").value;
    const email = document.getElementById("email").value;
    const country = document.getElementById("country").value;
    const address = document.getElementById("address").value;

    if (firstName === "" || lastName === "" || email === "" || city === "" || country === "" || address === "") {
        alert("Please fill out all account details.");
        return;
    }

    fetch("http://127.0.0.1:5000/update_account_settings", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            first_name: firstName,
            last_name: lastName,
            city: city,
            email: email,
            country: country,
            address: address
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server Response:", data);  // Debugging log
        alert(data.message);
        document.getElementById("teacher-name").textContent = firstName + " " + lastName;
    })
    .catch(error => console.error("Error:", error));
}