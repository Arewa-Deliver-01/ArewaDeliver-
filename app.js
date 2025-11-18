function saveProfile(role) {
    const data = {
        role: role,
        name: document.getElementById("name").value,
        phone: document.getElementById("phone").value,
        email: document.getElementById("email").value,
        address: document.getElementById("address").value
    };

    fetch("/save_profile", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(response => {
        document.getElementById("response").innerText = response.message;
    })
    .catch(() => {
        document.getElementById("response").innerText = "Error: Please try again.";
    });
}
