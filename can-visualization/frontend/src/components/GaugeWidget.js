import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useSignals } from '../utils/SignalContext';

const GaugeContainer = styled.div`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
`;

const GaugeTitle = styled.h3`
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  text-align: center;
`;

const GaugeWrapper = styled.div`
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 180px;
  height: 180px;
`;

const GaugeSvg = styled.svg`
  transform: rotate(-90deg);
`;

const GaugeValue = styled.div`
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  font-weight: bold;
`;

const GaugeUnit = styled.div`
  font-size: 0.9rem;
  font-weight: normal;
  color: #757575;
  margin-top: 0.25rem;
`;

const GaugeInfo = styled.div`
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #757575;
`;

const GaugeMinMax = styled.div`
  display: flex;
  justify-content: space-between;
  width: 100%;
  margin-top: 0.5rem;
  font-size: 0.9rem;
`;

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9e9e9e;
  text-align: center;
  font-size: 0.9rem;
`;

const GaugeWidget = ({ signalId, min, max, title }) => {
  const { signals, availableSignals } = useSignals();
  const [value, setValue] = useState(null);
  
  // Find signal details
  const [msgName, sigName] = (signalId || '').split('.');
  const signalDetails = availableSignals.find(
    s => s.message === msgName && s.name === sigName
  );
  
  // Set min/max from signal details if not provided
  const minValue = min !== undefined ? min : (signalDetails?.min || 0);
  const maxValue = max !== undefined ? max : (signalDetails?.max || 100);
  const unit = signalDetails?.unit || '';
  
  // Update value when signals change
  useEffect(() => {
    if (signalId && signals[signalId]) {
      setValue(signals[signalId].value);
    }
  }, [signalId, signals]);
  
  // Normalize value for gauge (0 to 1)
  const normalizedValue = value !== null 
    ? Math.min(Math.max((value - minValue) / (maxValue - minValue), 0), 1)
    : 0;
  
  // Get color based on value (green to yellow to red)
  const getGaugeColor = (normalized) => {
    const percent = normalized * 100;
    if (percent < 50) return `hsl(${120 - percent * 1.2}, 100%, 45%)`;
    if (percent < 75) return `hsl(${60 - (percent - 50) * 2.4}, 100%, 45%)`;
    return `hsl(0, 100%, ${50 - (percent - 75) * 0.2}%)`;
  };
  
  // SVG parameters for gauge
  const radius = 70;
  const strokeWidth = 15;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75; // 270 degrees arc
  const strokeDasharray = `${arcLength} ${circumference}`;
  const strokeDashoffset = arcLength - (normalizedValue * arcLength);
  const color = getGaugeColor(normalizedValue);
  
  // Format value for display
  const formatValue = (val) => {
    if (val === null) return '-';
    return typeof val === 'number' ? val.toFixed(1) : val;
  };
  
  return (
    <GaugeContainer>
      <GaugeTitle>{title || signalId || 'Gauge'}</GaugeTitle>
      
      {signalId ? (
        <>
          <GaugeWrapper>
            <GaugeSvg width="180" height="180" viewBox="0 0 180 180">
              {/* Background arc */}
              <circle
                cx="90"
                cy="90"
                r={radius}
                fill="none"
                stroke="#e0e0e0"
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeLinecap="round"
              />
              
              {/* Value arc */}
              <circle
                cx="90"
                cy="90"
                r={radius}
                fill="none"
                stroke={color}
                strokeWidth={strokeWidth}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
              />
            </GaugeSvg>
            
            <GaugeValue>
              {formatValue(value)}
              {unit && <GaugeUnit>{unit}</GaugeUnit>}
            </GaugeValue>
          </GaugeWrapper>
          
          <GaugeMinMax>
            <span>{minValue}</span>
            <span>{maxValue}</span>
          </GaugeMinMax>
          
          <GaugeInfo>
            <span>{msgName}</span>
            <span>{sigName}</span>
          </GaugeInfo>
        </>
      ) : (
        <EmptyState>
          No signal selected.
          <br />
          Please configure this gauge.
        </EmptyState>
      )}
    </GaugeContainer>
  );
};

export default GaugeWidget;