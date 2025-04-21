import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { useSignals } from '../utils/SignalContext';

const ChartContainer = styled.div`
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
  background-color: ${props => props.primary ? '#2196f3' : '#e0e0e0'};
  color: ${props => props.primary ? 'white' : 'black'};
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  cursor: pointer;
  
  &:hover {
    background-color: ${props => props.primary ? '#1976d2' : '#bdbdbd'};
  }
`;

const ChartContent = styled.div`
  height: 300px;
  width: 100%;
`;

const EmptyState = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9e9e9e;
  text-align: center;
`;

// Custom tooltip component
const CustomTooltip = ({ active, payload, label, labelFormatter, formatter }) => {
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
              {formatter ? formatter(entry.value) : entry.value}
            </span>
          </p>
        ))}
      </div>
    );
  }

  return null;
};

const SignalChart = () => {
  const { signalHistory, availableSignals, status } = useSignals();
  const [selectedSignal, setSelectedSignal] = useState('');
  const [chartData, setChartData] = useState([]);
  const [timeWindow, setTimeWindow] = useState(60); // seconds
  
  // Find selected signal details
  const signalDetails = availableSignals.find(s => {
    const [msgName, sigName] = selectedSignal.split('.');
    return s.message === msgName && s.name === sigName;
  });
  
  // Update chart data when signal history changes
  useEffect(() => {
    if (selectedSignal && signalHistory[selectedSignal]) {
      const { timestamps, values } = signalHistory[selectedSignal];
      
      // Create data points for the chart
      const data = timestamps.map((timestamp, index) => ({
        time: timestamp,
        value: values[index]
      }));
      
      setChartData(data);
    } else {
      setChartData([]);
    }
  }, [selectedSignal, signalHistory]);
  
  // When availableSignals changes, set the first one as selected if nothing is selected
  useEffect(() => {
    if (availableSignals.length > 0 && !selectedSignal) {
      const firstSignal = availableSignals[0];
      setSelectedSignal(`${firstSignal.message}.${firstSignal.name}`);
    }
  }, [availableSignals, selectedSignal]);
  
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };
  
  const formatValue = (value) => {
    if (typeof value === 'number') {
      return value.toFixed(2) + (signalDetails?.unit ? ` ${signalDetails.unit}` : '');
    }
    return value;
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
    <ChartContainer>
      <ChartHeader>
        <ChartTitle>Signal Chart</ChartTitle>
        <ChartControls>
          <div>
            <Select
              value={selectedSignal}
              onChange={(e) => setSelectedSignal(e.target.value)}
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
      
      <ChartContent>
        {filteredData.length > 0 ? (
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
                domain={[
                  dataMin => Math.floor(dataMin * 0.9), 
                  dataMax => Math.ceil(dataMax * 1.1)
                ]}
                label={{ 
                  value: signalDetails?.unit || 'Value', 
                  angle: -90, 
                  position: 'insideLeft' 
                }}
              />
              <Tooltip 
                content={<CustomTooltip />}
                labelFormatter={formatTimestamp}
                formatter={formatValue}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="value" 
                name={selectedSignal} 
                stroke="#2196f3" 
                dot={false} 
                activeDot={{ r: 4 }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : status.running ? (
          <EmptyState>
            No data available for the selected signal.
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
    </ChartContainer>
  );
};

export default SignalChart;