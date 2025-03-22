from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, 
                             QLabel, QHeaderView, QHBoxLayout, QComboBox, QPushButton)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
import pyqtgraph as pg
import logging
import time

class SignalTableWidget(QWidget):
    """
    Widget to display current signal values in a table format
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("SignalTableWidget")
        
        # Store signal data
        self.signal_values = {}  # {signal_name: value}
        self.signal_timestamps = {}  # {signal_name: last_update_time}
        self.stale_threshold = 5.0  # seconds before a signal is considered stale
        
        # Set up the layout
        layout = QVBoxLayout(self)
        
        # Create filter controls
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by message:"))
        self.msg_filter = QComboBox()
        self.msg_filter.addItem("All Messages")
        self.msg_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.msg_filter)
        
        filter_layout.addWidget(QLabel("Filter by interface:"))
        self.iface_filter = QComboBox()
        self.iface_filter.addItem("All Interfaces")
        self.iface_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.iface_filter)
        
        layout.addLayout(filter_layout)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Message, Signal, Value, Unit, Interface
        self.table.setHorizontalHeaderLabels(["Message", "Signal", "Value", "Unit", "Interface"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Read-only
        layout.addWidget(self.table)
        
        # Setup a timer to check for stale signals
        self.stale_timer = QTimer()
        self.stale_timer.timeout.connect(self.check_stale_signals)
        self.stale_timer.start(1000)  # Check every second
        
        # Internal data
        self.messages = set()
        self.interfaces = set()
        self.rows = {}  # Map (msg_name, signal_name, interface) to row index
    
    def update_signal(self, msg_id, msg_name, signal_name, value, unit, interface):
        """Update a signal value in the table"""
        current_time = time.time()
        
        # Update internal data
        self.messages.add(msg_name)
        self.interfaces.add(interface)
        
        # Update filter dropdowns if needed
        if msg_name not in [self.msg_filter.itemText(i) for i in range(self.msg_filter.count())]:
            self.msg_filter.addItem(msg_name)
        
        if interface not in [self.iface_filter.itemText(i) for i in range(self.iface_filter.count())]:
            self.iface_filter.addItem(interface)
        
        key = (msg_name, signal_name, interface)
        
        # Format value (handle different types)
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        
        # Store value and timestamp
        self.signal_values[key] = formatted_value
        self.signal_timestamps[key] = current_time
        
        # Check if we need to add a new row
        if key not in self.rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.rows[key] = row
            
            self.table.setItem(row, 0, QTableWidgetItem(msg_name))
            self.table.setItem(row, 1, QTableWidgetItem(signal_name))
            self.table.setItem(row, 2, QTableWidgetItem(formatted_value))
            self.table.setItem(row, 3, QTableWidgetItem(unit if unit else ""))
            self.table.setItem(row, 4, QTableWidgetItem(interface))
        else:
            # Update existing row
            row = self.rows[key]
            self.table.item(row, 2).setText(formatted_value)
        
        # Color code based on recency
        self.color_code_row(row, 0)  # Fresh update
        
        # Apply filters (in case they've been set)
        self.apply_filters()
    
    def check_stale_signals(self):
        """Check for and highlight stale signals"""
        current_time = time.time()
        
        for key, timestamp in self.signal_timestamps.items():
            if key in self.rows:
                age = current_time - timestamp
                row = self.rows[key]
                
                if age < self.stale_threshold:
                    # Normal - use color coding by age
                    self.color_code_row(row, age)
                else:
                    # Stale - highlight in gray
                    for col in range(self.table.columnCount()):
                        self.table.item(row, col).setBackground(QColor(200, 200, 200))
    
    def color_code_row(self, row, age):
        """Color code a row based on update age"""
        if age < 0.5:
            # Very recent - light green
            color = QColor(200, 255, 200)
        elif age < 1.0:
            # Recent - very light green
            color = QColor(225, 255, 225)
        elif age < self.stale_threshold:
            # Normal - white
            color = QColor(255, 255, 255)
        else:
            # Stale - light gray
            color = QColor(200, 200, 200)
        
        for col in range(self.table.columnCount()):
            self.table.item(row, col).setBackground(color)
    
    def apply_filters(self):
        """Apply message and interface filters to the table"""
        selected_msg = self.msg_filter.currentText()
        selected_iface = self.iface_filter.currentText()
        
        for key, row in self.rows.items():
            msg_name, _, interface = key
            
            # Determine if this row should be visible
            show_by_msg = (selected_msg == "All Messages" or selected_msg == msg_name)
            show_by_iface = (selected_iface == "All Interfaces" or selected_iface == interface)
            
            # Show or hide the row
            self.table.setRowHidden(row, not (show_by_msg and show_by_iface))

class SignalPlotWidget(QWidget):
    """
    Widget to plot signal values over time
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("SignalPlotWidget")
        
        # Set up the layout
        layout = QVBoxLayout(self)
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Signal:"))
        self.signal_selector = QComboBox()
        self.signal_selector.currentIndexChanged.connect(self.update_plot)
        controls_layout.addWidget(self.signal_selector)
        
        controls_layout.addWidget(QLabel("Time window:"))
        self.time_window = QComboBox()
        self.time_window.addItems(["10 seconds", "30 seconds", "1 minute", "5 minutes", "15 minutes"])
        self.time_window.currentIndexChanged.connect(self.update_plot_range)
        controls_layout.addWidget(self.time_window)
        
        self.clear_button = QPushButton("Clear Plot")
        self.clear_button.clicked.connect(self.clear_data)
        controls_layout.addWidget(self.clear_button)
        
        layout.addLayout(controls_layout)
        
        # Set up the plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')  # White background
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('bottom', 'Time (seconds)')
        self.plot_widget.setLabel('left', 'Value')
        layout.addWidget(self.plot_widget)
        
        # Data storage
        self.data = {}  # {signal_key: {'timestamps': [], 'values': []}}
        self.plot_items = {}  # {signal_key: PlotDataItem}
        self.signal_keys = []  # List of all signal keys
        self.current_signal = None
        
        # Time window values in seconds
        self.time_windows = {
            0: 10,    # 10 seconds
            1: 30,    # 30 seconds
            2: 60,    # 1 minute
            3: 300,   # 5 minutes
            4: 900    # 15 minutes
        }
    
    def add_data_point(self, msg_id, msg_name, signal_name, value, unit, interface):
        """Add a data point to the signal plot"""
        current_time = time.time()
        
        # Create a unique key for this signal
        signal_key = f"{msg_name}.{signal_name} ({interface})"
        
        # Add to the signal selector if this is a new signal
        if signal_key not in self.signal_keys:
            self.signal_keys.append(signal_key)
            self.signal_selector.addItem(signal_key)
            
            # Initialize data storage
            self.data[signal_key] = {
                'timestamps': [],
                'values': [],
                'unit': unit
            }
            
            # Create a plot item
            pen = pg.mkPen(color=(0, 0, 255), width=2)
            self.plot_items[signal_key] = self.plot_widget.plot(
                [], [], pen=pen, name=signal_key
            )
        
        # Add the data point
        self.data[signal_key]['timestamps'].append(current_time)
        self.data[signal_key]['values'].append(float(value) if isinstance(value, (int, float)) else 0)
        
        # Limit data points (to avoid memory issues)
        max_points = 1000
        if len(self.data[signal_key]['timestamps']) > max_points:
            self.data[signal_key]['timestamps'] = self.data[signal_key]['timestamps'][-max_points:]
            self.data[signal_key]['values'] = self.data[signal_key]['values'][-max_points:]
        
        # Update the plot if this is the currently selected signal
        if self.signal_selector.currentText() == signal_key:
            self.update_plot()
    
    def update_plot(self):
        """Update the plot with the currently selected signal"""
        signal_key = self.signal_selector.currentText()
        if not signal_key or signal_key not in self.data:
            return
        
        self.current_signal = signal_key
        
        # Get the data
        timestamps = self.data[signal_key]['timestamps']
        values = self.data[signal_key]['values']
        unit = self.data[signal_key]['unit']
        
        if not timestamps:
            return
        
        # Convert absolute timestamps to relative times (seconds from start)
        start_time = timestamps[0]
        relative_times = [t - start_time for t in timestamps]
        
        # Update the plot
        self.plot_items[signal_key].setData(relative_times, values)
        
        # Update labels
        self.plot_widget.setTitle(signal_key)
        self.plot_widget.setLabel('left', f'Value ({unit})' if unit else 'Value')
        
        # Update axis range
        self.update_plot_range()
    
    def update_plot_range(self):
        """Update the plot's time axis range based on selected time window"""
        if not self.current_signal or not self.data.get(self.current_signal, {}).get('timestamps'):
            return
        
        # Get the time window in seconds
        window_idx = self.time_window.currentIndex()
        window_seconds = self.time_windows.get(window_idx, 60)
        
        # Calculate the x-axis range
        timestamps = self.data[self.current_signal]['timestamps']
        start_time = timestamps[0]
        relative_times = [t - start_time for t in timestamps]
        
        if relative_times:
            # Set x-axis to show the selected time window
            max_time = relative_times[-1]
            min_time = max(0, max_time - window_seconds)
            self.plot_widget.setXRange(min_time, max_time)
            
            # Set y-axis to show all values in the visible range
            visible_values = [v for t, v in zip(relative_times, self.data[self.current_signal]['values'])
                            if min_time <= t <= max_time]
            
            if visible_values:
                min_val = min(visible_values)
                max_val = max(visible_values)
                padding = (max_val - min_val) * 0.1 if max_val != min_val else 1.0
                self.plot_widget.setYRange(min_val - padding, max_val + padding)
    
    def clear_data(self):
        """Clear all plot data"""
        if self.current_signal:
            self.data[self.current_signal]['timestamps'] = []
            self.data[self.current_signal]['values'] = []
            self.plot_items[self.current_signal].clear()
            self.logger.info(f"Cleared plot data for {self.current_signal}")