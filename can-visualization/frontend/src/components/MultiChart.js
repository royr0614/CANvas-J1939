import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { useSignals } from '../utils/SignalContext';

const MultiChartContainer = styled.div`
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  margin-bottom: 1rem;
`;

const ChartHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const ChartTitle = styled.h3`
  margin: 0;
  font-size: 1.1rem;
`;

const ChartControls = styled.div`
  display: flex;
  gap: 1rem;
`;

const Select = styled.select`
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
`;

const Button = styled.button`
  background-color: ${props => props.primary ? '#2196f3' : props.danger ? '#f44336' : '#e0e0e0'};
  color: ${props => (props.primary || props.danger) ? 'white' : 'black'};
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  
  &:hover {
    background-color: ${props => props.primary ? '#1976d2' : props.danger ? '#d32f2f' : '#bdbdbd'};
  }
`;

const ChartContent = styled.div`
  height: 400px;
  width: 100%;
`;

const SignalSelector = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
`;

const SignalChip = styled.div`
  display: flex;
  align-items: center;
  background-color: #e3f2fd;
  border-radius: 16px;
  padding: 0.25rem 0.75rem;
  font-size: 0.9rem;
  user-select: none;
  color: ${props => props.color};
  border: 1px solid ${props => props.color};
`;

const RemoveButton = styled.button`
  background: none;
  border: none;
  color: #616161;
  margin-left: 0.5rem;
  cursor: pointer;
  padding: 0;
  font-size: 1rem;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  
  &:hover {
    color: #d32f2f;
  }
`;

const EmptyState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9e9e9e;
  text-align: center;
`;

// Chart colors for multiple lines
const CHART_COLORS = [
  '#2196f3', // Blue
  '#f44336', // Red
  '#4caf50', // Green
  '#ff9800', // Orange
  '#9c27b0', // Purple
  '#00bcd4', // Cyan
  '#ff5722', // Deep Orange
  '#673ab7', // Deep Purple
  '#8bc34a', // Light Green
  '#3f51b5', // Indigo
];

// Custom tooltip
const CustomTooltip = ({ active, payload, label, labelFormatter }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ 
        backgroundColor: 'white', 
        padding: '0.5rem', 
        border: '1px solid #e0e0e0',
        borderRadius: '4px',
        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
      }}>
        <p style={{ margin: '0 0 0.5rem 0' }}>{labelFormatter(label)}</p>
        {payload.map((entry, index) => (
          <p key={`item-${index}`} style={{ margin: 0, color: entry.color }}>
            <span style={{ marginRight: '0.5rem' }}>{entry.name}:</span>
            <span style={{ fontWeight: 'bold' }}>
              {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
            </span>
          </p>
        ))}
      </div>
    );
  }

  return null;
};

