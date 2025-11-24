const chatSend = document.getElementById("chatSend");
const chatInput = document.getElementById("chatInput");
const chatOutput = document.getElementById("chatOutput");

chatSend.addEventListener("click", async () => {
  const userMessage = chatInput.value.trim();
  if(!userMessage) return;

  const response = await fetch("/api/ask", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({ message: userMessage })
  });

  const data = await response.json();
  const botReply = data.reply || "Sorry, I could not get a response.";

  const messageElement = document.createElement("p");
  messageElement.innerHTML = `<strong>You:</strong> ${userMessage}<br><strong>ArewaBot:</strong> ${botReply}`;
  chatOutput.appendChild(messageElement);

  chatInput.value = "";
  chatOutput.scrollTop = chatOutput.scrollHeight;
});