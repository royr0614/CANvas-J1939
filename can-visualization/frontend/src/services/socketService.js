import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.listeners = {
      connect: [],
      disconnect: [],
      status: [],
      signal_update: []
    };
  }

  connect(url) {
    if (this.socket) {
      return;
    }
    
    this.socket = io(url || 'http://localhost:5000');
    
    // Set up event listeners
    this.socket.on('connect', () => {
      console.log('Connected to WebSocket server');
      this._notifyListeners('connect');
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket server');
      this._notifyListeners('disconnect');
    });

    this.socket.on('status', (data) => {
      this._notifyListeners('status', data);
    });

    this.socket.on('signal_update', (data) => {
      this._notifyListeners('signal_update', data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  addListener(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
    
    return () => this.removeListener(event, callback);
  }

  removeListener(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  _notifyListeners(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  isConnected() {
    return this.socket?.connected || false;
  }
}

// Create a singleton instance
const socketService = new SocketService();
export default socketService;