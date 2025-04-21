import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Responsive, WidthProvider } from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import GaugeWidget from './GaugeWidget';
import SignalChart from './SignalChart';
import MultiChart from './MultiChart';
import { useSignals } from '../utils/SignalContext';

// Responsive grid layout with width provider
const ResponsiveGridLayout = WidthProvider(Responsive);

const DashboardContainer = styled.div`
  padding: 1rem;
`;

const ControlsContainer = styled.div`
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
`;

const Button = styled.button`
  background-color: ${props => props.primary ? '#2196f3' : props.danger ? '#f44336' : '#e0e0e0'};
  color: ${props => (props.primary || props.danger) ? 'white' : 'black'};
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  font-weight: 500;
  cursor: pointer;
  
  &:hover {
    background-color: ${props => props.primary ? '#1976d2' : props.danger ? '#d32f2f' : '#bdbdbd'};
  }
`;

const Select = styled.select`
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
  min-width: 200px;
`;

const EmptyState = styled.div`
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  text-align: center;
  color: #9e9e9e;
`;

// Widget configuration modal
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: white;
  border-radius: 4px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  padding: 1.5rem;
  width: 100%;
  max-width: 500px;
`;

const ModalTitle = styled.h3`
  margin-top: 0;
  margin-bottom: 1rem;
`;

const FormGroup = styled.div`
  margin-bottom: 1rem;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
