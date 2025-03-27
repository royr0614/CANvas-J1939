#!/bin/bash
# Setup script for CAN Dashboard

echo "Setting up CAN Visualization Dashboard..."

# Check if npm is installed
if ! command -v npm &> /dev/null
then
    echo "npm not found. Please install Node.js and npm first."
    echo "Visit https://nodejs.org/en/download/ for installation instructions."
    exit 1
fi

# Create dashboard directory
DASHBOARD_DIR="dashboard"
mkdir -p $DASHBOARD_DIR
cd $DASHBOARD_DIR

# Initialize React app
echo "Initializing React application..."
npm init -y
npm install --save react react-dom react-grid-layout recharts styled-components

# Create directory structure
mkdir -p public src/components src/utils

# Create React app files
echo "Creating React dashboard files..."

# Create public/index.html
cat > public/index.html << EOL
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>CAN Dashboard</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
                Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
        }
    </style>
</head>
<body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
    <script type="module" src="../src/index.js"></script>
</body>
</html>
EOL

# Create webpack config
cat > webpack.config.js << EOL
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
    }),
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    port: 3000,
  },
  resolve: {
    extensions: ['.js', '.jsx'],
  },
};
EOL

# Create babel config
cat > babel.config.js << EOL
module.exports = {
  presets: [
    '@babel/preset-env',
    ['@babel/preset-react', { runtime: 'automatic' }],
  ],
};
EOL

# Update package.json scripts
npm pkg set scripts.start="webpack serve --mode development"
npm pkg set scripts.build="webpack --mode production"

# Install dev dependencies
npm install --save-dev webpack webpack-cli webpack-dev-server babel-loader @babel/core @babel/preset-env @babel/preset-react html-webpack-plugin style-loader css-loader

# Create React components
echo "Creating React components..."

# Create src/index.js
cat > src/index.js << EOL
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(<App />);
EOL

# Create src/App.js
cat > src/App.js << EOL
import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import DashboardBuilder from './components/DashboardBuilder';
import DashboardView from './components/DashboardView';
import { SignalProvider } from './utils/SignalContext';

