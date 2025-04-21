import React, { useRef } from 'react';
import styled from 'styled-components';
import { useSignals } from '../utils/SignalContext';

const ControlPanelContainer = styled.div`
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const StatusInfo = styled.div`
  flex: 1;
`;

const StatusItem = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 0.25rem;
`;

const StatusDot = styled.div`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: ${props => props.active ? '#4caf50' : '#d32f2f'};
  margin-right: 0.5rem;
`;

const FileInput = styled.input`
  display: none;
`;

const Button = styled.button`
  background-color: ${props => props.primary ? '#2196f3' : props.danger ? '#f44336' : '#e0e0e0'};
  color: ${props => (props.primary || props.danger) ? 'white' : 'black'};
  border: none;
  border-radius: 4px;
  padding: 0.5rem 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: ${props => props.primary ? '#1976d2' : props.danger ? '#d32f2f' : '#bdbdbd'};
  }
  
  &:disabled {
    background-color: #e0e0e0;
    color: #9e9e9e;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  color: #d32f2f;
  padding: 0.5rem;
  margin-top: 0.5rem;
  border-radius: 4px;
  background-color: #ffebee;
  display: ${props => props.error ? 'block' : 'none'};
`;

const ControlPanel = () => {
  const {
    status,
    loading,
    error,
    uploadDBC,
    startCAN,
    stopCAN,
    clearError
  } = useSignals();
  
  const fileInputRef = useRef(null);
  
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      await uploadDBC(file);
      // Reset file input
      event.target.value = '';
    }
  };
  
  const handleBrowseClick = () => {
    fileInputRef.current.click();
  };
  
  const handleStartClick = async () => {
    await startCAN();
  };
  
  const handleStopClick = async () => {
    await stopCAN();
  };
  
  return (
    <div>
      <ControlPanelContainer>
        <StatusInfo>
          <StatusItem>
            <StatusDot active={status.dbcLoaded} />
            <span>DBC File: {status.dbcLoaded ? 'Loaded' : 'Not Loaded'}</span>
          </StatusItem>
          <StatusItem>
            <StatusDot active={status.running} />
            <span>CAN: {status.running ? 'Running' : 'Stopped'}</span>
          </StatusItem>
        </StatusInfo>
        
        <div>
          <FileInput
            type="file"
            accept=".dbc"
            ref={fileInputRef}
            onChange={handleFileUpload}
          />
          <Button onClick={handleBrowseClick} disabled={loading}>
            Load DBC File
          </Button>
        </div>
        
        {status.dbcLoaded && (
          <>
            {status.running ? (
              <Button danger onClick={handleStopClick} disabled={loading}>
                Stop CAN
              </Button>
            ) : (
              <Button primary onClick={handleStartClick} disabled={loading}>
                Start CAN
              </Button>
            )}
          </>
        )}
      </ControlPanelContainer>
      
      <ErrorMessage error={error} onClick={clearError}>
        {error}
      </ErrorMessage>
    </div>
  );
};

export default ControlPanel;