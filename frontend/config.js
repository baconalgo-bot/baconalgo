// config.js ou au début de ton fichier
const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:5000'  // Dev local
    : 'https://baconalgo-api-x1m8.onrender.com';  // Production

// Utilise ensuite:
fetch(`${API_URL}/api/scan`, { ... })
