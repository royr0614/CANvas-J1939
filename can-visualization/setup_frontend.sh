#!/bin/bash
# Setup script for CAN Visualization React Frontend

echo "Setting up React Frontend for CAN Visualization..."

# Create frontend directory
FRONTEND_DIR="frontend"
mkdir -p $FRONTEND_DIR
cd $FRONTEND_DIR

# Initialize React app with create-react-app
echo "Initializing React application..."
npx create-react-app .

# Install additional dependencies
echo "Installing additional dependencies..."
npm install --save socket.io-client axios recharts react-grid-layout styled-components

# Create directory structure
mkdir -p src/components src/services src/hooks src/utils

echo "React frontend setup complete!"