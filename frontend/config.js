// config.js - Configuration globale BaconAlgo
const CONFIG = {
    // API URL - Détecte automatiquement l'environnement
    API_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:5000'  // Dev local
        : 'https://baconalgo-api-x1m8.onrender.com',  // Production
    
    VERSION: '1.0.0',
    APP_NAME: 'BaconAlgo Station',
    
    // Timeout pour les requêtes (en millisecondes)
    API_TIMEOUT: 30000,
    
    // Refresh interval (en secondes)
    REFRESH_INTERVAL: 60,
};

// Log de la configuration
console.log('🥓 BaconAlgo Configuration:', {
    environment: window.location.hostname === 'localhost' ? '🔧 Development' : '🚀 Production',
    apiUrl: CONFIG.API_URL,
    version: CONFIG.VERSION
});

// Test de connexion API
async function testAPIConnection() {
    try {
        console.log('🔍 Testing API connection...');
        const response = await fetch(CONFIG.API_URL, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('✅ API is ONLINE:', data);
            return true;
        } else {
            console.warn('⚠️ API responded with status:', response.status);
            return false;
        }
    } catch (error) {
        console.error('❌ API is OFFLINE:', error.message);
        return false;
    }
}

// Helper pour faire des requêtes API
async function apiRequest(endpoint, options = {}) {
    const url = `${CONFIG.API_URL}${endpoint}`;
    
    try {
        console.log(`🚀 API Request: ${options.method || 'GET'} ${endpoint}`);
        
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                ...options.headers,
            },
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`✅ API Response from ${endpoint}:`, data);
        return { success: true, data };
        
    } catch (error) {
        console.error(`❌ API Error for ${endpoint}:`, error.message);
        return { success: false, error: error.message };
    }
}

// Test automatique au chargement
window.addEventListener('DOMContentLoaded', () => {
    testAPIConnection();
});
