import React, { useState } from 'react';
import styled from 'styled-components';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { WidgetCard, ValueWidget, GaugeWidget, ChartWidget } from './Widgets';

const Container = styled.div`
  display: flex;
  height: 100%;
`;

const Sidebar = styled.div`
  width: 300px;
  background-color: #f0f0f0;
  border-right: 1px solid #ddd;
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;

const Canvas = styled.div`
  flex: 1;
  padding: 1rem;
  overflow: auto;
`;

const Section = styled.div`
  margin-bottom: 1.5rem;
`;

const SectionTitle = styled.h3`
  margin-top: 0;
  font-size: 1rem;
  color: #333;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
`;

const Select = styled.select`
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
`;

const Button = styled.button`
  background-color: #4a90e2;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: bold;
  border-radius: 4px;
  margin-bottom: 0.5rem;
  
  &:hover {
    background-color: #2a70c2;
  }
  
  &.secondary {
    background-color: #6c757d;
    
    &:hover {
      background-color: #5a6268;
    }
  }
  
  &.danger {
    background-color: #dc3545;
    
    &:hover {
      background-color: #bd2130;
    }
  }
`;

const WidgetItem = styled.div`
  margin-bottom: 0.5rem;
  padding: 0.5rem;
  background-color: #fff;
  border: 1px solid #ddd;
  cursor: pointer;
  border-radius: 4px;
  
  &:hover {
    background-color: #f8f9fa;
    border-color: #adb5bd;
  }
