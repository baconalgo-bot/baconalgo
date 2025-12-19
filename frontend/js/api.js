// 🥓 API Connection to Railway Backend

class BaconAPI {
    constructor() {
        // Railway backend URL (will be set after deploy)
        this.baseURL = 'https://baconalgo-production.up.railway.app';
        this.ws = null;
    }
    
    async scan() {
        try {
            const response = await fetch(`${this.baseURL}/api/scan`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: error.message };
        }
    }
    
    async getTopSignals(limit = 10) {
        try {
            const response = await fetch(`${this.baseURL}/api/signals/top?limit=${limit}`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: error.message };
        }
    }
    
    async getStats() {
        try {
            const response = await fetch(`${this.baseURL}/api/stats`);
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            return { success: false, error: error.message };
        }
    }
    
    connectWebSocket(onMessage) {
        const wsURL = this.baseURL.replace('https://', 'wss://');
        this.ws = new WebSocket(`${wsURL}/ws`);
        
        this.ws.onopen = () => {
            console.log('✅ Connected to BaconAlgo');
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
        
        this.ws.onclose = () => {
            console.log('Disconnected. Reconnecting...');
            setTimeout(() => this.connectWebSocket(onMessage), 5000);
        };
    }
}

// Export
window.BaconAPI = BaconAPI;
