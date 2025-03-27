from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, pyqtSlot, QObject, pyqtSignal, Qt
import os
import json
import logging
import tempfile

class SignalBridge(QObject):
    """Bridge between Python and JavaScript for signal data"""
    # Signal to emit when new data is available 
    signalUpdated = pyqtSignal(str)
    dashboardConfigSaved = pyqtSignal(str)
    
    @pyqtSlot(str)
    def saveConfig(self, config_json):
        """Save dashboard configuration from JavaScript"""
        self.dashboardConfigSaved.emit(config_json)
    
    def updateSignal(self, signal_data):
        """Send signal data to JavaScript"""
        self.signalUpdated.emit(json.dumps(signal_data))

class DashboardView(QWidget):
    """Widget for displaying and configuring a CAN signal dashboard"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("DashboardView")
    
        # Set up the layout
        layout = QVBoxLayout(self)
    
        # Create bridge object for Python <-> JavaScript communication
        self.bridge = SignalBridge()
    
        # Initialize web channel
        from PyQt5.QtWebChannel import QWebChannel
        self.web_channel = QWebChannel()
        self.web_channel.registerObject("bridge", self.bridge)
    
        # Create web view for React dashboard
        self.web_view = QWebEngineView()
    
        # Create dashboard directory if it doesn't exist
        os.makedirs(os.path.join(os.path.dirname(__file__), "dashboard"), exist_ok=True)
    
        # Load dashboard HTML file
        self.load_dashboard()
    
        # Add web view to layout
        layout.addWidget(self.web_view)
    
        # Store signal data
        self.signals = {}
        self.dbc_signals = {}
    
        # Store message processor and DBC parser references
        self.message_processor = None
        self.dbc_parser = None
    
        # Store currently loaded dashboard config
        self.current_config = {}
    
        # Connect bridge signals
        if hasattr(self.bridge, 'dashboardConfigSaved'):
            self.bridge.dashboardConfigSaved.connect(self.save_dashboard_config)
    
    def load_dashboard(self):
        """Load the dashboard HTML file"""
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "index.html")
        
        if not os.path.exists(dashboard_path):
            # If dashboard file doesn't exist, create a temporary one with a message
            fd, temp_path = tempfile.mkstemp(suffix='.html')
            with os.fdopen(fd, 'w') as f:
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>CAN Dashboard</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        .message { background-color: #f8d7da; border: 1px solid #f5c6cb; 
                                  color: #721c24; padding: 20px; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <div class="message">
                        <h3>Dashboard files not found</h3>
                        <p>Please run the dashboard setup script to install the necessary files.</p>
                        <p>See the README.md file for instructions.</p>
                    </div>
                </body>
                </html>
                """)
            dashboard_path = temp_path
            
        # Load the dashboard file
        self.logger.info(f"Loading dashboard from {dashboard_path}")
        self.web_view.load(QUrl.fromLocalFile(dashboard_path))
        
        # Add the bridge object to the page
        self.web_view.page().setWebChannel(self.web_channel)
        
    def init_web_channel(self, message_processor, dbc_parser):
        """Initialize web channel for JavaScript communication"""
        # Store references to backend components
        self.message_processor = message_processor
        self.dbc_parser = dbc_parser
    
        # Connect message signals
        if self.message_processor:
            self.message_processor.message_decoded.connect(self.on_message_decoded)
        
    def on_message_decoded(self, frame_id, message_name, signals, interface):
        """Handle decoded CAN message"""
        # Update local signal cache
        for signal_name, value in signals.items():
            # Create a unique ID for this signal
            signal_id = f"{message_name}.{signal_name}"
            
            # Store value
            if signal_id not in self.signals:
                self.signals[signal_id] = {
                    'values': [],
                    'timestamps': [],
                    'current': value,
                    'message_id': frame_id,
                    'message_name': message_name,
                    'signal_name': signal_name,
                    'interface': interface
                }
                
                # Add to DBC signals list if this is a new signal
                message = self.dbc_parser.get_message_by_id(frame_id)
                if message:
                    for signal in message.signals:
                        if signal.name == signal_name:
                            self.dbc_signals[signal_id] = {
                                'name': signal_name,
                                'message': message_name,
                                'min': signal.minimum if signal.minimum is not None else 0,
                                'max': signal.maximum if signal.maximum is not None else 100,
                                'unit': signal.unit if signal.unit else '',
                                'description': signal.comment if signal.comment else ''
                            }
                            break
                
            # Update current value
            self.signals[signal_id]['current'] = value
            
            # Add to history (limit to 1000 points)
            current_time = time.time()
            self.signals[signal_id]['values'].append(value)
            self.signals[signal_id]['timestamps'].append(current_time)
            
            if len(self.signals[signal_id]['values']) > 1000:
                self.signals[signal_id]['values'] = self.signals[signal_id]['values'][-1000:]
                self.signals[signal_id]['timestamps'] = self.signals[signal_id]['timestamps'][-1000:]
            
            # Send update to JavaScript
            self.bridge.updateSignal({
                'id': signal_id,
                'value': value,
                'timestamp': current_time,
                'message': message_name,
                'signal': signal_name,
                'interface': interface
            })
    
    @pyqtSlot()
    def get_available_signals(self):
        """Get available signals from DBC file"""
        # This will be called from JavaScript
        return json.dumps(self.dbc_signals)
    
    @pyqtSlot(str)
    def save_dashboard_config(self, config_json):
        """Save dashboard configuration"""
        try:
            config = json.loads(config_json)
            self.logger.info(f"Saving dashboard config: {config}")
            
            # Save to a file
            config_dir = os.path.join(os.path.dirname(__file__), "dashboard", "configs")
            os.makedirs(config_dir, exist_ok=True)
            
            config_path = os.path.join(config_dir, f"{config['name']}.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            self.logger.info(f"Dashboard config saved to {config_path}")
            self.current_config = config
        except Exception as e:
            self.logger.error(f"Error saving dashboard config: {e}")
    
    @pyqtSlot(str)
    def load_dashboard(self):
        """Load the dashboard HTML file"""
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "dist", "index.html")
    
        if not os.path.exists(dashboard_path):
            # If dashboard file doesn't exist, create a temporary one with a message
            fd, temp_path = tempfile.mkstemp(suffix='.html')
            with os.fdopen(fd, 'w') as f:
                f.write("""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>CAN Dashboard</title>
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; }
                        .message { background-color: #f8d7da; border: 1px solid #f5c6cb; 
                                  color: #721c24; padding: 20px; border-radius: 5px; }
                    </style>
                </head>
                <body>
                    <div class="message">
                        <h3>Dashboard files not found</h3>
                        <p>Please run the dashboard setup script to install the necessary files.</p>
                        <p>See the README.md file for instructions.</p>
                    </div>
                </body>
                </html>
                """)
            dashboard_path = temp_path
        
        # Load the dashboard file
        self.logger.info(f"Loading dashboard from {dashboard_path}")
        self.web_view.load(QUrl.fromLocalFile(dashboard_path))
    
        # Add the bridge object to the page
        self.web_view.page().setWebChannel(self.web_channel)