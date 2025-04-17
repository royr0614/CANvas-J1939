import React, { useState, useContext } from 'react';
import styled from 'styled-components';
import GridLayout from 'react-grid-layout';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import SignalContext from '../utils/SignalContext';
import { WidgetCard, ValueWidget, GaugeWidget, ChartWidget } from './Widgets';

const Container = styled.div`
  height: 100%;
  padding: 1rem;
  box-sizing: border-box;
`;

const EmptyMessage = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  text-align: center;
`;

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
