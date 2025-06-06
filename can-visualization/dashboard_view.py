import os
import random
import json
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QUrl, QTimer

# Use the compatibility wrapper instead of direct imports
from webengine_wrapper import QWebEngineView, QWebEngineSettings, HAS_WEBENGINE

class DashboardView(QWidget):
    """Modern dashboard view using web technologies for visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("DashboardView")
        self.message_processor = None
        self.dbc_parser = None
        self.logger.info("Initializing dashboard view")
        
        # Store messages temporarily
        self.recent_messages = {}
        
        # Initialize UI
        self.init_ui()
        
        # Start update timer - instead of using QWebChannel, we'll use periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(200)  # Update 5 times per second
        
    def init_ui(self):
        """Initialize the user interface"""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if not HAS_WEBENGINE:
            # If web engine is not available, show a message
            layout.addWidget(QLabel("PyQtWebEngine is not available. Please install it with: pip install PyQtWebEngine"))
            self.logger.warning("PyQtWebEngine not available - dashboard functionality limited")
            return
        
        # Create web view
        self.web_view = QWebEngineView()
        
        # Create dashboard HTML file
        html_path = self.create_dashboard_html()
        if html_path:
            self.logger.info(f"Loading dashboard HTML from: {html_path}")
            self.web_view.load(QUrl.fromLocalFile(html_path))
        else:
            # Fallback message
            layout.addWidget(QLabel("Failed to create dashboard. Check logs for details."))
            self.logger.error("Failed to create dashboard HTML file")
            
        layout.addWidget(self.web_view)
    
    def create_dashboard_html(self):
        """Create the dashboard HTML file"""
        try:
            html_content = self.get_dashboard_html()
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            return file_path
        except Exception as e:
            self.logger.error(f"Error creating dashboard HTML: {e}")
            return None
    
    def get_dashboard_html(self):
        """Get the HTML content for the dashboard"""
        # We'll use a simpler approach without QWebChannel
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAN Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.7.0/chart.min.js"></script>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            height: 100%;
            background-color: #f0f2f5;
        }
        
        #app {
            height: 100%;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background-color: #1e3a8a;
            color: white;
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .content {
            flex: 1;
            padding: 20px;
            overflow: auto;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            padding: 15px;
            position: relative;
            overflow: hidden;
        }
        
        .card-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .card-value {
            font-size: 28px;
            font-weight: bold;
        }
        
        .card-unit {
            font-size: 14px;
            color: #999;
            margin-left: 5px;
        }
        
        .chart-container {
            height: 80px;
            margin-top: 10px;
            position: relative;
        }
        
        .gauge-container {
            height: 150px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .gauge {
            width: 120px;
            height: 120px;
            position: relative;
        }
        
        .gauge-background {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: #e0e0e0;
            position: absolute;
            clip-path: polygon(50% 0%, 100% 0%, 100% 100%, 50% 100%);
            transform: rotate(0deg);
        }
        
        .gauge-progress {
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: linear-gradient(to right, #4CAF50, #FFEB3B, #FF5722);
            position: absolute;
            clip-path: polygon(50% 0%, 100% 0%, 100% 100%, 50% 100%);
            transform-origin: center left;
        }
        
        .gauge-center {
            position: absolute;
            width: 80%;
            height: 80%;
            background: white;
            border-radius: 50%;
            top: 10%;
            left: 10%;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        
        .gauge-value {
            font-size: 24px;
            font-weight: bold;
        }
        
        .gauge-label {
            font-size: 12px;
            color: #666;
        }
        
        #content-charts {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .chart-card {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            padding: 15px;
            height: 300px;
        }
        
        .positive-change {
            color: #4CAF50;
        }
        
        .negative-change {
            color: #F44336;
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="header">
            <h2>CAN Visualization Dashboard</h2>
            <div id="status"></div>
        </div>
        
        <div class="content">
            <div class="dashboard">
                <!-- Speed Card -->
                <div class="card">
                    <div class="card-title">Speed</div>
                    <div class="card-value" id="speed-value">0</div>
                    <div class="card-unit">km/h</div>
                    <div class="chart-container">
                        <canvas id="speed-chart"></canvas>
                    </div>
                    <div class="card-change positive-change" id="speed-change">↑ 3.5%</div>
                </div>
                
                <!-- Engine Speed Card -->
                <div class="card">
                    <div class="card-title">Engine Speed</div>
                    <div class="card-value" id="engine-speed-value">0</div>
                    <div class="card-unit">rpm</div>
                    <div class="chart-container">
                        <canvas id="engine-speed-chart"></canvas>
                    </div>
                    <div class="card-change positive-change" id="engine-speed-change">↑ 8.7%</div>
                </div>
                
                <!-- Fuel Rate Card -->
                <div class="card">
                    <div class="card-title">Fuel Rate</div>
                    <div class="card-value" id="fuel-rate-value">27.0</div>
                    <div class="card-unit">l/h</div>
                    <div class="chart-container">
                        <canvas id="fuel-rate-chart"></canvas>
                    </div>
                    <div class="card-change negative-change" id="fuel-rate-change">↓ 8.7%</div>
                </div>
                
                <!-- Fuel Economy Card -->
                <div class="card">
                    <div class="card-title">Fuel Economy</div>
                    <div class="card-value" id="fuel-economy-value">2.5</div>
                    <div class="card-unit">km/l</div>
                    <div class="chart-container">
                        <canvas id="fuel-economy-chart"></canvas>
                    </div>
                    <div class="card-change positive-change" id="fuel-economy-change">↑ 9.8%</div>
                </div>
                
                <!-- Power Level Card -->
                <div class="card">
                    <div class="card-title">Power Level</div>
                    <div class="card-value" id="power-level-value">130</div>
                    <div class="card-unit">kW</div>
                    <div class="chart-container">
                        <canvas id="power-level-chart"></canvas>
                    </div>
                    <div class="card-change positive-change" id="power-level-change">↑ 10.5%</div>
                </div>
                
                <!-- Fuel Level Card -->
                <div class="card">
                    <div class="card-title">Fuel Level</div>
                    <div class="card-value" id="fuel-level-value">51</div>
                    <div class="card-unit">%</div>
                    <div class="chart-container">
                        <div style="width: 100%; height: 100%; background: #f5f5f5; position: relative; border-radius: 4px; overflow: hidden;">
                            <div id="fuel-level-bar" style="height: 100%; width: 51%; background: linear-gradient(to top, #FFC107, #FFEB3B); position: absolute; bottom: 0; transition: width 0.5s ease;"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Temperature Gauges -->
            <div class="card">
                <div class="card-title">Temperatures (degC)</div>
                <div style="display: flex; justify-content: space-around;">
                    <!-- Oil Temperature Gauge -->
                    <div class="gauge-container">
                        <div class="gauge">
                            <div class="gauge-background"></div>
                            <div class="gauge-progress" id="oil-temp-gauge" style="transform: rotate(0deg); background: #FFC107;"></div>
                            <div class="gauge-center">
                                <div class="gauge-value" id="oil-temp-value">101</div>
                                <div class="gauge-label">oil</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Fuel Temperature Gauge -->
                    <div class="gauge-container">
                        <div class="gauge">
                            <div class="gauge-background"></div>
                            <div class="gauge-progress" id="fuel-temp-gauge" style="transform: rotate(0deg); background: #2196F3;"></div>
                            <div class="gauge-center">
                                <div class="gauge-value" id="fuel-temp-value">36</div>
                                <div class="gauge-label">fuel</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Coolant Temperature Gauge -->
                    <div class="gauge-container">
                        <div class="gauge">
                            <div class="gauge-background"></div>
                            <div class="gauge-progress" id="coolant-temp-gauge" style="transform: rotate(0deg); background: #4CAF50;"></div>
                            <div class="gauge-center">
                                <div class="gauge-value" id="coolant-temp-value">90</div>
                                <div class="gauge-label">coolant</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="content-charts">
                <!-- Speed Chart -->
                <div class="chart-card">
                    <div class="card-title">Speed (km/h)</div>
                    <canvas id="speed-history-chart"></canvas>
                </div>
                
                <!-- Engine Speed Chart -->
                <div class="chart-card">
                    <div class="card-title">EngineSpeed (rpm)</div>
                    <canvas id="engine-speed-history-chart"></canvas>
                </div>
                
                <!-- CAN Message Chart -->
                <div class="chart-card">
                    <div class="card-title">Message: CAN1_AMB_500</div>
                    <canvas id="can-message-chart"></canvas>
                </div>
                
                <!-- Warning Lamps Chart -->
                <div class="chart-card">
                    <div class="card-title">Warning Lamps</div>
                    <canvas id="warning-lamps-chart"></canvas>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Data storage
        const dataHistory = {
            speed: {
                values: Array(60).fill(0),
                chart: null
            },
            engineSpeed: {
                values: Array(60).fill(0),
                chart: null
            },
            fuelRate: {
                values: Array(60).fill(0),
                chart: null
            },
            fuelEconomy: {
                values: Array(60).fill(0),
                chart: null
            },
            powerLevel: {
                values: Array(60).fill(0),
                chart: null
            },
            temperatures: {
                oil: 101,
                coolant: 90,
                fuel: 36
            },
            canMessage: {
                labels: Array(60).fill(''),
                cylinderTemp: Array(60).fill(0).map(() => Math.floor(35 + Math.random() * 15)),
                sensorPressure: Array(60).fill(0).map(() => Math.floor(90 + Math.random() * 10)),
                chart: null
            },
            warningLamps: {
                labels: Array(60).fill(''),
                compressor: Array(60).fill(0),
                engineWarning: Array(60).fill(0),
                brakeActive: Array(60).fill(0),
                chart: null
            },
            fuelLevel: 51
        };
        
        // Initialize starting values
        document.getElementById('speed-value').textContent = '50';
        document.getElementById('engine-speed-value').textContent = '1800';
        
        // Polling for updates - no need for web channel
        function pollForUpdates() {
            fetch('dashboard-data.json')
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        // If file not found, continue with simulation
                        simulateUpdates();
                        return null;
                    }
                })
                .then(data => {
                    if (data) {
                        processUpdates(data);
                    }
                })
                .catch(error => {
                    // On error, continue with simulation
                    console.log('Using simulation mode:', error);
                    simulateUpdates();
                });
        }
        
        function processUpdates(data) {
            // Process real data from CAN messages
            if (data.CCVS1 && data.CCVS1.WheelBasedVehicleSpeed !== undefined) {
                updateSpeed(data.CCVS1.WheelBasedVehicleSpeed);
            }
            
            if (data.EEC1 && data.EEC1.EngineSpeed !== undefined) {
                updateEngineSpeed(data.EEC1.EngineSpeed);
            }
            
            // For other values, continue with simulation
            simulateOtherValues();
        }
        
        function updateSpeed(value) {
            document.getElementById('speed-value').textContent = Math.round(value);
            
            // Update history
            dataHistory.speed.values.push(value);
            dataHistory.speed.values.shift();
            
            // Update charts
            if (dataHistory.speed.chart) {
                dataHistory.speed.chart.data.datasets[0].data = dataHistory.speed.values.slice(-20);
                dataHistory.speed.chart.update();
            }
            
            if (dataHistory.speedHistory) {
                dataHistory.speedHistory.data.datasets[0].data = dataHistory.speed.values;
                dataHistory.speedHistory.update();
            }
        }
        
        function updateEngineSpeed(value) {
            document.getElementById('engine-speed-value').textContent = Math.round(value);
            
            // Update history
            dataHistory.engineSpeed.values.push(value);
            dataHistory.engineSpeed.values.shift();
            
            // Update charts
            if (dataHistory.engineSpeed.chart) {
                dataHistory.engineSpeed.chart.data.datasets[0].data = dataHistory.engineSpeed.values.slice(-20);
                dataHistory.engineSpeed.chart.update();
            }
            
            if (dataHistory.engineSpeedHistory) {
                dataHistory.engineSpeedHistory.data.datasets[0].data = dataHistory.engineSpeed.values;
                dataHistory.engineSpeedHistory.update();
            }
        }
        
        // Initialize charts
        function initCharts() {
            // Mini charts
            const createMiniChart = (canvasId, data, color) => {
                const ctx = document.getElementById(canvasId).getContext('2d');
                return new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: Array(20).fill(''),
                        datasets: [{
                            data: data,
                            borderColor: color,
                            backgroundColor: 'rgba(0, 0, 0, 0)',
                            borderWidth: 2,
                            pointRadius: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            x: {
                                display: false
                            },
                            y: {
                                display: false,
                                beginAtZero: true
                            }
                        },
                        plugins: {
                            legend: {
                                display: false
                            },
                            tooltip: {
                                enabled: false
                            }
                        },
                        elements: {
                            line: {
                                tension: 0.4
                            }
                        },
                        animation: false
                    }
                });
            };
            
            // Create mini charts
            dataHistory.speed.chart = createMiniChart('speed-chart', dataHistory.speed.values.slice(-20), '#4a90e2');
            dataHistory.engineSpeed.chart = createMiniChart('engine-speed-chart', dataHistory.engineSpeed.values.slice(-20), '#ff7300');
            dataHistory.fuelRate.chart = createMiniChart('fuel-rate-chart', dataHistory.fuelRate.values.slice(-20), '#50b432');
            dataHistory.fuelEconomy.chart = createMiniChart('fuel-economy-chart', dataHistory.fuelEconomy.values.slice(-20), '#ed561b');
            dataHistory.powerLevel.chart = createMiniChart('power-level-chart', dataHistory.powerLevel.values.slice(-20), '#8884d8');
            
            // Initialize gauges
            updateGauge('oil-temp-gauge', 'oil-temp-value', dataHistory.temperatures.oil, 50, 150);
            updateGauge('coolant-temp-gauge', 'coolant-temp-value', dataHistory.temperatures.coolant, 50, 120);
            updateGauge('fuel-temp-gauge', 'fuel-temp-value', dataHistory.temperatures.fuel, 0, 80);
            
            // Create larger history charts
            const timeLabels = Array(60).fill('').map((_, i) => i.toString());
            
            // Speed history chart
            const speedHistoryCtx = document.getElementById('speed-history-chart').getContext('2d');
            dataHistory.speedHistory = new Chart(speedHistoryCtx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        label: 'Speed (km/h)',
                        data: dataHistory.speed.values,
                        borderColor: '#4a90e2',
                        backgroundColor: 'rgba(74, 144, 226, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    elements: {
                        line: {
                            tension: 0.4
                        }
                    },
                    animation: false
                }
            });
            
            // Engine speed history chart
            const engineSpeedHistoryCtx = document.getElementById('engine-speed-history-chart').getContext('2d');
            dataHistory.engineSpeedHistory = new Chart(engineSpeedHistoryCtx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [{
                        label: 'Engine Speed (rpm)',
                        data: dataHistory.engineSpeed.values,
                        borderColor: '#ff7300',
                        backgroundColor: 'rgba(255, 115, 0, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        pointRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    elements: {
                        line: {
                            tension: 0.4
                        }
                    },
                    animation: false
                }
            });
            
            // CAN message chart
            const canMessageCtx = document.getElementById('can-message-chart').getContext('2d');
            dataHistory.canMessageChart = new Chart(canMessageCtx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [
                        {
                            label: 'Cylinder Temp',
                            data: dataHistory.canMessage.cylinderTemp,
                            borderColor: '#8884d8',
                            borderWidth: 2,
                            pointRadius: 0
                        },
                        {
                            label: 'Sensor Pressure',
                            data: dataHistory.canMessage.sensorPressure,
                            borderColor: '#ffa500',
                            borderWidth: 2,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    },
                    elements: {
                        line: {
                            tension: 0.4
                        }
                    },
                    animation: false
                }
            });
            
            // Warning lamps chart
            const warningLampsCtx = document.getElementById('warning-lamps-chart').getContext('2d');
            dataHistory.warningLampsChart = new Chart(warningLampsCtx, {
                type: 'line',
                data: {
                    labels: timeLabels,
                    datasets: [
                        {
                            label: 'Compressor',
                            data: dataHistory.warningLamps.compressor,
                            borderColor: '#4CAF50',
                            borderWidth: 2,
                            pointRadius: 0,
                            stepped: true
                        },
                        {
                            label: 'Engine Warning',
                            data: dataHistory.warningLamps.engineWarning,
                            borderColor: '#FF9800',
                            borderWidth: 2,
                            pointRadius: 0,
                            stepped: true
                        },
                        {
                            label: 'Brake',
                            data: dataHistory.warningLamps.brakeActive,
                            borderColor: '#2196F3',
                            borderWidth: 2,
                            pointRadius: 0,
                            stepped: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1.1
                        }
                    },
                    elements: {
                        line: {
                            tension: 0
                        }
                    },
                    animation: false
                }
            });
            
            // Add some warning events
            for (let i = 10; i < 15; i++) dataHistory.warningLamps.compressor[i] = 1;
            for (let i = 30; i < 35; i++) dataHistory.warningLamps.engineWarning[i] = 1;
            dataHistory.warningLampsChart.update();
        }
        
        // Update temperature gauges
        function updateGauge(id, valueId, value, min, max) {
            // Update value display
            document.getElementById(valueId).textContent = Math.round(value);
            
            // Calculate rotation (from -90 to 90 degrees)
            const percentage = (value - min) / (max - min);
            const rotation = -90 + percentage * 180;
            document.getElementById(id).style.transform = `rotate(${rotation}deg)`;
            
            // Update color based on value
            let color;
            if (percentage < 0.33) {
                color = '#4CAF50'; // Green
            } else if (percentage < 0.66) {
                color = '#FFEB3B'; // Yellow
            } else {
                color = '#FF5722'; // Red/Orange
            }
            document.getElementById(id).style.background = color;
        }
        
        // Simulate other values besides speed and RPM
        function simulateOtherValues() {
            // Fuel level slowly decreases
            dataHistory.fuelLevel = Math.max(0, dataHistory.fuelLevel - 0.05);
            document.getElementById('fuel-level-value').textContent = Math.round(dataHistory.fuelLevel);
            document.getElementById('fuel-level-bar').style.width = `${dataHistory.fuelLevel}%`;
            
            // Temperatures change slowly
            dataHistory.temperatures.oil += (Math.random() - 0.5) * 2;
            dataHistory.temperatures.oil = Math.max(80, Math.min(120, dataHistory.temperatures.oil));
            updateGauge('oil-temp-gauge', 'oil-temp-value', dataHistory.temperatures.oil, 50, 150);
            
            dataHistory.temperatures.coolant += (Math.random() - 0.5) * 2;
            dataHistory.temperatures.coolant = Math.max(70, Math.min(110, dataHistory.temperatures.coolant));
            updateGauge('coolant-temp-gauge', 'coolant-temp-value', dataHistory.temperatures.coolant, 50, 120);
            
            dataHistory.temperatures.fuel += (Math.random() - 0.5) * 1;
            dataHistory.temperatures.fuel = Math.max(20, Math.min(50, dataHistory.temperatures.fuel));
            updateGauge('fuel-temp-gauge', 'fuel-temp-value', dataHistory.temperatures.fuel, 0, 80);
            
            // CAN message data
            const lastCylinderTemp = dataHistory.canMessage.cylinderTemp[dataHistory.canMessage.cylinderTemp.length - 1];
            const lastSensorPressure = dataHistory.canMessage.sensorPressure[dataHistory.canMessage.sensorPressure.length - 1];
            
            dataHistory.canMessage.cylinderTemp.push(Math.max(30, Math.min(60, lastCylinderTemp + (Math.random() - 0.5) * 2)));
            dataHistory.canMessage.cylinderTemp.shift();
            
            dataHistory.canMessage.sensorPressure.push(Math.max(85, Math.min(115, lastSensorPressure + (Math.random() - 0.5) * 3)));
            dataHistory.canMessage.sensorPressure.shift();
            
            dataHistory.canMessageChart.data.datasets[0].data = dataHistory.canMessage.cylinderTemp;
            dataHistory.canMessageChart.data.datasets[1].data = dataHistory.canMessage.sensorPressure;
            dataHistory.canMessageChart.update();
            
            // Warning lamps - shift data and add new values
            for (const type of ['compressor', 'engineWarning', 'brakeActive']) {
                dataHistory.warningLamps[type].shift();
                
                // Occasionally generate warnings
                if (Math.random() > 0.98) {
                    dataHistory.warningLamps[type].push(1);
                } else if (dataHistory.warningLamps[type][dataHistory.warningLamps[type].length - 1] === 1 && Math.random() > 0.7) {
                    // Reset warnings after they've been active
                    dataHistory.warningLamps[type].push(0);
                } else {
                    // Otherwise continue previous state
                    dataHistory.warningLamps[type].push(dataHistory.warningLamps[type][dataHistory.warningLamps[type].length - 1]);
                }
            }
            
            dataHistory.warningLampsChart.data.datasets[0].data = dataHistory.warningLamps.compressor;
            dataHistory.warningLampsChart.data.datasets[1].data = dataHistory.warningLamps.engineWarning;
            dataHistory.warningLampsChart.data.datasets[2].data = dataHistory.warningLamps.brakeActive;
            dataHistory.warningLampsChart.update();
        }
        
        // Simulate all updates for testing
        function simulateUpdates() {
            // Speed
            const currentSpeed = parseFloat(document.getElementById('speed-value').textContent);
            const newSpeed = Math.max(0, Math.min(120, currentSpeed + (Math.random() - 0.5) * 5));
            updateSpeed(newSpeed);
            
            // Engine speed
            const currentRPM = parseFloat(document.getElementById('engine-speed-value').textContent);
            const newRPM = Math.max(800, Math.min(3000, currentRPM + (Math.random() - 0.5) * 100));
            updateEngineSpeed(newRPM);
            
            // Simulate other values
            simulateOtherValues();
        }
        
        // Initialize everything
        window.onload = function() {
            // Set status
            document.getElementById('status').textContent = 'Initializing...';
            
            // Initialize charts
            initCharts();
            
            // Start polling for updates (or use simulation if polling fails)
            document.getElementById('status').textContent = 'Running';
            setInterval(pollForUpdates, 200); // Poll 5 times per second
            
            // Initial simulation to populate charts
            simulateUpdates();
        };
    </script>
</body>
</html>"""
    
    def init_web_channel(self, message_processor, dbc_parser):
        """Initialize with the message processor"""
        self.message_processor = message_processor
        self.dbc_parser = dbc_parser
        
        # Connect signals to update dashboard
        if message_processor:
            message_processor.message_decoded.connect(self.on_message_decoded)
    
    def on_message_decoded(self, frame_id, message_name, signals, interface):
        """Handle a decoded CAN message"""
        # Store the message for the next update cycle
        self.recent_messages[message_name] = signals
        self.logger.debug(f"Stored message for dashboard: {message_name}")
    
    def update_dashboard(self):
        """Update the dashboard with recent messages"""
        if not self.recent_messages:
            return
            
        try:
            # Write messages to a JSON file that the web view can read
            data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard-data.json")
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(self.recent_messages, f)
                
            # Clear recent messages
            self.recent_messages = {}
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")