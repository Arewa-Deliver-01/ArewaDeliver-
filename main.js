// main.js - minimal helpers used by templates
document.addEventListener('DOMContentLoaded', ()=> {
  // If there is a global "notify" button: request permission
  const notifyBtns = document.querySelectorAll('[data-notify-enable]');
  notifyBtns.forEach(btn => btn.addEventListener('click', async ()=>{
    if(!('Notification' in window)) return alert('Notifications not supported');
    const perm = await Notification.requestPermission();
    if(perm === 'granted') alert('Notifications enabled');
    else alert('Notifications blocked');
  }));
});