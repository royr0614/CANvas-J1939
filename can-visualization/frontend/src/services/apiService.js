import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const apiService = {
  // Get server status
  getStatus: async () => {
    try {
      const response = await axios.get(`${API_URL}/status`);
      return response.data;
    } catch (error) {
      console.error('Error fetching status:', error);
      throw error;
    }
  },

  // Get available signals
  getSignals: async () => {
    try {
      const response = await axios.get(`${API_URL}/signals`);
      return response.data.signals;
    } catch (error) {
      console.error('Error fetching signals:', error);
      throw error;
    }
  },

  // Get signal data
  getSignalData: async (signalIds, limit = 100) => {
    try {
      const response = await axios.get(
        `${API_URL}/signals/data?ids=${signalIds.join(',')}&limit=${limit}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching signal data:', error);
      throw error;
    }
  },

  // Upload DBC file
  uploadDBC: async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_URL}/dbc`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading DBC file:', error);
      throw error;
    }
  },

  // Start CAN simulation
  startCAN: async () => {
    try {
      const response = await axios.post(`${API_URL}/start`);
      return response.data;
    } catch (error) {
      console.error('Error starting CAN:', error);
      throw error;
    }
  },

  // Stop CAN simulation
  stopCAN: async () => {
    try {
      const response = await axios.post(`${API_URL}/stop`);
      return response.data;
    } catch (error) {
      console.error('Error stopping CAN:', error);
      throw error;
    }
  },
};

export default apiService;