`;

function DashboardBuilder({ config, onSave }) {
  const [name, setName] = useState(config.name || 'My Dashboard');
  const [layout, setLayout] = useState(config.layout || []);
  const [widgets, setWidgets] = useState(config.widgets || {});
  const [selectedWidget, setSelectedWidget] = useState(null);
  const [nextWidgetId, setNextWidgetId] = useState(
    layout.length > 0 ? Math.max(...layout.map(item => parseInt(item.i.replace('widget', '')))) + 1 : 1
  );
  
  // Available signals (would come from the backend in the real implementation)
  const [availableSignals] = useState([
    { id: 'EEC1.EngineSpeed', name: 'Engine Speed', unit: 'rpm', min: 0, max: 8000 },
    { id: 'CCVS1.WheelBasedVehicleSpeed', name: 'Vehicle Speed', unit: 'km/h', min: 0, max: 120 }
  ]);
  
  const addWidget = (type) => {
    const id = `widget${nextWidgetId}`;
    const newWidget = {
      type,
      title: `New ${type.charAt(0).toUpperCase() + type.slice(1)}`,
      signalId: availableSignals[0]?.id || ''
    };
    
    // Add default properties based on widget type
    if (type === 'gauge') {
      newWidget.min = 0;
      newWidget.max = 100;
    } else if (type === 'value') {
      newWidget.precision = 1;
    }
    
    const newLayout = [
      ...layout,
      {
        i: id,
        x: (layout.length * 3) % 12,
        y: Math.floor((layout.length * 3) / 12) * 4,
        w: 3,
        h: 4
      }
    ];
    
    setWidgets({ ...widgets, [id]: newWidget });
    setLayout(newLayout);
    setSelectedWidget(id);
    setNextWidgetId(nextWidgetId + 1);
  };
  
  const removeWidget = (id) => {
    const newWidgets = { ...widgets };
    delete newWidgets[id];
    setWidgets(newWidgets);
    setLayout(layout.filter(item => item.i !== id));
    
    if (selectedWidget === id) {
      setSelectedWidget(null);
    }
  };
  
  const updateWidget = (id, updates) => {
    setWidgets({
      ...widgets,
      [id]: {
        ...widgets[id],
        ...updates
      }
    });
  };
  
  const handleSave = () => {
    onSave({
      name,
      layout,
      widgets
    });
  };
  
  const handleLayoutChange = (newLayout) => {
    setLayout(newLayout);
  };
  
  return (
    <Container>
      <Sidebar>
        <Section>
          <SectionTitle>Dashboard Settings</SectionTitle>
          <Input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Dashboard Name"
          />
          <Button onClick={handleSave}>Save Dashboard</Button>
        </Section>
        
        <Section>
          <SectionTitle>Add Widgets</SectionTitle>
          <Button onClick={() => addWidget('value')}>Add Value Widget</Button>
          <Button onClick={() => addWidget('gauge')}>Add Gauge Widget</Button>
          <Button onClick={() => addWidget('chart')}>Add Chart Widget</Button>
        </Section>
        
        {selectedWidget && (
          <Section>
            <SectionTitle>Widget Properties</SectionTitle>
            <Input
              type="text"
              value={widgets[selectedWidget].title}
              onChange={(e) => updateWidget(selectedWidget, { title: e.target.value })}
              placeholder="Title"
            />
            
            <Select
              value={widgets[selectedWidget].signalId}
              onChange={(e) => updateWidget(selectedWidget, { signalId: e.target.value })}
            >
              <option value="">Select Signal</option>
              {availableSignals.map(signal => (
                <option key={signal.id} value={signal.id}>
                  {signal.name} ({signal.id})
                </option>
              ))}
            </Select>
            
            {widgets[selectedWidget].type === 'gauge' && (
              <>
                <Input
                  type="number"
                  value={widgets[selectedWidget].min}
                  onChange={(e) => updateWidget(selectedWidget, { min: parseFloat(e.target.value) })}
                  placeholder="Min Value"
                />
                <Input
                  type="number"
                  value={widgets[selectedWidget].max}
                  onChange={(e) => updateWidget(selectedWidget, { max: parseFloat(e.target.value) })}
                  placeholder="Max Value"
                />
              </>
            )}
            
            {widgets[selectedWidget].type === 'value' && (
              <Input
                type="number"
                value={widgets[selectedWidget].precision}
                onChange={(e) => updateWidget(selectedWidget, { precision: parseInt(e.target.value) })}
                placeholder="Decimal Precision"
                min="0"
                max="5"
              />
            )}
            
            <Button
              className="danger"
              onClick={() => removeWidget(selectedWidget)}
            >
              Remove Widget
            </Button>
          </Section>
        )}
      </Sidebar>
      
      <Canvas>
        <GridLayout
          className="layout"
          layout={layout}
          cols={12}
          rowHeight={50}
          width={window.innerWidth - 340}
          isDraggable={true}
          isResizable={true}
          onLayoutChange={handleLayoutChange}
          compactType="vertical"
        >
          {layout.map(item => {
            const widget = widgets[item.i];
            const isSelected = selectedWidget === item.i;
            
            switch (widget.type) {
              case 'value':
                return (
                  <div key={item.i} onClick={() => setSelectedWidget(item.i)}>
                    <ValueWidget
                      title={widget.title}
                      value={0}
                      unit={availableSignals.find(s => s.id === widget.signalId)?.unit || ''}
                      precision={widget.precision}
                      isSelected={isSelected}
                    />
                  </div>
                );
              case 'gauge':
                return (
                  <div key={item.i} onClick={() => setSelectedWidget(item.i)}>
                    <GaugeWidget
                      title={widget.title}
                      value={50}
                      min={widget.min}
                      max={widget.max}
                      unit={availableSignals.find(s => s.id === widget.signalId)?.unit || ''}
                      isSelected={isSelected}
                    />
                  </div>
                );
              case 'chart':
                return (
                  <div key={item.i} onClick={() => setSelectedWidget(item.i)}>
                    <ChartWidget
                      title={widget.title}
                      signalId={widget.signalId}
                      unit={availableSignals.find(s => s.id === widget.signalId)?.unit || ''}
                      isSelected={isSelected}
                    />
                  </div>
                );
              default:
                return (
                  <div key={item.i} onClick={() => setSelectedWidget(item.i)}>
                    <WidgetCard title={widget.title || 'Unknown Widget'} isSelected={isSelected} />
                  </div>
                );
            }
          })}
        </GridLayout>
      </Canvas>
    </Container>
  );
}

export default DashboardBuilder;
