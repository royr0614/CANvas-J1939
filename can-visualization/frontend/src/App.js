import React, { useState } from 'react';
import styled from 'styled-components';
import { SignalProvider } from './utils/SignalContext';
import ControlPanel from './components/ControlPanel';
import SignalTable from './components/SignalTable';
import SignalChart from './components/SignalChart';
import MultiChart from './components/MultiChart';
import Dashboard from './components/Dashboard';

const AppContainer = styled.div`
  min-height: 100vh;
  background-color: #f5f5f5;
`;

const Header = styled.header`
  background-color: #2196f3;
  color: white;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const Title = styled.h1`
  margin: 0;
  font-size: 1.5rem;
`;

const Content = styled.main`
  padding: 1rem 2rem;
`;

const TabsContainer = styled.div`
  display: flex;
  margin-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
`;

const Tab = styled.button`
  padding: 0.75rem 1.5rem;
  background-color: ${props => props.active ? 'white' : 'transparent'};
  color: ${props => props.active ? '#2196f3' : '#757575'};
  border: none;
  border-bottom: 3px solid ${props => props.active ? '#2196f3' : 'transparent'};
  font-weight: ${props => props.active ? '500' : 'normal'};
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background-color: ${props => props.active ? 'white' : '#f0f0f0'};
  }
`;

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  return (
    <SignalProvider>
      <AppContainer>
        <Header>
          <Title>CAN Visualization</Title>
        </Header>
        
        <Content>
          <ControlPanel />
          
          <TabsContainer>
            <Tab 
              active={activeTab === 'dashboard'} 
              onClick={() => setActiveTab('dashboard')}
            >
              Dashboard
            </Tab>
            <Tab 
              active={activeTab === 'table'} 
              onClick={() => setActiveTab('table')}
            >
              Signal Table
            </Tab>
            <Tab 
              active={activeTab === 'chart'} 
              onClick={() => setActiveTab('chart')}
            >
              Signal Chart
            </Tab>
            <Tab 
              active={activeTab === 'multichart'} 
              onClick={() => setActiveTab('multichart')}
            >
              Multi Chart
            </Tab>
          </TabsContainer>
          
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'table' && <SignalTable />}
          {activeTab === 'chart' && <SignalChart />}
          {activeTab === 'multichart' && <MultiChart />}
        </Content>
      </AppContainer>
    </SignalProvider>
  );
}

export default App;