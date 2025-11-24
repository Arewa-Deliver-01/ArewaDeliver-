// Mini Wallet & Demo Transactions
function registerUser(formData) {
    const users = JSON.parse(localStorage.getItem('arewa_users') || '[]');
    const user = {
        fullname: formData.get('fullname'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        role: formData.get('role'),
        password: formData.get('password'),
        wallet: { balance: 0, transactions: [] }
    };
    users.push(user);
    localStorage.setItem('arewa_users', JSON.stringify(users));
    alert('Registered successfully (Demo)');
    window.location.href = "verify.html";
}
