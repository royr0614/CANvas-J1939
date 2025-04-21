#!/usr/bin/env python3
"""
Test script for the configurable CAN visualization dashboard
This script allows testing the dashboard with the J1939 demo DBC file
"""

import sys
import os
import logging
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

# Import components
from configurable_dashboard_view import ConfigurableDashboardView
from dbc_parser import DBCParser
from can_simulator import DualCANSimulator
from message_processor import MessageProcessor
from can_interface import CANInterface

class TestConfigurableDashboardApp(QMainWindow):
    """Test application for the configurable dashboard view"""
    
    def __init__(self):
        super().__init__()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("TestDashboard")
        
        # Set window properties
        self.setWindowTitle("Configurable CAN Dashboard Test")
        self.setMinimumSize(1024, 768)
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        
        # Get path to DBC file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dbc_path = os.path.join(script_dir, "CSS-Electronics-SAE-J1939-DEMO.dbc")
        
        if not os.path.exists(dbc_path):
            self.logger.error(f"DBC file not found: {dbc_path}")
            raise FileNotFoundError(f"DBC file not found: {dbc_path}")
        
        # Load DBC file
        self.dbc_parser = DBCParser(dbc_path)
        self.logger.info(f"Loaded DBC file: {dbc_path}")
        
        # Create CAN interface
        self.can_interface = CANInterface()
        
        # Create message processor
        self.message_processor = MessageProcessor(self.can_interface, self.dbc_parser)
        
        # Create dashboard view
        self.dashboard_view = ConfigurableDashboardView()
        layout.addWidget(self.dashboard_view)
        
        # Initialize web channel
        self.dashboard_view.init_web_channel(self.message_processor, self.dbc_parser)
        
        # Create simulator
        self.simulator = DualCANSimulator(self.dbc_parser)
        self.simulator.add_sender_callback(self.message_processor.process_message)
        self.simulator.add_receiver_callback(self.message_processor.process_message)
        
        # Start simulator with a delay to allow dashboard initialization
        QTimer.singleShot(2000, self.start_simulator)
        
        # Show window
        self.show()
    
    def start_simulator(self):
        """Start the CAN simulator"""
        self.logger.info("Starting CAN simulator")
        self.simulator.start()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    try:
        window = TestConfigurableDashboardApp()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Error starting application: {e}")
        if isinstance(e, FileNotFoundError):
            print("\nERROR: DBC file not found. Make sure CSS-Electronics-SAE-J1939-DEMO.dbc is in the same directory as this script.")
        else:
            print(f"\nERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()