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
        
        # Initialize components
        self.init_ui()
        self.init_components()
        
        # Load settings
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
        
        # Create control bar
        control_layout = QHBoxLayout()
        
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
        
        main_layout.addLayout(control_layout)
        
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
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Update UI based on direct PCAN checkbox
        self.direct_pcan_checkbox.stateChanged.connect(self.update_interface_controls)
        self.update_interface_controls()
    
    def update_interface_controls(self):
        """Show/hide interface controls based on direct PCAN checkbox"""
        if self.direct_pcan_checkbox.isChecked():
            self.interface_widget.setVisible(False)
        else:
            self.interface_widget.setVisible(True)
    
    def init_components(self):
        """Initialize backend components"""
        # Create CAN interface (allow virtual only in simulation mode)
        self.can_interface = CANInterface(allow_virtual=self.args.simulation)
        
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
        
        # Connect signals
        self.message_processor.message_decoded.connect(self.on_message_decoded)
        self.message_processor.unknown_message.connect(self.on_unknown_message)
        
        # Simulator (used in simulation mode)
        self.simulator = None
    
    def load_settings(self):
        """Load application settings"""
        settings = QSettings("CANVisApp", "CANVis")
        
        # Load window geometry
        geometry = settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # Load splitter state
        splitter_state = settings.value("splitter_state")
        if splitter_state:
            self.splitter.restoreState(splitter_state)
        
        # Load last DBC file
        last_dbc = settings.value("last_dbc")
        if last_dbc and not self.args.dbc:
            self.load_dbc_file(last_dbc)
        
        # Load direct PCAN setting
        use_direct_pcan = settings.value("use_direct_pcan", type=bool)
        if use_direct_pcan is not None and not self.args.simulation:
            self.direct_pcan_checkbox.setChecked(use_direct_pcan)
            self.update_interface_controls()
    
    def save_settings(self):
        """Save application settings"""
        settings = QSettings("CANVisApp", "CANVis")
        
        # Save window geometry
        settings.setValue("window_geometry", self.saveGeometry())
        
        # Save splitter state
        settings.setValue("splitter_state", self.splitter.saveState())
        
        # Save DBC file path
        if hasattr(self, 'dbc_path') and self.dbc_path:
            settings.setValue("last_dbc", self.dbc_path)
        
        # Save direct PCAN setting
        settings.setValue("use_direct_pcan", self.direct_pcan_checkbox.isChecked())
    
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
            self.update_message_tree()
        else:
            self.status_bar.showMessage("Failed to load DBC file")
            QMessageBox.critical(self, "Error", f"Failed to load DBC file: {file_path}")
    
    def update_message_tree(self):
        """Update the message tree with information from the loaded DBC"""
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
            
        if self.args.simulation:
            self._start_simulation()
        elif self.direct_pcan_checkbox.isChecked():
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
            
            # Create direct PCAN interface
            self.direct_pcan = DirectPCANInterface()
            self.pcan_processor = DirectPCANMessageProcessor(self.direct_pcan, self.dbc_parser)
            
            # Add callback for message processing
            self.pcan_processor.add_callback(self.on_direct_pcan_message)
            
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
        self._update_ui_with_message(frame_id, message_name, signals, interface)
    
    def on_direct_pcan_message(self, frame_id, message_name, signals, interface):
        """Handle message from DirectPCANInterface"""
        self._update_ui_with_message(frame_id, message_name, signals, interface)
    
    def _update_ui_with_message(self, frame_id, message_name, signals, interface):
        """Update UI with message data"""
        # Update signal table and plot for each signal
        for signal_name, value in signals.items():
            # Get unit if available
            message = self.dbc_parser.get_message_by_id(frame_id)
            if not message:
                continue
                
            unit = ""
            for signal in message.signals:
                if signal.name == signal_name:
                    unit = signal.unit or ""
                    break
            
            # Update table
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

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = CANVisApp()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()