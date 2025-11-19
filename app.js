// Auth & registration demo system using localStorage
// Replace with real backend API in production.

function _readUsers() {
  return JSON.parse(localStorage.getItem("arewa_users") || "[]");
}
function _writeUsers(list) {
  localStorage.setItem("arewa_users", JSON.stringify(list));
}

// Register new user
function registerUser(formData) {
  const data = {};
  for (const pair of formData.entries()) {
    data[pair[0]] = pair[1];
  }

  const users = _readUsers();
  const email = (data.email || "").trim().toLowerCase();

  if (users.find((u) => u.email === email)) {
    alert("Email already registered");
    return false;
  }

  const user = {
    id: Date.now(),
    name: data.fullname || "User",
    email,
    phone: data.phone || "",
    password: data.password || "",
    role: data.role || "customer",
    vendor_business: data.vendor_business || "",
    rider_vehicle: data.rider_vehicle || "",
    wallet: { balance: 0, transactions: [] },
    kyc: { status: "pending" }
  };

  users.push(user);
  _writeUsers(users);

  // Create session
  localStorage.setItem(
    "arewa_session",
    JSON.stringify({
      user_id: user.id,
      name: user.name,
      email: user.email,
      role: user.role
    })
  );

  // Redirect by role immediately after register
  if (user.role === "vendor") location.href = "vendor_dashboard.html";
  else if (user.role === "rider") location.href = "rider_dashboard.html";
  else location.href = "customer_dashboard.html";

  return true;
}

// Login user (returns complete user object)
async function loginUser(creds) {
  const users = _readUsers();
  const email = (creds.email || "").trim().toLowerCase();

  const user = users.find(
    (u) => u.email === email && u.password === creds.password
  );

  if (!user) return null;

  // Save session
  localStorage.setItem(
    "arewa_session",
    JSON.stringify({
      user_id: user.id,
      name: user.name,
      email: user.email,
      role: user.role
    })
  );

  return user;
}

// Logout function
function logout() {
  localStorage.removeItem("arewa_session");
  location.href = "index.html";
}

window.registerUser = registerUser;
window.loginUser = loginUser;
window.logout = logout;
