import sys
import argparse
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox,
                           QSplitter, QTreeWidget, QTreeWidgetItem, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt, QSettings

# Import both interface options
from can_interface import CANInterface
from direct_pcan_interface import DirectPCANInterface, DirectPCANMessageProcessor
from dbc_parser import DBCParser
from message_processor import MessageProcessor
from can_simulator import DualCANSimulator
from signal_display import SignalTableWidget, SignalPlotWidget
import time

# Import the new dashboard view
from dashboard_view import DashboardView
from configurable_dashboard_view import ConfigurableDashboardView



class CANVisApp(QMainWindow): 
    """Main application window for CAN data visualization"""
    def __init__(self):
        super().__init__()


        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger("CANVisApp")
        self.logger.info("Starting CAN visualization application")



        # Parse command line arguments
        self.args = self.parse_arguments()

        # Initialize UI components
        self.init_ui()

        # Initialize backend components
        self.init_components()
    
        # Initialize dashboard if in dashboard mode
        # MOVE THIS LINE FROM init_ui TO HERE
        if self.args.dashboard and hasattr(self, 'dashboard_view'):
            self.dashboard_view.init_web_channel(self.message_processor, self.dbc_parser)

        # Load settings if the method exists
        if hasattr(self, 'load_settings'):
            self.load_settings()

        # Show the window
        self.show()
    
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('canvis.log')
            ]
        )
    
    def parse_arguments(self):
        """Parse command line arguments"""
        parser = argparse.ArgumentParser(description='CAN Data Visualization')
        parser.add_argument('--dbc', help='Path to DBC file')
        parser.add_argument('--simulation', action='store_true', help='Run in simulation mode')
        parser.add_argument('--direct-pcan', action='store_true', 
                          help='Use direct PCAN interface (like decode_pcan.py)')
        # Add new dashboard mode argument
        parser.add_argument('--dashboard', action='store_true',
                          help='Enable modern dashboard interface')
        return parser.parse_args()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("CAN Data Visualization")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        # Create control bar
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)
        control_layout.setSpacing(5)
        # DBC file controls
        control_layout.addWidget(QLabel("DBC File:"))
        self.dbc_path_label = QLabel("No DBC file loaded")
        control_layout.addWidget(self.dbc_path_label)
        
        self.load_dbc_button = QPushButton("Load DBC")
        self.load_dbc_button.clicked.connect(self.load_dbc_file)
        control_layout.addWidget(self.load_dbc_button)
        
        # Use PCAN like decode_pcan.py checkbox
        self.direct_pcan_checkbox = QCheckBox("Use Direct PCAN Interface")
        self.direct_pcan_checkbox.setChecked(self.args.direct_pcan)
        control_layout.addWidget(self.direct_pcan_checkbox)
        
        # CAN interface controls (only shown when not using direct PCAN)
        self.interface_widget = QWidget()
        interface_layout = QHBoxLayout(self.interface_widget)
        interface_layout.setContentsMargins(0, 0, 0, 0)
        
        interface_layout.addWidget(QLabel("Sender:"))
        self.sender_combo = QComboBox()
        interface_layout.addWidget(self.sender_combo)
        
        interface_layout.addWidget(QLabel("Receiver:"))
        self.receiver_combo = QComboBox()
        interface_layout.addWidget(self.receiver_combo)
        
        control_layout.addWidget(self.interface_widget)
        
        # Start/Stop buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_can)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_can)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        self.send_test_button = QPushButton("Send Test Messages")
        self.send_test_button.clicked.connect(self.send_test_messages)
        control_layout.addWidget(self.send_test_button)
        
        main_layout.addLayout(control_layout)
        
        # Use dashboard view or traditional view based on args
        if self.args.dashboard:
            self._init_dashboard_ui(main_layout)
        else:
            self._init_traditional_ui(main_layout)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Update UI based on direct PCAN checkbox
        self.direct_pcan_checkbox.stateChanged.connect(self.on_interface_mode_changed)
        self.update_interface_controls()
    
    def _init_traditional_ui(self, main_layout):
        """Initialize the traditional splitview UI"""
        # Create main splitter
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Message tree
        self.message_tree = QTreeWidget()
        self.message_tree.setHeaderLabels(["Messages"])
        self.splitter.addWidget(self.message_tree)
        
        # Right panel: Signal display tabs
        self.tabs = QTabWidget()
        
        # Table tab
        self.table_widget = SignalTableWidget()
        self.tabs.addTab(self.table_widget, "Signal Table")
        
        # Plot tab
        self.plot_widget = SignalPlotWidget()
        self.tabs.addTab(self.plot_widget, "Signal Plot")
        
        self.splitter.addWidget(self.tabs)
        self.splitter.setSizes([300, 700])
        
        main_layout.addWidget(self.splitter)
    
    def _init_dashboard_ui(self, main_layout):
        """Initialize the modern dashboard UI"""
        # Create the configurable dashboard view
        self.dashboard_view = ConfigurableDashboardView()
        main_layout.addWidget(self.dashboard_view, 1)
        # In ConfigurableDashboardView.init_ui
    
    
    def update_interface_controls(self):
        """Show/hide interface controls based on direct PCAN checkbox"""
        if self.direct_pcan_checkbox.isChecked():
            self.interface_widget.setVisible(False)
        else:
            self.interface_widget.setVisible(True)
    
    
    def init_components(self):
        """Initialize backend components"""
        # Create CAN interface (allow virtual only in simulation mode)
        self.can_interface = CANInterface()
    
        # Variables for direct PCAN interface
        self.direct_pcan = None
        self.pcan_processor = None
    
        # Configure CAN interfaces based on mode
        if self.args.simulation:
            self.logger.info("Running in simulation mode")
            self.sender_combo.addItem("Simulated Sender")
            self.receiver_combo.addItem("Simulated Receiver")
            # Disable direct PCAN in simulation mode
            self.direct_pcan_checkbox.setChecked(False)
            self.direct_pcan_checkbox.setEnabled(False)
        else:
            # Add available CAN interfaces
            channels = ["PCAN_USBBUS1", "PCAN_USBBUS2"]
            for channel in channels:
                self.sender_combo.addItem(channel)
                self.receiver_combo.addItem(channel)
    
        # Create DBC parser
        self.dbc_parser = DBCParser()
    
        # Load DBC file if specified
        if self.args.dbc:
            self.load_dbc_file(self.args.dbc)
    
        # Create message processor for standard interface
        self.message_processor = MessageProcessor(self.can_interface, self.dbc_parser)
    
        # Connect signals for standard interface
        self.message_processor.message_decoded.connect(self.on_message_decoded)
        self.message_processor.unknown_message.connect(self.on_unknown_message)
    
        # Initialize dashboard view if in dashboard mode
        if self.args.dashboard and hasattr(self, 'dashboard_view'):
            self.dashboard_view.init_web_channel(self.message_processor, self.dbc_parser)
            
        # If direct PCAN is specified in args, set it up now
        if self.args.direct_pcan:
            self.direct_pcan_checkbox.setChecked(True)
            self.update_interface_controls()
    
        # Simulator (used in simulation mode)
        self.simulator = None
    
    def load_dbc_file(self, file_path=None):
        """Load a DBC file"""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open DBC File", "", "DBC Files (*.dbc);;All Files (*)"
            )
            
            if not file_path:
                return
        
        # Update UI
        self.status_bar.showMessage(f"Loading DBC file: {file_path}")
        self.dbc_path_label.setText(file_path)
        
        # Load the DBC file
        success = self.dbc_parser.load_dbc(file_path)
        
        if success:
            self.dbc_path = file_path
            self.status_bar.showMessage(f"DBC file loaded: {file_path}")
            
            # Update message tree for traditional view
            if not self.args.dashboard:
                self.update_message_tree()
        else:
            self.status_bar.showMessage("Failed to load DBC file")
            QMessageBox.critical(self, "Error", f"Failed to load DBC file: {file_path}")
    
    def update_message_tree(self):
        """Update the message tree with information from the loaded DBC"""
        # Only necessary for traditional view
        if self.args.dashboard:
            return
            
        # Clear existing items
        self.message_tree.clear()
        
        # Get all message IDs
        message_ids = self.dbc_parser.get_all_message_ids()
        if not message_ids:
            self.logger.warning("No messages found in DBC file")
            return
            
        for msg_id in message_ids:
            message = self.dbc_parser.get_message_by_id(msg_id)
            if not message:
                continue
            
            # Create message item
            msg_item = QTreeWidgetItem([f"{message.name} (0x{msg_id:X})"])
            self.message_tree.addTopLevelItem(msg_item)
            
            # Add signals as children
            for signal in message.signals:
                signal_item = QTreeWidgetItem([signal.name])
                msg_item.addChild(signal_item)
        
        # Expand all items
        self.message_tree.expandAll()
    
    def start_can(self):
        """Start CAN communication"""
        if not self.dbc_parser.db:
            QMessageBox.warning(self, "Warning", "Please load a DBC file first")
            return
        
        # Use command line arg if present, otherwise use checkbox
        use_direct_pcan = self.args.direct_pcan or self.direct_pcan_checkbox.isChecked()
    
        # Log the current state
        self.logger.info(f"Starting CAN with simulation={self.args.simulation}, direct_pcan={use_direct_pcan}")
        
        if self.args.simulation:
            self._start_simulation()
        elif use_direct_pcan:
            self.logger.info("Starting DirectPCAN interface")
            self._start_direct_pcan()
        else:
            self._start_standard_interface()
    
    def _start_simulation(self):
        """Start in simulation mode"""
        # Create simulator if not already created
        if not self.simulator:
            self.simulator = DualCANSimulator(self.dbc_parser)
            self.simulator.add_sender_callback(self.message_processor.process_message)
            self.simulator.add_receiver_callback(self.message_processor.process_message)
        
        # Start simulator
        self.simulator.start()
        self.status_bar.showMessage("Simulation started")
        
        # Update UI
        self._update_ui_running_state(True)
    
    def _start_direct_pcan(self):
        """Start with direct PCAN interface"""
        try:
            # Clean up existing interface if any
            if self.direct_pcan:
                self.direct_pcan.stop()
        
            self.logger.info("Initializing DirectPCAN interface")
        
            # Create direct PCAN interface
            self.direct_pcan = DirectPCANInterface()
            self.pcan_processor = DirectPCANMessageProcessor(self.direct_pcan, self.dbc_parser)
        
            # Add callback for message processing
            self.pcan_processor.add_callback(self.on_direct_pcan_message)
            self.logger.info("Added callback for DirectPCAN message processing")
        
            # Start the interface
            self.direct_pcan.start()
            self.status_bar.showMessage("DirectPCAN interface started - PCAN_USBBUS1 (sender), PCAN_USBBUS2 (receiver)")
        
            # Update UI
            self._update_ui_running_state(True)
        
        except Exception as e:
            self.logger.error(f"Failed to start DirectPCAN interface: {e}")
            QMessageBox.critical(self, "Hardware Error", 
                            f"Failed to connect to PCAN hardware: {str(e)}\n\n"
                            f"Please ensure your PCAN adapters are connected.")
            self.status_bar.showMessage("PCAN hardware connection failed")
    
    def _start_standard_interface(self):
        """Start with standard CAN interface"""
        sender = self.sender_combo.currentText()
        receiver = self.receiver_combo.currentText()
        
        try:
            # Add interfaces
            self.can_interface.add_interface("sender", interface_type='pcan',
                                          channel=sender, role="sender")
            self.can_interface.add_interface("receiver", interface_type='pcan',
                                          channel=receiver, role="receiver")
            
            # Start interfaces
            self.can_interface.start()
            self.status_bar.showMessage(f"CAN started - Sender: {sender}, Receiver: {receiver}")
            
            # Update UI
            self._update_ui_running_state(True)
            
        except Exception as e:
            self.logger.error(f"Failed to start CAN interface: {e}")
            QMessageBox.critical(self, "Hardware Error", 
                            f"Failed to connect to CAN hardware: {str(e)}\n\n"
                            f"Please ensure your PCAN adapters are connected.")
            self.status_bar.showMessage("Hardware connection failed")
    
    def _update_ui_running_state(self, running):
        """Update UI elements based on running state"""
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.load_dbc_button.setEnabled(not running)
        self.sender_combo.setEnabled(not running)
        self.receiver_combo.setEnabled(not running)
        self.direct_pcan_checkbox.setEnabled(not running and not self.args.simulation)
    
    def stop_can(self):
        """Stop CAN communication"""
        if self.args.simulation and self.simulator:
            self.simulator.stop()
            self.status_bar.showMessage("Simulation stopped")
        elif self.direct_pcan_checkbox.isChecked() and self.direct_pcan:
            self.direct_pcan.stop()
            self.status_bar.showMessage("DirectPCAN interface stopped")
        else:
            self.can_interface.stop()
            self.status_bar.showMessage("CAN stopped")
        
        # Update UI
        self._update_ui_running_state(False)
    
    def on_message_decoded(self, frame_id, message_name, signals, interface):
        """Handle decoded CAN message from standard interface"""
        self.logger.info(f"Decoded message received: ID=0x{frame_id:X}, Name={message_name}, Interface={interface}")
        self.logger.info(f"Signal values: {signals}")
        self._update_ui_with_message(frame_id, message_name, signals, interface)
    
    def on_direct_pcan_message(self, frame_id, message_name, signals, interface):
        """Handle message from DirectPCANInterface"""
        self.logger.info(f"DirectPCAN message received: ID=0x{frame_id:X}, Name={message_name}, Interface={interface}")
        self.logger.info(f"Signal values: {signals}")
        self._update_ui_with_message(frame_id, message_name, signals, interface)
    
    def _update_ui_with_message(self, frame_id, message_name, signals, interface):
        """Update UI with message data"""
        self.logger.info(f"Updating UI with message: {message_name}, signals: {signals}")
    
        # In dashboard mode, no need to update traditional UI
        if self.args.dashboard:
            return
    
        # Update signal table and plot for each signal
        for signal_name, value in signals.items():
            # Get unit if available
            message = self.dbc_parser.get_message_by_id(frame_id)
            if not message:
                self.logger.warning(f"No message definition found for ID 0x{frame_id:X}")
                continue
                
            unit = ""
            for signal in message.signals:
                if signal.name == signal_name:
                    unit = signal.unit or ""
                    break
        
            # Update table
            self.logger.info(f"Updating table for signal: {signal_name}={value} {unit}")
            self.table_widget.update_signal(
                frame_id, message_name, signal_name, value, unit, interface
            )
        
            # Update plot
            self.plot_widget.add_data_point(
                frame_id, message_name, signal_name, value, unit, interface
            )
    
    def on_unknown_message(self, frame_id, data_hex, interface):
        """Handle unknown CAN message"""
        self.status_bar.showMessage(
            f"Unknown message: ID=0x{frame_id:X}, Data={data_hex}, Interface={interface}"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop CAN if running
        if self.stop_button.isEnabled():
            self.stop_can()
        
        # Save settings
        self.save_settings()
        
        # Accept the close event
        event.accept()

    
    def send_test_messages(self):
        """Send test messages to verify connection"""
        if not self.dbc_parser.db:
            QMessageBox.warning(self, "Warning", "Please load a DBC file first")
            return
        
        if not self.start_button.isEnabled():  # Check if CAN is running
            # Get all message IDs from the DBC
            message_ids = self.dbc_parser.get_all_message_ids()
            if not message_ids:
                self.logger.warning("No messages found in DBC file")
                return
            
            self.logger.info(f"Sending test messages for IDs: {[f'0x{id:X}' for id in message_ids]}")
        
            # Send a test message for each message in the DBC
            for msg_id in message_ids:
                message = self.dbc_parser.get_message_by_id(msg_id)
                if not message:
                    continue
                
                self.logger.info(f"Creating test message for {message.name}, ID: 0x{msg_id:X}")
                
                # Create signal values (set to mid-range values)
                signal_values = {}
                for signal in message.signals:
                    min_val = signal.minimum if signal.minimum is not None else 0
                    max_val = signal.maximum if signal.maximum is not None else 100
                    # Use mid-range value
                    signal_values[signal.name] = (min_val + max_val) / 2
                    self.logger.info(f"  Signal: {signal.name}, Value: {signal_values[signal.name]}")
            
                # In send_test_messages method, modify the section that decides which interface to use:
                if self.direct_pcan_checkbox.isChecked() and self.direct_pcan:
                    # Using direct PCAN interface
                    self.logger.info(f"Sending via DirectPCAN interface: {message.name}")
                    success = self.pcan_processor.send_message(msg_id, signal_values)
                    self.logger.info(f"Sent test message {message.name} (0x{msg_id:X}) using DirectPCAN: {success}")
                else:
                    # Using standard interface
                    self.logger.info(f"Sending via standard interface: {message.name}")
                    sender_interface = "sender"  # This is always "sender" in standard interface mode
                    success = self.message_processor.create_and_send_message(
                        sender_interface, msg_id, signal_values)
                    self.logger.info(f"Sent test message {message.name} (0x{msg_id:X}) using standard interface: {success}")
            
                # Wait a bit between messages
                time.sleep(0.1)
        
            self.status_bar.showMessage("Test messages sent")
        else:
            QMessageBox.warning(self, "Warning", "Start CAN interface first")

    def save_settings(self):
        """Save application settings (placeholder)"""
        self.logger.info("Settings would be saved here")

    def on_interface_mode_changed(self):
        """Handle changes between direct PCAN and standard interface modes"""
        # Stop any running interfaces
        if self.stop_button.isEnabled():
            self.stop_can()
        
        # Update UI based on current mode
        self.update_interface_controls()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Apply dark theme if in dashboard mode
    args = sys.argv
    if '--dashboard' in args:
        from PyQt5.QtGui import QPalette, QColor
        
        # Apply dark palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Text, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
        app.setPalette(dark_palette)
        
        # Apply stylesheet for better appearance
        app.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a9ae2;
            }
            QPushButton:pressed {
                background-color: #3a80d2;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
        """)
    
    window = CANVisApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()