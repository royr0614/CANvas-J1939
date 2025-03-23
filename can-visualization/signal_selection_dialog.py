from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
                           QPushButton, QLabel, QLineEdit, QCheckBox, QMessageBox,
                           QGroupBox, QSplitter, QApplication, QHeaderView, QComboBox)
from PyQt5.QtCore import Qt, QSettings, pyqtSignal
import logging

class SignalSelectionDialog(QDialog):
    """
    Dialog for selecting specific signals from a large DBC file.
    Limits the number of signals that can be selected.
    """
    # Signal emitted when user completes selection
    selection_complete = pyqtSignal(list)
    
    def __init__(self, dbc_parser, parent=None, max_signals=10):
        super().__init__(parent)
        self.dbc_parser = dbc_parser
        self.max_signals = max_signals  # Configurable maximum number of signals
        self.selected_signals = []  # List to store selected signals
        self.logger = logging.getLogger("SignalSelectionDialog")
        
        self.setWindowTitle("Select Signals to Monitor")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.populate_message_tree()
        
    def setup_ui(self):
        """Set up the dialog user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Info label with max signals limit
        info_label = QLabel(f"Select up to {self.max_signals} signals to monitor. " 
                         f"Limiting the number of signals prevents performance issues with large DBC files.")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Search controls
        search_group = QGroupBox("Search")
        search_layout = QHBoxLayout(search_group)
        
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter message or signal name to filter")
        self.search_input.textChanged.connect(self.filter_tree)
        search_layout.addWidget(self.search_input)
        
        search_layout.addWidget(QLabel("Filter:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Messages", "Signals"])
        self.filter_combo.currentIndexChanged.connect(self.filter_tree)
        search_layout.addWidget(self.filter_combo)
        
        layout.addWidget(search_group)
        
        # Create splitter for tree and selection
        splitter = QSplitter(Qt.Horizontal)
        
        # Message and signal tree
        tree_group = QGroupBox("Available Signals")
        tree_layout = QVBoxLayout(tree_group)
        
        self.message_tree = QTreeWidget()
        self.message_tree.setHeaderLabels(["Name", "ID/Details"])
        self.message_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.message_tree.itemChanged.connect(self.on_item_checked)
        tree_layout.addWidget(self.message_tree)
        
        # Quick select buttons
        buttons_layout = QHBoxLayout()
        self.expand_all_button = QPushButton("Expand All")
        self.expand_all_button.clicked.connect(self.message_tree.expandAll)
        buttons_layout.addWidget(self.expand_all_button)
        
        self.collapse_all_button = QPushButton("Collapse All")
        self.collapse_all_button.clicked.connect(self.message_tree.collapseAll)
        buttons_layout.addWidget(self.collapse_all_button)
        
        self.select_none_button = QPushButton("Select None")
        self.select_none_button.clicked.connect(self.select_none)
        buttons_layout.addWidget(self.select_none_button)
        
        tree_layout.addLayout(buttons_layout)
        
        # Selected signals group
        selected_group = QGroupBox("Selected Signals")
        selected_layout = QVBoxLayout(selected_group)
        
        self.selection_counter = QLabel(f"0/{self.max_signals} signals selected")
        selected_layout.addWidget(self.selection_counter)
        
        self.selected_tree = QTreeWidget()
        self.selected_tree.setHeaderLabels(["Message", "Signal", "ID"])
        self.selected_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        selected_layout.addWidget(self.selected_tree)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected_signal)
        selected_layout.addWidget(self.remove_button)
        
        # Add both groups to splitter
        splitter.addWidget(tree_group)
        splitter.addWidget(selected_group)
        splitter.setSizes([500, 300])
        
        layout.addWidget(splitter)
        
        # OK and Cancel buttons
        buttons_layout = QHBoxLayout()
        
        # Save/Load profile buttons
        self.save_profile_button = QPushButton("Save Selection Profile")
        self.save_profile_button.clicked.connect(self.save_selection_profile)
        buttons_layout.addWidget(self.save_profile_button)
        
        self.load_profile_button = QPushButton("Load Selection Profile")
        self.load_profile_button.clicked.connect(self.load_selection_profile)
        buttons_layout.addWidget(self.load_profile_button)
        
        buttons_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_selection)
        buttons_layout.addWidget(self.ok_button)
        
        layout.addLayout(buttons_layout)
    
    def populate_message_tree(self):
        """Populate the tree with messages and signals from the DBC"""
        self.message_tree.clear()
        self.message_tree.setUpdatesEnabled(False)  # Disable updates for faster loading
        
        # Get all message IDs from DBC
        message_ids = self.dbc_parser.get_all_message_ids()
        if not message_ids:
            self.logger.warning("No messages found in DBC file")
            self.message_tree.setUpdatesEnabled(True)
            return
            
        for msg_id in message_ids:
            message = self.dbc_parser.get_message_by_id(msg_id)
            if not message:
                continue
            
            # Create message item
            msg_item = QTreeWidgetItem([
                message.name, 
                f"ID: 0x{msg_id:X}"
            ])
            msg_item.setFlags(msg_item.flags() | Qt.ItemIsUserCheckable)
            msg_item.setCheckState(0, Qt.Unchecked)
            self.message_tree.addTopLevelItem(msg_item)
            
            # Add signals as children
            for signal in message.signals:
                details = []
                if signal.minimum is not None:
                    details.append(f"Min: {signal.minimum}")
                if signal.maximum is not None:
                    details.append(f"Max: {signal.maximum}")
                if signal.unit:
                    details.append(f"Unit: {signal.unit}")
                    
                detail_str = ", ".join(details)
                
                signal_item = QTreeWidgetItem([
                    signal.name,
                    detail_str
                ])
                signal_item.setData(0, Qt.UserRole, {
                    'type': 'signal',
                    'message_id': msg_id,
                    'message_name': message.name,
                    'signal_name': signal.name,
                    'unit': signal.unit or ""
                })
                signal_item.setFlags(signal_item.flags() | Qt.ItemIsUserCheckable)
                signal_item.setCheckState(0, Qt.Unchecked)
                msg_item.addChild(signal_item)
        
        self.message_tree.setUpdatesEnabled(True)  # Re-enable updates
    
    def filter_tree(self):
        """Filter the tree based on search text"""
        search_text = self.search_input.text().lower()
        filter_mode = self.filter_combo.currentText()
        
        self.message_tree.setUpdatesEnabled(False)  # Disable updates for better performance
        
        # Process all top-level items (messages)
        for i in range(self.message_tree.topLevelItemCount()):
            msg_item = self.message_tree.topLevelItem(i)
            msg_visible = False
            
            # Check if message matches search
            if filter_mode in ["All", "Messages"]:
                if search_text in msg_item.text(0).lower():
                    msg_visible = True
            
            # Process child items (signals)
            signal_visible = False
            for j in range(msg_item.childCount()):
                signal_item = msg_item.child(j)
                
                # Check if signal matches search
                if filter_mode in ["All", "Signals"]:
                    if search_text in signal_item.text(0).lower():
                        signal_item.setHidden(False)
                        signal_visible = True
                    else:
                        signal_item.setHidden(True)
                else:
                    # If not searching signals, hide/show based on message visibility
                    signal_item.setHidden(not msg_visible)
            
            # Show message if it or any of its signals match
            msg_item.setHidden(not (msg_visible or signal_visible))
            
            # Expand message items that match or contain matching signals
            if msg_visible or signal_visible:
                self.message_tree.expandItem(msg_item)
            else:
                self.message_tree.collapseItem(msg_item)
        
        self.message_tree.setUpdatesEnabled(True)  # Re-enable updates
    
    def on_item_checked(self, item, column):
        """Handle check state changes in the tree"""
        if column != 0:
            return
            
        # Temporarily disconnect the signal to prevent recursive calls
        self.message_tree.itemChanged.disconnect(self.on_item_checked)
        
        # Get check state
        checked = item.checkState(0) == Qt.Checked
        
        # Check if this is a message or signal item
        is_signal = item.parent() is not None
        
        if is_signal:
            # This is a signal item
            self.handle_signal_selection(item, checked)
        else:
            # This is a message item - propagate to all child signals
            for i in range(item.childCount()):
                signal_item = item.child(i)
                signal_item.setCheckState(0, item.checkState(0))
                self.handle_signal_selection(signal_item, checked)
        
        # Reconnect the signal
        self.message_tree.itemChanged.connect(self.on_item_checked)
    
    def handle_signal_selection(self, item, checked):
        """Handle signal selection/deselection"""
        # Extract signal data
        signal_data = item.data(0, Qt.UserRole)
        if not signal_data or signal_data.get('type') != 'signal':
            return
            
        # Check if already in selected list
        found = False
        for i, data in enumerate(self.selected_signals):
            if (data['message_id'] == signal_data['message_id'] and 
                data['signal_name'] == signal_data['signal_name']):
                if checked:
                    # Already selected
                    found = True
                    break
                else:
                    # Remove from selected list
                    self.selected_signals.pop(i)
                    found = True
                    break
        
        # Add to selected list if checked and not already in list
        if checked and not found:
            # Check if we're at the limit
            if len(self.selected_signals) >= self.max_signals:
                # Uncheck the item
                item.setCheckState(0, Qt.Unchecked)
                
                # Show warning
                QMessageBox.warning(self, "Selection Limit Reached", 
                                  f"You can select at most {self.max_signals} signals. "
                                  f"Deselect some signals before adding new ones.")
                return
                
            # Add to selected list
            self.selected_signals.append(signal_data)
        
        # Update selected signals display
        self.update_selected_display()
        
        # Update the parent message's check state
        self.update_parent_check_state(item.parent())
    
    def update_parent_check_state(self, parent_item):
        """Update a message item's check state based on its children"""
        if not parent_item:
            return
            
        # Count checked children
        total_count = parent_item.childCount()
        checked_count = 0
        
        for i in range(total_count):
            if parent_item.child(i).checkState(0) == Qt.Checked:
                checked_count += 1
        
        # Set parent state based on children
        if checked_count == 0:
            parent_item.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count:
            parent_item.setCheckState(0, Qt.Checked)
        else:
            parent_item.setCheckState(0, Qt.PartiallyChecked)
    
    def update_selected_display(self):
        """Update the display of selected signals"""
        self.selected_tree.clear()
        
        for signal_data in self.selected_signals:
            item = QTreeWidgetItem([
                signal_data['message_name'],
                signal_data['signal_name'],
                f"0x{signal_data['message_id']:X}"
            ])
            item.setData(0, Qt.UserRole, signal_data)
            self.selected_tree.addTopLevelItem(item)
        
        # Update counter
        self.selection_counter.setText(f"{len(self.selected_signals)}/{self.max_signals} signals selected")
    
    def remove_selected_signal(self):
        """Remove a signal from the selected list"""
        # Get selected items in the selected tree
        items = self.selected_tree.selectedItems()
        if not items:
            return
            
        # Remove from selected list
        for item in items:
            signal_data = item.data(0, Qt.UserRole)
            if signal_data:
                # Find and remove from selected signals
                for i, data in enumerate(self.selected_signals):
                    if (data['message_id'] == signal_data['message_id'] and 
                        data['signal_name'] == signal_data['signal_name']):
                        self.selected_signals.pop(i)
                        break
                
                # Uncheck the item in the main tree
                self.uncheck_signal_in_tree(signal_data)
        
        # Update display
        self.update_selected_display()
    
    def uncheck_signal_in_tree(self, signal_data):
        """Find and uncheck a signal in the main tree"""
        # Find the message item
        for i in range(self.message_tree.topLevelItemCount()):
            msg_item = self.message_tree.topLevelItem(i)
            message = self.dbc_parser.get_message_by_id(signal_data['message_id'])
            
            if message and msg_item.text(0) == message.name:
                # Find the signal item
                for j in range(msg_item.childCount()):
                    signal_item = msg_item.child(j)
                    if signal_item.text(0) == signal_data['signal_name']:
                        # Disconnect signal to prevent recursion
                        self.message_tree.itemChanged.disconnect(self.on_item_checked)
                        
                        # Uncheck the signal
                        signal_item.setCheckState(0, Qt.Unchecked)
                        
                        # Update parent message check state
                        self.update_parent_check_state(msg_item)
                        
                        # Reconnect signal
                        self.message_tree.itemChanged.connect(self.on_item_checked)
                        return
    
    def select_none(self):
        """Clear all selections"""
        # Disconnect signal to prevent multiple updates
        self.message_tree.itemChanged.disconnect(self.on_item_checked)
        
        # Uncheck all items
        for i in range(self.message_tree.topLevelItemCount()):
            msg_item = self.message_tree.topLevelItem(i)
            msg_item.setCheckState(0, Qt.Unchecked)
            
            for j in range(msg_item.childCount()):
                signal_item = msg_item.child(j)
                signal_item.setCheckState(0, Qt.Unchecked)
        
        # Clear selected signals
        self.selected_signals = []
        self.update_selected_display()
        
        # Reconnect signal
        self.message_tree.itemChanged.connect(self.on_item_checked)
    
    def accept_selection(self):
        """Accept the current selection and close the dialog"""
        if not self.selected_signals:
            # Confirm if no signals are selected
            response = QMessageBox.question(
                self, "No Signals Selected",
                "No signals are selected. Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if response == QMessageBox.No:
                return
        
        # Emit the selection complete signal
        self.selection_complete.emit(self.selected_signals)
        self.accept()
    
    def save_selection_profile(self):
        """Save the current selection profile"""
        if not self.selected_signals:
            QMessageBox.warning(self, "No Selection", "There are no signals selected to save.")
            return
            
        # Create a simple list of message_id + signal_name pairs for storage
        profile = [
            f"{data['message_id']}:{data['signal_name']}"
            for data in self.selected_signals
        ]
        
        # Save to settings
        settings = QSettings("CANVis", "SignalProfiles")
        
        # Get existing profiles
        existing_profiles = settings.value("profiles", {})
        if not isinstance(existing_profiles, dict):
            existing_profiles = {}
        
        # Prompt for profile name
        from PyQt5.QtWidgets import QInputDialog
        profile_name, ok = QInputDialog.getText(
            self, "Save Profile", "Enter a name for this profile:"
        )
        
        if ok and profile_name:
            existing_profiles[profile_name] = profile
            settings.setValue("profiles", existing_profiles)
            QMessageBox.information(self, "Profile Saved", f"Profile '{profile_name}' saved with {len(profile)} signals.")
    
    def load_selection_profile(self):
        """Load a selection profile"""
        # Get profiles from settings
        settings = QSettings("CANVis", "SignalProfiles")
        profiles = settings.value("profiles", {})
        
        if not profiles:
            QMessageBox.information(self, "No Profiles", "No saved profiles found.")
            return
        
        # Let user select a profile
        from PyQt5.QtWidgets import QInputDialog
        profile_name, ok = QInputDialog.getItem(
            self, "Load Profile", "Select a profile to load:",
            list(profiles.keys()), 0, False
        )
        
        if not ok or not profile_name:
            return
            
        # Clear current selection
        self.select_none()
        
        # Load the profile
        profile = profiles[profile_name]
        
        # Convert the simple stored format back to full signal data
        for signal_id in profile:
            try:
                # Parse the stored format
                msg_id_str, signal_name = signal_id.split(":", 1)
                msg_id = int(msg_id_str)
                
                # Get message information
                message = self.dbc_parser.get_message_by_id(msg_id)
                if not message:
                    continue
                    
                # Find the signal in the message
                signal_data = None
                for signal in message.signals:
                    if signal.name == signal_name:
                        signal_data = {
                            'type': 'signal',
                            'message_id': msg_id,
                            'message_name': message.name,
                            'signal_name': signal_name,
                            'unit': signal.unit or ""
                        }
                        break
                
                if signal_data and len(self.selected_signals) < self.max_signals:
                    self.selected_signals.append(signal_data)
                    
                    # Check the corresponding item in the tree
                    self.check_signal_in_tree(signal_data)
                
            except Exception as e:
                self.logger.error(f"Error loading profile item {signal_id}: {e}")
                continue
        
        # Update display
        self.update_selected_display()
        
        QMessageBox.information(
            self, "Profile Loaded", 
            f"Loaded {len(self.selected_signals)} signals from profile '{profile_name}'."
        )
    
    def check_signal_in_tree(self, signal_data):
        """Find and check a signal in the main tree"""
        # Find the message item
        for i in range(self.message_tree.topLevelItemCount()):
            msg_item = self.message_tree.topLevelItem(i)
            message = self.dbc_parser.get_message_by_id(signal_data['message_id'])
            
            if message and msg_item.text(0) == message.name:
                # Find the signal item
                for j in range(msg_item.childCount()):
                    signal_item = msg_item.child(j)
                    if signal_item.text(0) == signal_data['signal_name']:
                        # Disconnect signal to prevent recursion
                        self.message_tree.itemChanged.disconnect(self.on_item_checked)
                        
                        # Check the signal
                        signal_item.setCheckState(0, Qt.Checked)
                        
                        # Update parent message check state
                        self.update_parent_check_state(msg_item)
                        
                        # Reconnect signal
                        self.message_tree.itemChanged.connect(self.on_item_checked)
                        return