document.addEventListener("DOMContentLoaded", function () {
    const trackForm = document.getElementById("trackForm");
    const statusBox = document.getElementById("trackingResult");
    const statusText = document.getElementById("statusText");

    trackForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const trackingId = document.getElementById("trackingId").value.trim();

        if (!trackingId) {
            alert("Please enter a valid Tracking ID.");
            return;
        }

        statusText.innerText = "Checking status...";
        statusBox.style.display = "block";

        try {
            const response = await fetch(`/track/${trackingId}`);
            const data = await response.json();

            if (data.error) {
                statusText.innerText = "Tracking ID not found.";
            } else {
                statusText.innerText = `Delivery Status: ${data.status}`;
            }
        } catch (error) {
            statusText.innerText = "Unable to connect to server. Please try again.";
        }
    });
});