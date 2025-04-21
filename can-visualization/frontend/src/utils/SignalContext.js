import React, { createContext, useState, useEffect, useContext } from 'react';
import socketService from '../services/socketService';
import apiService from '../services/apiService';

const SignalContext = createContext({
  signals: {},         // Current signal values
  signalHistory: {},   // Historical signal data
  availableSignals: [], // Available signals from DBC
  status: {            // Server status
    dbcLoaded: false,
    running: false,
    simulation: false
  },
  loading: false,
  error: null
});

export const SignalProvider = ({ children }) => {
  const [signals, setSignals] = useState({});
  const [signalHistory, setSignalHistory] = useState({});
  const [availableSignals, setAvailableSignals] = useState([]);
  const [status, setStatus] = useState({
    dbcLoaded: false,
    running: false,
    simulation: false
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Connect to WebSocket when component mounts
  useEffect(() => {
    socketService.connect();

    // Handle socket connection events
    const connectHandler = () => {
      fetchStatus();
      fetchAvailableSignals();
    };
    const disconnectHandler = () => {
      console.log('WebSocket disconnected');
    };
    const statusHandler = (data) => {
      setStatus({
        dbcLoaded: data.dbc_loaded,
        running: data.running,
        simulation: data.simulation
      });
    };
    
    // Handle signal updates
    const signalUpdateHandler = (data) => {
      // Update current signal value
      setSignals(prev => ({
        ...prev,
        [data.id]: {
          value: data.value,
          timestamp: data.timestamp,
          messageName: data.message,
          signalName: data.signal,
          interface: data.interface
        }
      }));
      
      // Update signal history
      setSignalHistory(prev => {
        const history = prev[data.id] || { timestamps: [], values: [] };
        
        // Limit history to 1000 points
        const timestamps = [...history.timestamps, data.timestamp];
        const values = [...history.values, data.value];
        
        if (timestamps.length > 1000) {
          timestamps.shift();
          values.shift();
        }
        
        return {
          ...prev,
          [data.id]: {
            timestamps,
            values
          }
        };
      });
    };
    
    // Add socket event listeners
    socketService.addListener('connect', connectHandler);
    socketService.addListener('disconnect', disconnectHandler);
    socketService.addListener('status', statusHandler);
    socketService.addListener('signal_update', signalUpdateHandler);
    
    // Clean up on unmount
    return () => {
      socketService.removeListener('connect', connectHandler);
      socketService.removeListener('disconnect', disconnectHandler);
      socketService.removeListener('status', statusHandler);
      socketService.removeListener('signal_update', signalUpdateHandler);
      socketService.disconnect();
    };
  }, []);

  // Fetch server status
  const fetchStatus = async () => {
    try {
      const data = await apiService.getStatus();
      setStatus({
        dbcLoaded: data.dbc_loaded,
        running: data.running,
        simulation: data.simulation
      });
    } catch (error) {
      setError('Failed to fetch server status');
      console.error(error);
    }
  };

  // Fetch available signals
  const fetchAvailableSignals = async () => {
    if (!status.dbcLoaded) return;
    
    try {
      setLoading(true);
      const signals = await apiService.getSignals();
      setAvailableSignals(signals);
      setLoading(false);
    } catch (error) {
      setError('Failed to fetch available signals');
      setLoading(false);
      console.error(error);
    }
  };

  // Upload DBC file
  const uploadDBC = async (file) => {
    try {
      setLoading(true);
      await apiService.uploadDBC(file);
      await fetchStatus();
      await fetchAvailableSignals();
      setLoading(false);
      return true;
    } catch (error) {
      setError('Failed to upload DBC file');
      setLoading(false);
      console.error(error);
      return false;
    }
  };

  // Start CAN simulation
  const startCAN = async () => {
    try {
      setLoading(true);
      await apiService.startCAN();
      await fetchStatus();
      setLoading(false);
      return true;
    } catch (error) {
      setError('Failed to start CAN simulation');
      setLoading(false);
      console.error(error);
      return false;
    }
  };

  // Stop CAN simulation
  const stopCAN = async () => {
    try {
      setLoading(true);
      await apiService.stopCAN();
      await fetchStatus();
      setLoading(false);
      return true;
    } catch (error) {
      setError('Failed to stop CAN simulation');
      setLoading(false);
      console.error(error);
      return false;
    }
  };

  // Load historical data for specific signals
  const loadSignalHistory = async (signalIds, limit = 100) => {
    try {
      const data = await apiService.getSignalData(signalIds, limit);
      setSignalHistory(prev => ({
        ...prev,
        ...data
      }));
      return data;
    } catch (error) {
      console.error('Failed to load signal history:', error);
      return null;
    }
  };

  // Clear error
  const clearError = () => setError(null);

  return (
    <SignalContext.Provider
      value={{
        signals,
        signalHistory,
        availableSignals,
        status,
        loading,
        error,
        fetchStatus,
        fetchAvailableSignals,
        uploadDBC,
        startCAN,
        stopCAN,
        loadSignalHistory,
        clearError
      }}
    >
      {children}
    </SignalContext.Provider>
  );
};

// Custom hook for using the signal context
export const useSignals = () => useContext(SignalContext);

export default SignalContext;