`;

const ModalActions = styled.div`
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
`;

// Default layouts for different screen sizes
const defaultLayouts = {
  lg: [
    { i: 'chart1', x: 0, y: 0, w: 12, h: 8, minW: 6, minH: 4 },
    { i: 'multichart', x: 0, y: 8, w: 12, h: 10, minW: 6, minH: 4 },
    { i: 'gauge1', x: 0, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge2', x: 3, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge3', x: 6, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge4', x: 9, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
  ],
  md: [
    { i: 'chart1', x: 0, y: 0, w: 12, h: 8, minW: 6, minH: 4 },
    { i: 'multichart', x: 0, y: 8, w: 12, h: 10, minW: 6, minH: 4 },
    { i: 'gauge1', x: 0, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge2', x: 3, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge3', x: 6, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge4', x: 9, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
  ],
  sm: [
    { i: 'chart1', x: 0, y: 0, w: 6, h: 8, minW: 6, minH: 4 },
    { i: 'multichart', x: 0, y: 8, w: 6, h: 10, minW: 6, minH: 4 },
    { i: 'gauge1', x: 0, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge2', x: 3, y: 18, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge3', x: 0, y: 24, w: 3, h: 6, minW: 3, minH: 6 },
    { i: 'gauge4', x: 3, y: 24, w: 3, h: 6, minW: 3, minH: 6 },
  ],
  xs: [
    { i: 'chart1', x: 0, y: 0, w: 4, h: 8, minW: 4, minH: 4 },
    { i: 'multichart', x: 0, y: 8, w: 4, h: 10, minW: 4, minH: 4 },
    { i: 'gauge1', x: 0, y: 18, w: 2, h: 6, minW: 2, minH: 6 },
    { i: 'gauge2', x: 2, y: 18, w: 2, h: 6, minW: 2, minH: 6 },
    { i: 'gauge3', x: 0, y: 24, w: 2, h: 6, minW: 2, minH: 6 },
    { i: 'gauge4', x: 2, y: 24, w: 2, h: 6, minW: 2, minH: 6 },
  ],
};

// Default widget configurations
const defaultWidgetConfigs = {
  chart1: {
    type: 'chart',
    title: 'Signal Chart',
    signalId: '',
  },
  multichart: {
    type: 'multichart',
    title: 'Multi Signal Chart',
  },
  gauge1: {
    type: 'gauge',
    title: 'Engine Speed',
    signalId: '',
    min: 0,
    max: 8000,
  },
  gauge2: {
    type: 'gauge',
    title: 'Vehicle Speed',
    signalId: '',
    min: 0,
    max: 120,
  },
  gauge3: {
    type: 'gauge',
    title: 'Gauge 3',
    signalId: '',
    min: 0,
    max: 100,
  },
  gauge4: {
    type: 'gauge',
    title: 'Gauge 4',
    signalId: '',
    min: 0,
    max: 100,
  },
};

const Dashboard = () => {
  const { availableSignals, status } = useSignals();
  const [layouts, setLayouts] = useState(defaultLayouts);
  const [widgetConfigs, setWidgetConfigs] = useState(defaultWidgetConfigs);
  const [editingWidget, setEditingWidget] = useState(null);
  const [editConfig, setEditConfig] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  
  // Load dashboard configuration from localStorage
  useEffect(() => {
    try {
      const savedLayouts = localStorage.getItem('canvis_layouts');
      const savedConfigs = localStorage.getItem('canvis_widget_configs');
      
      if (savedLayouts) {
        setLayouts(JSON.parse(savedLayouts));
      }
      
      if (savedConfigs) {
        setWidgetConfigs(JSON.parse(savedConfigs));
      }
    } catch (error) {
      console.error('Error loading saved dashboard:', error);
    }
  }, []);
  
  // Save dashboard configuration to localStorage
  const saveDashboard = () => {
    try {
      localStorage.setItem('canvis_layouts', JSON.stringify(layouts));
      localStorage.setItem('canvis_widget_configs', JSON.stringify(widgetConfigs));
      alert('Dashboard saved successfully!');
    } catch (error) {
      console.error('Error saving dashboard:', error);
      alert('Error saving dashboard: ' + error.message);
    }
  };
  
  // Reset to default dashboard
  const resetDashboard = () => {
    if (window.confirm('Are you sure you want to reset the dashboard to default?')) {
      setLayouts(defaultLayouts);
      setWidgetConfigs(defaultWidgetConfigs);
      localStorage.removeItem('canvis_layouts');
      localStorage.removeItem('canvis_widget_configs');
    }
  };
  
  // Handle layout changes
  const handleLayoutChange = (currentLayout, allLayouts) => {
    setLayouts(allLayouts);
  };
  
  // Open widget configuration modal
  const openWidgetConfig = (widgetId) => {
    setEditingWidget(widgetId);
    setEditConfig(widgetConfigs[widgetId] || {});
    setIsEditing(true);
  };
  
  // Close widget configuration modal
  const closeWidgetConfig = () => {
    setIsEditing(false);
    setEditingWidget(null);
    setEditConfig({});
  };
  
  // Save widget configuration
  const saveWidgetConfig = () => {
    if (!editingWidget) return;
    
    setWidgetConfigs({
      ...widgetConfigs,
      [editingWidget]: editConfig
    });
    
    closeWidgetConfig();
  };
  
  // Handle input changes in config modal
  const handleConfigChange = (e) => {
    const { name, value, type } = e.target;
    
    setEditConfig({
      ...editConfig,
      [name]: type === 'number' ? Number(value) : value
    });
  };
  
  // Render widget based on its configuration
  const renderWidget = (widgetId) => {
    const config = widgetConfigs[widgetId] || {};
    
    switch (config.type) {
      case 'gauge':
        return (
          <GaugeWidget
            signalId={config.signalId}
            title={config.title}
            min={config.min}
            max={config.max}
          />
        );
      case 'chart':
        return <SignalChart />;
      case 'multichart':
        return <MultiChart />;
      default:
        return (
          <div style={{ padding: '1rem', textAlign: 'center' }}>
            <p>Unconfigured Widget</p>
            <Button onClick={() => openWidgetConfig(widgetId)}>Configure</Button>
          </div>
        );
    }
  };
  
  return (
    <DashboardContainer>
      <ControlsContainer>
        <Button primary onClick={() => setIsEditing(!isEditing)}>
          {isEditing ? 'Exit Edit Mode' : 'Edit Dashboard'}
        </Button>
        
        {isEditing && (
          <>
            <Button onClick={saveDashboard}>Save Dashboard</Button>
            <Button danger onClick={resetDashboard}>Reset to Default</Button>
          </>
        )}
      </ControlsContainer>
      
      {status.dbcLoaded ? (
        <ResponsiveGridLayout
          className="layout"
          layouts={layouts}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480 }}
          cols={{ lg: 12, md: 12, sm: 6, xs: 4 }}
          rowHeight={30}
          isResizable={isEditing}
          isDraggable={isEditing}
          onLayoutChange={handleLayoutChange}
        >
          {Object.keys(layouts.lg).map(i => {
            const id = layouts.lg[i].i;
            return (
              <div key={id} data-grid={layouts.lg[i]}>
                {isEditing && (
                  <div style={{ 
                    position: 'absolute', 
                    top: '5px', 
                    right: '5px', 
                    zIndex: 1, 
                    padding: '5px',
                    background: 'rgba(255, 255, 255, 0.8)',
                    borderRadius: '4px'
                  }}>
                    <Button onClick={() => openWidgetConfig(id)}>Configure</Button>
                  </div>
                )}
                {renderWidget(id)}
              </div>
            );
          })}
        </ResponsiveGridLayout>
      ) : (
        <EmptyState>
          <h3>No DBC file loaded</h3>
          <p>Please load a DBC file first to configure the dashboard.</p>
        </EmptyState>
      )}
      
      {/* Widget Configuration Modal */}
      {isEditing && editingWidget && (
        <ModalOverlay>
          <ModalContent>
            <ModalTitle>Configure Widget: {editingWidget}</ModalTitle>
            
            <FormGroup>
              <Label htmlFor="type">Widget Type</Label>
              <Select
                id="type"
                name="type"
                value={editConfig.type || ''}
                onChange={handleConfigChange}
              >
                <option value="">Select Widget Type</option>
                <option value="gauge">Gauge</option>
                <option value="chart">Chart</option>
                <option value="multichart">Multi Chart</option>
              </Select>
            </FormGroup>
            
            <FormGroup>
              <Label htmlFor="title">Title</Label>
              <Input
                id="title"
                name="title"
                value={editConfig.title || ''}
                onChange={handleConfigChange}
                placeholder="Widget Title"
              />
            </FormGroup>
            
            {(editConfig.type === 'gauge' || editConfig.type === 'chart') && (
              <FormGroup>
                <Label htmlFor="signalId">Signal</Label>
                <Select
                  id="signalId"
                  name="signalId"
                  value={editConfig.signalId || ''}
                  onChange={handleConfigChange}
                >
                  <option value="">Select Signal</option>
                  {availableSignals.map(signal => (
                    <option 
                      key={`${signal.message}.${signal.name}`} 
                      value={`${signal.message}.${signal.name}`}
                    >
                      {signal.message} - {signal.name}
                    </option>
                  ))}
                </Select>
              </FormGroup>
            )}
            
            {editConfig.type === 'gauge' && (
              <>
                <FormGroup>
                  <Label htmlFor="min">Minimum Value</Label>
                  <Input
                    id="min"
                    name="min"
                    type="number"
                    value={editConfig.min || 0}
                    onChange={handleConfigChange}
                  />
                </FormGroup>
                
                <FormGroup>
                  <Label htmlFor="max">Maximum Value</Label>
                  <Input
                    id="max"
                    name="max"
                    type="number"
                    value={editConfig.max || 100}
                    onChange={handleConfigChange}
                  />
                </FormGroup>
              </>
            )}
            
            <ModalActions>
              <Button onClick={closeWidgetConfig}>Cancel</Button>
              <Button primary onClick={saveWidgetConfig}>Save</Button>
            </ModalActions>
          </ModalContent>
        </ModalOverlay>
      )}
    </DashboardContainer>
  );
};

export default Dashboard;