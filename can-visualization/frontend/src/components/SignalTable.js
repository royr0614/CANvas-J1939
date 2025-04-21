import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useSignals } from '../utils/SignalContext';

const TableContainer = styled.div`
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  margin-bottom: 1rem;
`;

const FilterControls = styled.div`
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background-color: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
`;

const Select = styled.select`
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  min-width: 200px;
`;

const TableScroll = styled.div`
  max-height: 400px;
  overflow-y: auto;
`;

const StyledTable = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const TableHead = styled.thead`
  background-color: #f5f5f5;
`;

const TableBody = styled.tbody``;

const TableRow = styled.tr`
  &:nth-child(even) {
    background-color: #f9f9f9;
  }
  
  &.fresh {
    background-color: #e8f5e9;
  }
  
  transition: background-color 0.3s;
`;

const TableCell = styled.td`
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e0e0e0;
`;

const TableHeader = styled.th`
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
  position: sticky;
  top: 0;
  background-color: #f5f5f5;
`;

const EmptyState = styled.div`
  padding: 2rem;
  text-align: center;
  color: #9e9e9e;
`;

const SignalTable = () => {
  const { signals, availableSignals, status } = useSignals();
  const [messageFilter, setMessageFilter] = useState('all');
  const [interfaceFilter, setInterfaceFilter] = useState('all');
  const [filteredSignals, setFilteredSignals] = useState([]);
  const [freshSignals, setFreshSignals] = useState({});
  
  // Get unique message names and interfaces
  const messageNames = [...new Set(availableSignals.map(signal => signal.message))];
  const interfaces = [...new Set(Object.values(signals).map(signal => signal.interface))].filter(Boolean);
  
  // Filter signals when filter changes
  useEffect(() => {
    const filtered = Object.entries(signals)
      .filter(([id, signal]) => {
        const messageName = signal.messageName;
        const interfaceName = signal.interface;
        
        return (messageFilter === 'all' || messageName === messageFilter) &&
               (interfaceFilter === 'all' || interfaceName === interfaceFilter);
      })
      .map(([id, signal]) => ({
        id,
        ...signal
      }));
    
    setFilteredSignals(filtered);
  }, [signals, messageFilter, interfaceFilter, availableSignals]);
  
  // Handle fresh updates (highlight new values)
  useEffect(() => {
    const timer = {};
    
    // When signals update, mark them as fresh
    Object.keys(signals).forEach(id => {
      if (timer[id]) {
        clearTimeout(timer[id]);
      }
      
      setFreshSignals(prev => ({ ...prev, [id]: true }));
      
      // After 1 second, remove the fresh marking
      timer[id] = setTimeout(() => {
        setFreshSignals(prev => ({ ...prev, [id]: false }));
      }, 1000);
    });
    
    return () => {
      // Clean up timers
      Object.values(timer).forEach(t => clearTimeout(t));
    };
  }, [signals]);
  
  const formatValue = (value) => {
    if (typeof value === 'number') {
      return value.toFixed(2);
    }
    return value;
  };
  
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp * 1000).toLocaleTimeString();
  };
  
  // Find signal unit from available signals
  const getSignalUnit = (id) => {
    const signalParts = id.split('.');
    if (signalParts.length !== 2) return '';
    
    const [messageName, signalName] = signalParts;
    const signal = availableSignals.find(s => s.message === messageName && s.name === signalName);
    return signal?.unit || '';
  };
  
  return (
    <TableContainer>
      <FilterControls>
        <div>
          <label htmlFor="message-filter">Filter by Message: </label>
          <Select
            id="message-filter"
            value={messageFilter}
            onChange={(e) => setMessageFilter(e.target.value)}
          >
            <option value="all">All Messages</option>
            {messageNames.map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </Select>
        </div>
        
        {interfaces.length > 0 && (
          <div>
            <label htmlFor="interface-filter">Filter by Interface: </label>
            <Select
              id="interface-filter"
              value={interfaceFilter}
              onChange={(e) => setInterfaceFilter(e.target.value)}
            >
              <option value="all">All Interfaces</option>
              {interfaces.map(name => (
                <option key={name} value={name}>{name}</option>
              ))}
            </Select>
          </div>
        )}
      </FilterControls>
      
      <TableScroll>
        <StyledTable>
          <TableHead>
            <tr>
              <TableHeader>Message</TableHeader>
              <TableHeader>Signal</TableHeader>
              <TableHeader>Value</TableHeader>
              <TableHeader>Unit</TableHeader>
              <TableHeader>Interface</TableHeader>
              <TableHeader>Last Update</TableHeader>
            </tr>
          </TableHead>
          <TableBody>
            {filteredSignals.length > 0 ? (
              filteredSignals.map(signal => (
                <TableRow
                  key={signal.id}
                  className={freshSignals[signal.id] ? 'fresh' : ''}
                >
                  <TableCell>{signal.messageName}</TableCell>
                  <TableCell>{signal.signalName}</TableCell>
                  <TableCell>{formatValue(signal.value)}</TableCell>
                  <TableCell>{getSignalUnit(signal.id)}</TableCell>
                  <TableCell>{signal.interface}</TableCell>
                  <TableCell>{formatTimestamp(signal.timestamp)}</TableCell>
                </TableRow>
              ))
            ) : status.running ? (
              <TableRow>
                <TableCell colSpan={6}>
                  <EmptyState>
                    Waiting for signals...
                  </EmptyState>
                </TableCell>
              </TableRow>
            ) : (
              <TableRow>
                <TableCell colSpan={6}>
                  <EmptyState>
                    No signals available. Please start the CAN simulation.
                  </EmptyState>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </StyledTable>
      </TableScroll>
    </TableContainer>
  );
};

export default SignalTable;