const MultiChart = () => {
  const { signalHistory, availableSignals, status } = useSignals();
  const [selectedSignals, setSelectedSignals] = useState([]);
  const [newSignal, setNewSignal] = useState('');
  const [timeWindow, setTimeWindow] = useState(60); // seconds
  const [chartData, setChartData] = useState([]);
  
  // Update chart data when signal histories change
  useEffect(() => {
    if (selectedSignals.length === 0 || Object.keys(signalHistory).length === 0) {
      setChartData([]);
      return;
    }
    
    // Get all timestamps from all selected signals
    const allTimestamps = new Set();
    
    selectedSignals.forEach(signalId => {
      if (signalHistory[signalId]) {
        signalHistory[signalId].timestamps.forEach(timestamp => {
          allTimestamps.add(timestamp);
        });
      }
    });
    
    // Convert to array and sort
    const timestamps = Array.from(allTimestamps).sort();
    
    // Create chart data with all signals
    const data = timestamps.map(timestamp => {
      const dataPoint = { time: timestamp };
      
      selectedSignals.forEach(signalId => {
        if (!signalHistory[signalId]) return;
        
        const { timestamps: signalTimestamps, values: signalValues } = signalHistory[signalId];
        
        // Find the closest timestamp (exact or just before)
        let valueIndex = -1;
        for (let i = 0; i < signalTimestamps.length; i++) {
          if (signalTimestamps[i] <= timestamp) {
            valueIndex = i;
          } else {
            break;
          }
        }
        
        // If found, add to data point
        if (valueIndex >= 0) {
          dataPoint[signalId] = signalValues[valueIndex];
        }
      });
      
      return dataPoint;
    });
    
    setChartData(data);
  }, [selectedSignals, signalHistory]);
  
  // When availableSignals changes, set the first one as the new signal option
  useEffect(() => {
    if (availableSignals.length > 0 && !newSignal) {
      const firstSignal = availableSignals[0];
      setNewSignal(`${firstSignal.message}.${firstSignal.name}`);
    }
  }, [availableSignals, newSignal]);
  
  const handleAddSignal = () => {
    if (!newSignal || selectedSignals.includes(newSignal)) return;
    
    // Maximum 10 signals (corresponding to colors array)
    if (selectedSignals.length >= 10) {
      alert('Maximum 10 signals can be displayed at once.');
      return;
    }
    
    setSelectedSignals([...selectedSignals, newSignal]);
  };
  
  const handleRemoveSignal = (signalId) => {
    setSelectedSignals(selectedSignals.filter(id => id !== signalId));
  };
  
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };
  
  // Get signal name for display
  const getSignalName = (signalId) => {
    const [msgName, sigName] = signalId.split('.');
    return `${msgName}.${sigName}`;
  };
  
  // Find unit for a signal
  const getSignalUnit = (signalId) => {
    const [msgName, sigName] = signalId.split('.');
    const signal = availableSignals.find(s => s.message === msgName && s.name === sigName);
    return signal?.unit || '';
  };
  
  // Filter data based on time window
  const filterDataByTimeWindow = () => {
    if (!chartData.length) return [];
    
    const now = Math.max(...chartData.map(d => d.time));
    const cutoff = now - timeWindow;
    
    return chartData.filter(d => d.time >= cutoff);
  };
  
  const filteredData = filterDataByTimeWindow();
  
  return (
    <MultiChartContainer>
      <ChartHeader>
        <ChartTitle>Multi Signal Chart</ChartTitle>
        <ChartControls>
          <div>
            <Select
              value={timeWindow}
              onChange={(e) => setTimeWindow(Number(e.target.value))}
            >
              <option value={10}>10 seconds</option>
              <option value={30}>30 seconds</option>
              <option value={60}>1 minute</option>
              <option value={300}>5 minutes</option>
              <option value={600}>10 minutes</option>
            </Select>
          </div>
        </ChartControls>
      </ChartHeader>
      
      <SignalSelector>
        <div>
          <Select
            value={newSignal}
            onChange={(e) => setNewSignal(e.target.value)}
            disabled={availableSignals.length === 0}
          >
            {availableSignals.length === 0 ? (
              <option value="">No signals available</option>
            ) : (
              availableSignals.map(signal => (
                <option 
                  key={`${signal.message}.${signal.name}`} 
                  value={`${signal.message}.${signal.name}`}
                >
                  {signal.message} - {signal.name}
                </option>
              ))
            )}
          </Select>
        </div>
        <Button 
          primary 
          onClick={handleAddSignal}
          disabled={!newSignal || selectedSignals.includes(newSignal)}
        >
          Add Signal
        </Button>
        
        {selectedSignals.length > 0 && (
          <Button 
            danger
            onClick={() => setSelectedSignals([])}
          >
            Clear All
          </Button>
        )}
      </SignalSelector>
      
      {selectedSignals.length > 0 && (
        <SignalSelector>
          {selectedSignals.map((signalId, index) => (
            <SignalChip 
              key={signalId} 
              color={CHART_COLORS[index % CHART_COLORS.length]}
            >
              {getSignalName(signalId)}
              <RemoveButton onClick={() => handleRemoveSignal(signalId)}>×</RemoveButton>
            </SignalChip>
          ))}
        </SignalSelector>
      )}
      
      <ChartContent>
        {filteredData.length > 0 && selectedSignals.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={filteredData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                tickFormatter={formatTimestamp}
                domain={['dataMin', 'dataMax']}
                type="number"
              />
              <YAxis 
                domain={['auto', 'auto']}
              />
              <Tooltip 
                content={<CustomTooltip />}
                labelFormatter={formatTimestamp}
              />
              <Legend />
              {selectedSignals.map((signalId, index) => (
                <Line 
                  key={signalId}
                  type="monotone" 
                  dataKey={signalId} 
                  name={getSignalName(signalId)} 
                  stroke={CHART_COLORS[index % CHART_COLORS.length]}
                  dot={false}
                  activeDot={{ r: 4 }}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : selectedSignals.length === 0 ? (
          <EmptyState>
            No signals selected.
            <br />
            Please add signals using the controls above.
          </EmptyState>
        ) : status.running ? (
          <EmptyState>
            No data available for the selected signals.
            <br />
            Waiting for updates...
          </EmptyState>
        ) : (
          <EmptyState>
            No signal data available.
            <br />
            Please start the CAN simulation.
          </EmptyState>
        )}
      </ChartContent>
    </MultiChartContainer>
  );
};

export default MultiChart;