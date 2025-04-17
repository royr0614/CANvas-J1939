import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import DashboardBuilder from './components/DashboardBuilder';
import DashboardView from './components/DashboardView';
import { SignalProvider } from './utils/SignalContext';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
`;

const Header = styled.header`
  background-color: #2a2a2a;
  color: white;
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Title = styled.h1`
  margin: 0;
  font-size: 1.2rem;
`;

const TabsContainer = styled.div`
  display: flex;
  gap: 1rem;
`;

const Tab = styled.button`
  background-color: ${props => props.active ? '#4a90e2' : 'transparent'};
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: ${props => props.active ? 'bold' : 'normal'};
  border-radius: 4px;
  
  &:hover {
    background-color: ${props => props.active ? '#4a90e2' : '#3a3a3a'};
  }
`;

const Content = styled.main`
  flex: 1;
  overflow: auto;
  background-color: #f5f5f5;
`;

function App() {
  const [activeTab, setActiveTab] = useState('view');
  const [signals, setSignals] = useState({});
  const [dashboardConfig, setDashboardConfig] = useState({
    name: 'Default Dashboard',
    layout: [],
    widgets: {}
  });

  // Connect to PyQt bridge when available
  useEffect(() => {
    // Wait for QWebChannel to be available (injected by PyQt)
    window.onload = () => {
      if (window.QWebChannel) {
        new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
          const bridge = channel.objects.bridge;
          
          // Listen for signal updates
          bridge.signalUpdated.connect((signalJson) => {
            const signalData = JSON.parse(signalJson);
            setSignals(prev => ({
              ...prev,
              [signalData.id]: {
                ...prev[signalData.id],
                current: signalData.value,
                timestamp: signalData.timestamp,
                message: signalData.message,
                signal: signalData.signal,
                interface: signalData.interface
              }
            }));
          });
          
          // Store bridge for sending data back
          window.canBridge = bridge;
          console.log('Connected to PyQt bridge');
        });
      } else {
        console.log('QWebChannel not available - running in standalone mode');
        
        // Mock signal data for standalone testing
        const mockInterval = setInterval(() => {
          const mockSignals = {
            'EEC1.EngineSpeed': {
              current: Math.random() * 3000,
              timestamp: Date.now(),
              message: 'EEC1',
              signal: 'EngineSpeed',
              interface: 'simulator'
            },
            'CCVS1.WheelBasedVehicleSpeed': {
              current: Math.random() * 100,
              timestamp: Date.now(),
              message: 'CCVS1',
              signal: 'WheelBasedVehicleSpeed',
              interface: 'simulator'
            }
          };
          
          setSignals(prev => ({...prev, ...mockSignals}));
        }, 1000);
        
        return () => clearInterval(mockInterval);
      }
    };
  }, []);

  const saveConfig = (config) => {
    setDashboardConfig(config);
    // Save to PyQt if bridge is available
    if (window.canBridge) {
      window.canBridge.saveConfig(JSON.stringify(config));
    }
  };

  return (
    <SignalProvider value={{ signals }}>
      <AppContainer>
        <Header>
          <Title>CAN Dashboard</Title>
          <TabsContainer>
            <Tab 
              active={activeTab === 'view'} 
              onClick={() => setActiveTab('view')}
            >
              Dashboard
            </Tab>
            <Tab 
              active={activeTab === 'edit'} 
              onClick={() => setActiveTab('edit')}
            >
              Edit Dashboard
            </Tab>
          </TabsContainer>
        </Header>
        <Content>
          {activeTab === 'view' ? (
            <DashboardView config={dashboardConfig} />
          ) : (
            <DashboardBuilder 
              config={dashboardConfig} 
              onSave={saveConfig} 
            />
          )}
        </Content>
      </AppContainer>
    </SignalProvider>
  );
}

export default App;
