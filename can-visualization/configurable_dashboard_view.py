import os
import random
import json
import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QDialog, QTreeWidget, QTreeWidgetItem, QCheckBox, 
                            QComboBox, QSpinBox, QGroupBox, QFormLayout, QDialogButtonBox)
from PyQt5.QtCore import QUrl, QTimer, Qt
from PyQt5.QtGui import QFontDatabase, QFont

# Use the compatibility wrapper instead of direct imports
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineScript
    HAS_WEBENGINE = True
except ImportError:
    from PyQt5.QtWidgets import QLabel
    HAS_WEBENGINE = False
    
    # Create stub classes
    class QWebEngineView(QLabel):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setText("QWebEngineView not available.\nPlease install PyQtWebEngine")
    
    class QWebEngineSettings:
        pass
    
    class QWebEngineScript:
        pass

class SignalSelectorDialog(QDialog):
    """Dialog for selecting CAN signals to display in the dashboard"""
    
    def __init__(self, dbc_parser, parent=None):
        super().__init__(parent)
        self.dbc_parser = dbc_parser
        self.selected_signals = []
        
        self.setWindowTitle("Select Signals for Dashboard")
        self.setMinimumSize(500, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Signal tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Signal", "Message", "ID"])
        self.tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        layout.addWidget(self.tree)
        
        # Visualization type
        form_layout = QFormLayout()
        self.viz_type = QComboBox()
        self.viz_type.addItems(["Gauge", "Line Chart", "Numeric Display"])
        form_layout.addRow("Visualization Type:", self.viz_type)
        
        # Widget size
        self.widget_size = QComboBox()
        self.widget_size.addItems(["Small", "Medium", "Large"])
        self.widget_size.setCurrentIndex(1)  # Default to medium
        form_layout.addRow("Widget Size:", self.widget_size)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Populate tree
        self.populate_tree()
    
    def populate_tree(self):
        """Populate the tree with signals from the DBC file"""
        if not self.dbc_parser or not self.dbc_parser.db:
            return
            
        # Get all messages
        message_ids = self.dbc_parser.get_all_message_ids()
        for msg_id in message_ids:
            message = self.dbc_parser.get_message_by_id(msg_id)
            if not message:
                continue
                
            # Add signals from this message
            for signal in message.signals:
                item = QTreeWidgetItem([
                    signal.name,
                    message.name,
                    f"0x{msg_id:X}"
                ])
                # Store message ID and signal name as data
                item.setData(0, Qt.UserRole, {
                    'message_id': msg_id,
                    'message_name': message.name,
                    'signal_name': signal.name,
                    'unit': signal.unit or ""
                })
                self.tree.addTopLevelItem(item)
        
        # Sort by message name
        self.tree.sortItems(1, Qt.AscendingOrder)
    
    def get_selected_signals(self):
        """Get the selected signals and visualization settings"""
        selected_items = self.tree.selectedItems()
        signals = []
        
        for item in selected_items:
            signal_data = item.data(0, Qt.UserRole)
            if signal_data:
                signal_data['viz_type'] = self.viz_type.currentText()
                signal_data['widget_size'] = self.widget_size.currentText()
                signals.append(signal_data)
                
        return signals


class ConfigurableDashboardView(QWidget):
    """Configurable dashboard view for CAN visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("ConfigurableDashboardView")
        self.message_processor = None
        self.dbc_parser = None
        self.logger.info("Initializing configurable dashboard view")
        
        # Store messages and configured widgets
        self.recent_messages = {}
        self.configured_widgets = []
        
        # Initialize UI
        self.init_ui()
        
        # Start update timer
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(200)  # Update 5 times per second
    
    def init_ui(self):
        """Initialize the user interface"""
        # Create layout
        layout = QVBoxLayout(self)
        
        # Control bar
        control_layout = QHBoxLayout()
        # In ConfigurableDashboardView.init_ui
        layout.setContentsMargins(0, 0, 0, 0)
        # And for the control_layout
        control_layout.setContentsMargins(5, 5, 5, 5)
        self.add_widget_button = QPushButton("Add Widget")
        self.add_widget_button.clicked.connect(self.add_widget_dialog)
        control_layout.addWidget(self.add_widget_button)
        
        self.clear_dashboard_button = QPushButton("Clear Dashboard")
        self.clear_dashboard_button.clicked.connect(self.clear_dashboard)
        control_layout.addWidget(self.clear_dashboard_button)
        
        self.status_label = QLabel("Dashboard Ready")
        control_layout.addWidget(self.status_label)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # WebView for dashboard
        if not HAS_WEBENGINE:
            # If web engine is not available, show a message
            layout.addWidget(QLabel("PyQtWebEngine is not available. Please install it with: pip install PyQtWebEngine"))
            self.logger.warning("PyQtWebEngine not available - dashboard functionality limited")
            return
        else:
            self.web_view = QWebEngineView()
            layout.addWidget(self.web_view, 1)
        
        # Enable JavaScript
        self.web_view.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        
        # Load the HTML content directly
        html_content = self.get_dashboard_html()
        self.web_view.setHtml(html_content)
        
        # Connect to the page created signal to inject the JavaScript bridge
        self.web_view.loadFinished.connect(self.on_load_finished)
        
        layout.addWidget(self.web_view)
    
    def on_load_finished(self, ok):
        """Handle the web page finished loading"""
        if ok:
            self.logger.info("Dashboard page loaded successfully")
            
            # Inject JavaScript to handle direct data injection
            script = """
            // Store the received data globally
            var dashboardData = {};
            var dashboardConfig = { widgets: [] };
            
            // Function to be called from Python
            function updateData(data) {
                // Parse the JSON data
                var jsonData = JSON.parse(data);
                dashboardData = jsonData;
                
                // Process the data updates
                if (typeof updateWidgets === 'function') {
                    updateWidgets(dashboardData);
                }
            }
            
            // Function to update dashboard configuration
            function updateConfig(config) {
                // Parse the JSON config
                var jsonConfig = JSON.parse(config);
                dashboardConfig = jsonConfig;
                
                // Update the dashboard configuration
                if (typeof updateDashboardConfig === 'function') {
                    updateDashboardConfig(dashboardConfig.widgets);
                }
            }
            
            // Function to notify Python when a widget is removed
            function removeWidgetPython(widgetId) {
                // This will be replaced by QWebChannel
                console.log("Widget removed: " + widgetId);
                
                // Remove widget from our config
                dashboardConfig.widgets = dashboardConfig.widgets.filter(w => w.id !== widgetId);
            }
            """
            
            # Run the script
            self.web_view.page().runJavaScript(script)
        else:
            self.logger.error("Failed to load dashboard page")
    
    def get_dashboard_html(self):
        """Get the HTML content for the dashboard"""
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
        
        .empty-dashboard {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 400px;
            color: #666;
            border: 2px dashed #ccc;
            border-radius: 8px;
            text-align: center;
            padding: 20px;
        }
        
        .empty-dashboard h3 {
            margin-bottom: 10px;
        }
        
        .widget {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            padding: 15px;
            position: relative;
            overflow: hidden;
        }
        
        .widget-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 5px;
            display: flex;
            justify-content: space-between;
        }
        
        .widget-title .widget-close {
            cursor: pointer;
            color: #999;
            font-size: 16px;
        }
        
        .widget-title .widget-close:hover {
            color: #f44336;
        }
        
        .widget-value {
            font-size: 28px;
            font-weight: bold;
        }
        
        .widget-unit {
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
            height: 130px;
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
        
        .widget.small {
            grid-column: span 1;
        }
        
        .widget.medium {
            grid-column: span 2;
        }
        
        .widget.large {
            grid-column: span 3;
        }
        
        @media (max-width: 768px) {
            .widget.medium, .widget.large {
                grid-column: span 1;
            }
        }
    </style>
</head>
<body>
    <div id="app">
        <div class="header">
            <h2>CAN Visualization Dashboard</h2>
            <div id="status">Ready</div>
        </div>
        
        <div class="content">
            <div id="dashboard" class="dashboard">
                <div id="empty-dashboard" class="empty-dashboard">
                    <h3>No Widgets Added</h3>
                    <p>Add widgets using the "Add Widget" button above</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Track widgets and data
        const widgets = {};
        const dataHistory = {};
                
        // Update dashboard configuration (add/remove widgets)
        function updateDashboardConfig(widgetConfigs) {
            // Hide empty dashboard message if we have widgets
            if (widgetConfigs.length > 0) {
                document.getElementById('empty-dashboard').style.display = 'none';
            } else {
                document.getElementById('empty-dashboard').style.display = 'flex';
            }
            
            // First, remove any widgets that are no longer in the config
            const currentWidgetIds = Object.keys(widgets);
            const newWidgetIds = widgetConfigs.map(w => w.id);
            
            for (const widgetId of currentWidgetIds) {
                if (!newWidgetIds.includes(widgetId)) {
                    // Remove the widget
                    const element = document.getElementById(`widget-${widgetId}`);
                    if (element) {
                        element.remove();
                    }
                    delete widgets[widgetId];
                    delete dataHistory[widgetId];
                }
            }
            
            // Add or update widgets
            for (const widgetConfig of widgetConfigs) {
                if (!widgets[widgetConfig.id]) {
                    // Add new widget
                    addWidget(widgetConfig);
                }
            }
        }
        
        // Add a new widget to the dashboard
        function addWidget(config) {
            const dashboard = document.getElementById('dashboard');
            
            // Create widget element
            const widget = document.createElement('div');
            widget.id = `widget-${config.id}`;
            widget.className = `widget ${config.size.toLowerCase()}`;
            
            // Set up data history
            dataHistory[config.id] = {
                values: Array(60).fill(0),
                chart: null
            };
            
            // Create widget content based on type
            if (config.type === 'Gauge') {
                widget.innerHTML = `
                    <div class="widget-title">
                        <span>${config.signal} (${config.message})</span>
                        <span class="widget-close" onclick="removeWidget('${config.id}')">&times;</span>
                    </div>
                    <div class="gauge-container">
                        <div class="gauge">
                            <div class="gauge-background"></div>
                            <div class="gauge-progress" id="gauge-${config.id}" style="transform: rotate(-90deg);"></div>
                            <div class="gauge-center">
                                <div class="gauge-value" id="value-${config.id}">0</div>
                                <div class="gauge-label">${config.unit || ''}</div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (config.type === 'Line Chart') {
                widget.innerHTML = `
                    <div class="widget-title">
                        <span>${config.signal} (${config.message})</span>
                        <span class="widget-close" onclick="removeWidget('${config.id}')">&times;</span>
                    </div>
                    <div class="chart-container">
                        <canvas id="chart-${config.id}"></canvas>
                    </div>
                `;
            } else {
                // Numeric display
                widget.innerHTML = `
                    <div class="widget-title">
                        <span>${config.signal} (${config.message})</span>
                        <span class="widget-close" onclick="removeWidget('${config.id}')">&times;</span>
                    </div>
                    <div class="widget-value" id="value-${config.id}">0</div>
                    <div class="widget-unit">${config.unit || ''}</div>
                `;
            }
            
            dashboard.appendChild(widget);
            
            // Initialize chart if needed
            if (config.type === 'Line Chart') {
                const ctx = document.getElementById(`chart-${config.id}`).getContext('2d');
                dataHistory[config.id].chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: Array(20).fill(''),
                        datasets: [{
                            data: dataHistory[config.id].values.slice(-20),
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
                            x: {
                                display: false
                            },
                            y: {
                                display: true,
                                beginAtZero: false
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
            }
            
            // Store widget config
            widgets[config.id] = config;
        }
        
        // Remove a widget (called from widget close button)
        function removeWidget(widgetId) {
            // Send message to parent window
            if (typeof removeWidgetPython === 'function') {
                removeWidgetPython(widgetId);
            }
            
            // Remove widget from DOM
            const element = document.getElementById(`widget-${widgetId}`);
            if (element) {
                element.remove();
            }
            
            // Clean up data
            delete widgets[widgetId];
            delete dataHistory[widgetId];
            
            // Show empty dashboard if no widgets left
            if (Object.keys(widgets).length === 0) {
                document.getElementById('empty-dashboard').style.display = 'flex';
            }
        }
        
        // Update gauges and charts with new data
        function updateWidgets(data) {
            // Update each widget with matching data
            for (const widgetId in widgets) {
                const widget = widgets[widgetId];
                const messageName = widget.message;
                const signalName = widget.signal;
                
                // Find the value for this widget
                if (data[messageName] && data[messageName][signalName] !== undefined) {
                    const value = data[messageName][signalName];
                    
                    // Update data history
                    dataHistory[widgetId].values.push(value);
                    dataHistory[widgetId].values.shift();
                    
                    // Update widget based on type
                    if (widget.type === 'Gauge') {
                        updateGauge(widgetId, value);
                    } else if (widget.type === 'Line Chart') {
                        updateChart(widgetId, value);
                    } else {
                        // Numeric display
                        updateNumeric(widgetId, value);
                    }
                }
            }
        }
        
        // Update gauge widget
        function updateGauge(widgetId, value) {
            // Update value text
            const valueElement = document.getElementById(`value-${widgetId}`);
            if (valueElement) {
                valueElement.textContent = typeof value === 'number' ? 
                    value.toFixed(value < 10 ? 1 : 0) : value;
            }
            
            // Update gauge position
            const gaugeElement = document.getElementById(`gauge-${widgetId}`);
            if (gaugeElement) {
                // Estimate min/max from recent values
                const values = dataHistory[widgetId].values.filter(v => v !== 0);
                const min = values.length > 0 ? Math.min(...values) : 0;
                const max = values.length > 0 ? Math.max(...values) : 100;
                const buffer = (max - min) * 0.1; // Add 10% buffer
                
                const percentage = (value - min) / (max - min + buffer);
                const rotation = -90 + percentage * 180;
                gaugeElement.style.transform = `rotate(${rotation}deg)`;
                
                // Update color based on value
                let color;
                if (percentage < 0.33) {
                    color = '#4CAF50'; // Green
                } else if (percentage < 0.66) {
                    color = '#FFEB3B'; // Yellow
                } else {
                    color = '#FF5722'; // Red/Orange
                }
                gaugeElement.style.background = color;
            }
        }
        
        // Update chart widget
        function updateChart(widgetId, value) {
            const chart = dataHistory[widgetId].chart;
            if (chart) {
                chart.data.datasets[0].data = dataHistory[widgetId].values.slice(-20);
                chart.update();
            }
        }
        
        // Update numeric display widget
        function updateNumeric(widgetId, value) {
            const valueElement = document.getElementById(`value-${widgetId}`);
            if (valueElement) {
                valueElement.textContent = typeof value === 'number' ? 
                    value.toFixed(value < 10 ? 1 : 0) : value;
            }
        }
        
        // Initialize
        window.addEventListener('load', function() {
            document.getElementById('status').textContent = 'Ready - Add widgets to begin';
        });
    </script>
</body>
</html>"""
    
    def init_web_channel(self, message_processor, dbc_parser):
        """Initialize with the message processor and DBC parser"""
        self.message_processor = message_processor
        self.dbc_parser = dbc_parser
        
        if message_processor:
            message_processor.message_decoded.connect(self.on_message_decoded)
        
        self.status_label.setText("Dashboard Ready - Add Widgets to Begin")
    
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
            # Send data to JavaScript
            if hasattr(self, 'web_view'):
                # Convert messages to JSON
                data_json = json.dumps(self.recent_messages)
                
                # Inject data using JavaScript
                js_code = f"updateData('{data_json.replace("'", "\\'")}');"
                self.web_view.page().runJavaScript(js_code)
                
                # Clear recent messages
                self.recent_messages = {}
                
                # Update widget configuration if needed
                config_json = json.dumps({"widgets": self.configured_widgets})
                js_code = f"updateConfig('{config_json.replace("'", "\\'")}')\;"
                self.web_view.page().runJavaScript(js_code)
            
        except Exception as e:
            self.logger.error(f"Error updating dashboard: {e}")
    
    def add_widget_dialog(self):
        """Show dialog to add a widget to the dashboard"""
        if not self.dbc_parser or not self.dbc_parser.db:
            self.status_label.setText("Error: No DBC file loaded")
            return
            
        dialog = SignalSelectorDialog(self.dbc_parser, self)
        if dialog.exec_():
            selected_signals = dialog.get_selected_signals()
            if selected_signals:
                for signal in selected_signals:
                    self.add_widget(signal)
    
    def add_widget(self, signal_config):
        """Add a widget to the dashboard"""
        widget_id = f"widget_{len(self.configured_widgets)}_{random.randint(1000, 9999)}"
        
        # Create widget configuration
        widget_config = {
            "id": widget_id,
            "type": signal_config["viz_type"],
            "size": signal_config["widget_size"],
            "message": signal_config["message_name"],
            "signal": signal_config["signal_name"],
            "unit": signal_config["unit"]
        }
        
        # Add to configured widgets
        self.configured_widgets.append(widget_config)
        
        # Update status
        self.status_label.setText(f"Added widget for {signal_config['signal_name']}")
        
        # Force update to dashboard
        self.update_dashboard()
        
        self.logger.info(f"Added widget: {signal_config['signal_name']} (Type: {signal_config['viz_type']}, Size: {signal_config['widget_size']})")
    
    def clear_dashboard(self):
        """Clear all widgets from the dashboard"""
        self.configured_widgets = []
        self.update_dashboard()
        self.status_label.setText("Dashboard cleared")