const AppContainer = styled.div\`
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
\`;

const Header = styled.header\`
  background-color: #2a2a2a;
  color: white;
  padding: 0.5rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
\`;

const Title = styled.h1\`
  margin: 0;
  font-size: 1.2rem;
\`;

const TabsContainer = styled.div\`
  display: flex;
  gap: 1rem;
\`;

const Tab = styled.button\`
  background-color: \${props => props.active ? '#4a90e2' : 'transparent'};
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  cursor: pointer;
  font-weight: \${props => props.active ? 'bold' : 'normal'};
  border-radius: 4px;
  
  &:hover {
    background-color: \${props => props.active ? '#4a90e2' : '#3a3a3a'};
  }
\`;

const Content = styled.main\`
  flex: 1;
  overflow: auto;
  background-color: #f5f5f5;
\`;

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
EOL

# Create SignalContext.js
cat > src/utils/SignalContext.js << EOL
import React from 'react';

const SignalContext = React.createContext({});

export const SignalProvider = SignalContext.Provider;
export default SignalContext;
EOL

# Create DashboardView
cat > src/components/DashboardView.js << EOL
import React, { useState, useContext } from 'react';
import styled from 'styled-components';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import SignalContext from '../utils/SignalContext';
import { WidgetCard, ValueWidget, GaugeWidget, ChartWidget } from './Widgets';

const Container = styled.div\`
  height: 100%;
  padding: 1rem;
  box-sizing: border-box;
\`;

const EmptyMessage = styled.div\`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
\`;

function DashboardView({ config }) {
  const { signals } = useContext(SignalContext);
  
  if (!config.layout || config.layout.length === 0) {
    return (
      <EmptyMessage>
        <h2>No dashboard widgets configured</h2>
        <p>Switch to "Edit Dashboard" to create your dashboard</p>
      </EmptyMessage>
    );
  }
  
  return (
    <Container>
      <GridLayout
        className="layout"
        layout={config.layout}
        cols={12}
        rowHeight={50}
        width={window.innerWidth - 40}
        isDraggable={false}
        isResizable={false}
        compactType="vertical"
      >
        {config.layout.map(item => {
          const widget = config.widgets[item.i];
          const signalValue = signals[widget?.signalId]?.current || 0;
          
          switch (widget?.type) {
            case 'value':
              return (
                <div key={item.i}>
                  <ValueWidget
                    title={widget.title || widget.signalId}
                    value={signalValue}
                    unit={widget.unit || ''}
                    precision={widget.precision || 1}
                  />
                </div>
              );
            case 'gauge':
              return (
                <div key={item.i}>
                  <GaugeWidget
                    title={widget.title || widget.signalId}
                    value={signalValue}
                    min={widget.min || 0}
                    max={widget.max || 100}
                    unit={widget.unit || ''}
                  />
                </div>
              );
            case 'chart':
              return (
                <div key={item.i}>
                  <ChartWidget
                    title={widget.title || widget.signalId}
                    signalId={widget.signalId}
                    unit={widget.unit || ''}
                  />
                </div>
              );
            default:
              return (
                <div key={item.i}>
                  <WidgetCard title="Unknown Widget Type" />
                </div>
              );
          }
        })}
      </GridLayout>
    </Container>
  );
}

export default DashboardView;
EOL

# Create DashboardBuilder.js
cat > src/components/DashboardBuilder.js << EOL
import React, { useState } from 'react';
import styled from 'styled-components';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { WidgetCard, ValueWidget, GaugeWidget, ChartWidget } from './Widgets';

const Container = styled.div\`
  display: flex;
  height: 100%;
\`;

const Sidebar = styled.div\`
  width: 300px;
  background-color: #f0f0f0;
  border-right: 1px solid #ddd;
  padding: 1rem;
  display: flex;
  flex-direction: column;
\`;

const Canvas = styled.div\`
  flex: 1;
  padding: 1rem;
  overflow: auto;
\`;

const Section = styled.div\`
  margin-bottom: 1.5rem;
\`;

const SectionTitle = styled.h3\`
  margin-top: 0;
  font-size: 1rem;
  color: #333;
\`;

const Input = styled.input\`
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
\`;

const Select = styled.select\`
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 0.5rem;
\`;

const Button = styled.button\`
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
\`;

const WidgetItem = styled.div\`
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
\`;

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
    const id = \`widget\${nextWidgetId}\`;
    const newWidget = {
      type,
      title: \`New \${type.charAt(0).toUpperCase() + type.slice(1)}\`,
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
EOL

# Create Widgets.js
cat > src/components/Widgets.js << EOL
import React, { useContext, useEffect, useState } from 'react';
import styled, { css } from 'styled-components';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import SignalContext from '../utils/SignalContext';

// Shared styles for widget cards
export const WidgetCard = styled.div\`
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 1rem;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  
  \${props => props.isSelected && css\`
    outline: 2px solid #4a90e2;
    box-shadow: 0 0 0 4px rgba(74, 144, 226, 0.3);
  \`}
\`;

const WidgetTitle = styled.h3\`
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
\`;

const WidgetContent = styled.div\`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
\`;

// Value Widget
const ValueDisplay = styled.div\`
  font-size: 2.5rem;
  font-weight: bold;
  color: #2a2a2a;
  display: flex;
  align-items: baseline;
\`;

const ValueUnit = styled.span\`
  font-size: 1rem;
  color: #666;
  margin-left: 0.5rem;
\`;

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
const GaugeContainer = styled.div\`
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
\`;

const GaugeSvg = styled.svg\`
  transform: rotate(-90deg);
\`;

const GaugeValue = styled.div\`
  position: absolute;
  bottom: 0;
  font-size: 1.5rem;
  font-weight: bold;
  color: #2a2a2a;
  display: flex;
  align-items: baseline;
\`;

export function GaugeWidget({ title, value, min = 0, max = 100, unit = '', isSelected }) {
  // Normalize value between 0 and 1
  const normalizedValue = Math.min(Math.max((value - min) / (max - min), 0), 1);
  
  // Convert to percentage for the gauge
  const percentage = normalizedValue * 100;
  
  // Calculate colors based on value (green to yellow to red)
  const getColor = (percent) => {
    if (percent < 50) return \`hsl(\${120 - percent * 1.2}, 100%, 45%)\`;
    if (percent < 75) return \`hsl(\${60 - (percent - 50) * 2.4}, 100%, 45%)\`;
    return \`hsl(0, 100%, \${50 - (percent - 75) * 0.2}%)\`;
  };
  
  // SVG parameters
  const radius = 40;
  const strokeWidth = 10;
  const circumference = 2 * Math.PI * radius;
  const arcLength = circumference * 0.75; // 270 degrees arc
  const strokeDasharray = \`\${arcLength} \${circumference}\`;
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
const ChartContainer = styled.div\`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
\`;

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
              formatter={(value) => [value.toFixed(2) + (unit ? \` \${unit}\` : ''), title]}
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
EOL

# Build the React app
echo "Building React Dashboard..."
npm run build

echo "Dashboard setup complete!"
echo "To start the CAN visualization with dashboard, run:"
echo "python main_app.py --dbc <your_dbc_file.dbc> --dashboard"