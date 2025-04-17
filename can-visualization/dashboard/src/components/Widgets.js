import React, { useContext, useEffect, useState } from 'react';
import styled, { css } from 'styled-components';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import SignalContext from '../utils/SignalContext';

// Shared styles for widget cards
export const WidgetCard = styled.div`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  ${props => props.isSelected && css`
    outline: 2px solid #4a90e2;
    box-shadow: 0 0 0 4px rgba(74, 144, 226, 0.3);
  `}
`;

const WidgetTitle = styled.h3`
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const WidgetContent = styled.div`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
`;

// Value Widget
const ValueDisplay = styled.div`
  font-size: 2.5rem;
  font-weight: bold;
  color: #2a2a2a;
  display: flex;
  align-items: baseline;
`;

const ValueUnit = styled.span`
  font-size: 1rem;
  color: #666;
  margin-left: 0.5rem;
`;

export function ValueWidget({ title, value, unit, precision = 1, isSelected }) {
  const formattedValue = typeof value === 'number' ? value.toFixed(precision) : value;
  
  return (
    <WidgetCard isSelected={isSelected}>
      <WidgetTitle>{title}</WidgetTitle>
      <WidgetContent>
        <ValueDisplay>
          {formattedValue}
          {unit && <ValueUnit>{unit}</ValueUnit>}
        </ValueDisplay>
      </WidgetContent>
    </WidgetCard>
  );
}

// Gauge Widget
const GaugeContainer = styled.div`
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

const GaugeSvg = styled.svg`
  transform: rotate(-90deg);
`;

const GaugeValue = styled.div`
  position: absolute;
  bottom: 0;
  font-size: 1.5rem;
  font-weight: bold;
  color: #2a2a2a;
  display: flex;
  align-items: baseline;
`;

export function GaugeWidget({ title, value, min = 0, max = 100, unit = '', isSelected }) {
  // Normalize value between 0 and 1
  const normalizedValue = Math.min(Math.max((value - min) / (max - min), 0), 1);
  
  // Convert to percentage for the gauge
  const percentage = normalizedValue * 100;
  
  // Calculate colors based on value (green to yellow to red)
  const getColor = (percent) => {
    if (percent < 50) return `hsl(${120 - percent * 1.2}, 100%, 45%)`;
    if (percent < 75) return `hsl(${60 - (percent - 50) * 2.4}, 100%, 45%)`;
    return `hsl(0, 100%, ${50 - (percent - 75) * 0.2}%)`;
  };
  
  // SVG parameters
  const radius = 40;
  const strokeWidth = 10;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75; // 270 degrees arc
  const strokeDasharray = `${arcLength} ${circumference}`;
  const strokeDashoffset = arcLength - (normalizedValue * arcLength);
  
  return (
    <WidgetCard isSelected={isSelected}>
      <WidgetTitle>{title}</WidgetTitle>
      <WidgetContent>
        <GaugeContainer>
          <GaugeSvg width="100%" height="100%" viewBox="0 0 100 100">
            {/* Background arc */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke="#e6e6e6"
              strokeWidth={strokeWidth}
              strokeDasharray={strokeDasharray}
              strokeLinecap="round"
            />
            
            {/* Value arc */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke={getColor(percentage)}
              strokeWidth={strokeWidth}
              strokeDasharray={strokeDasharray}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
            />
          </GaugeSvg>
          
          <GaugeValue>
            {value.toFixed(1)}
            {unit && <ValueUnit>{unit}</ValueUnit>}
          </GaugeValue>
        </GaugeContainer>
      </WidgetContent>
    </WidgetCard>
  );
}

// Chart Widget
const ChartContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
`;

export function ChartWidget({ title, signalId, unit = '', isSelected }) {
  const { signals } = useContext(SignalContext);
  const [chartData, setChartData] = useState([]);
  
  useEffect(() => {
    // If we have signal data, update chart
    if (signals[signalId]) {
      const now = Date.now();
      const newPoint = {
        time: now,
        value: signals[signalId].current
      };
      
      setChartData(prev => {
        const newData = [...prev, newPoint];
        // Keep only last 50 points
        if (newData.length > 50) {
          return newData.slice(-50);
        }
        return newData;
      });
    }
  }, [signals, signalId]);
  
  return (
    <WidgetCard isSelected={isSelected}>
      <WidgetTitle>{title}</WidgetTitle>
      <ChartContainer>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="time" 
              type="number"
              domain={['auto', 'auto']}
              tickFormatter={(value) => new Date(value).toLocaleTimeString()}
              scale="time"
              tick={{ fontSize: 10 }}
            />
            <YAxis 
              tick={{ fontSize: 10 }}
              unit={unit}
            />
            <Tooltip 
              labelFormatter={(value) => new Date(value).toLocaleTimeString()}
              formatter={(value) => [value.toFixed(2) + (unit ? ` ${unit}` : ''), title]}
            />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="#4a90e2" 
              dot={false} 
              isAnimationActive={false} 
            />
          </LineChart>
        </ResponsiveContainer>
      </ChartContainer>
    </WidgetCard>
  );
}
