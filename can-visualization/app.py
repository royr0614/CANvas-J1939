from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import time
import logging
import argparse
import os
import json
import threading
import sys
from pathlib import Path

# Add the parent directory to sys.path to import the CAN modules
sys.path.append(str(Path(__file__).parent.parent))

# Import CAN modules
from dbc_parser import DBCParser
from can_simulator import DualCANSimulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('canvis_flask.log')
    ]
)
logger = logging.getLogger("CANVisFlask")

# Create Flask app
app = Flask(__name__, static_folder='frontend/build')
CORS(app)  # Enable CORS for all routes
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
dbc_parser = None
simulator = None
running = False
signals_data = {}  # Store signal data: {signal_id: {timestamps: [], values: []}}

# Parse arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='CAN Data Visualization Server')
    parser.add_argument('--dbc', help='Path to DBC file')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    return parser.parse_args()

# Routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/status')
def status():
    global dbc_parser, simulator, running
    return jsonify({
        'dbc_loaded': dbc_parser is not None and dbc_parser.db is not None,
        'running': running,
        'simulation': simulator is not None
    })

@app.route('/api/signals')
def get_signals():
    """Get available signals from the DBC file"""
    global dbc_parser
    
    if not dbc_parser or not dbc_parser.db:
        return jsonify({'error': 'No DBC file loaded'}), 400
    
    signals = []
    message_ids = dbc_parser.get_all_message_ids()
    
    for msg_id in message_ids:
        message = dbc_parser.get_message_by_id(msg_id)
        if not message:
            continue
        
        for signal in message.signals:
            signal_data = {
                'id': f"{message.name}.{signal.name}",
                'name': signal.name,
                'message': message.name,
                'message_id': msg_id,
                'min': signal.minimum if signal.minimum is not None else 0,
                'max': signal.maximum if signal.maximum is not None else 100,
                'unit': signal.unit if signal.unit else '',
            }
            signals.append(signal_data)
    
    return jsonify({'signals': signals})

@app.route('/api/signals/data')
def get_signals_data():
    """Get current signal data"""
    global signals_data
    
    # Get parameters
    signal_ids = request.args.get('ids', '').split(',')
    limit = request.args.get('limit', 100, type=int)
    
    result = {}
    for signal_id in signal_ids:
        if signal_id in signals_data:
            # Return the last N data points
            data = signals_data[signal_id]
            if len(data['values']) > limit:
                result[signal_id] = {
                    'timestamps': data['timestamps'][-limit:],
                    'values': data['values'][-limit:]
                }
            else:
                result[signal_id] = data
    
    return jsonify(result)

@app.route('/api/dbc', methods=['POST'])
def load_dbc():
    """Load a DBC file"""
    global dbc_parser
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save the file temporarily
    file_path = os.path.join(os.path.dirname(__file__), 'temp_dbc.dbc')
    file.save(file_path)
    
    # Create DBC parser if not exists
    if dbc_parser is None:
        dbc_parser = DBCParser()
    
    # Load the DBC file
    success = dbc_parser.load_dbc(file_path)
    
    if success:
        return jsonify({'message': 'DBC file loaded successfully'})
    else:
        return jsonify({'error': 'Failed to load DBC file'}), 500

@app.route('/api/start', methods=['POST'])
def start():
    """Start the CAN simulation"""
    global dbc_parser, simulator, running
    
    if not dbc_parser or not dbc_parser.db:
        return jsonify({'error': 'No DBC file loaded'}), 400
    
    if running:
        return jsonify({'message': 'Already running'})
    
    try:
        # Create simulator if not exists
        if simulator is None:
            simulator = DualCANSimulator(dbc_parser)
            simulator.add_sender_callback(process_can_message)
            simulator.add_receiver_callback(process_can_message)
        
        # Start simulator
        simulator.start()
        running = True
        
        return jsonify({'message': 'CAN simulation started'})
    except Exception as e:
        logger.error(f"Error starting CAN simulation: {e}")
        return jsonify({'error': f'Failed to start: {str(e)}'}), 500

@app.route('/api/stop', methods=['POST'])
def stop():
    """Stop the CAN simulation"""
    global simulator, running
    
    if not running:
        return jsonify({'message': 'Not running'})
    
    try:
        # Stop simulator
        if simulator:
            simulator.stop()
        running = False
        
        return jsonify({'message': 'CAN simulation stopped'})
    except Exception as e:
        logger.error(f"Error stopping CAN simulation: {e}")
        return jsonify({'error': f'Failed to stop: {str(e)}'}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected")
    emit('status', {
        'dbc_loaded': dbc_parser is not None and dbc_parser.db is not None,
        'running': running,
        'simulation': simulator is not None
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")

# Signal processing
def process_can_message(msg, interface_name):
    """Process CAN message and update signals"""
    global dbc_parser, signals_data
    
    try:
        # Decode the message
        decoded_data = dbc_parser.decode_message(msg.arbitration_id, msg.data)
        
        if decoded_data:
            logger.info(f"Successfully decoded message ID 0x{msg.arbitration_id:X}: {decoded_data}")
            # Get message definition
            message = dbc_parser.get_message_by_id(msg.arbitration_id)
            message_name = message.name if message else f"Unknown_0x{msg.arbitration_id:X}"
            
            # Process each signal
            current_time = time.time()
            for signal_name, value in decoded_data.items():
                # Create a unique ID for this signal
                signal_id = f"{message_name}.{signal_name}"
                logger.info(f"Emitting signal update: {signal_id}={value}")
                
                # Store signal data
                if signal_id not in signals_data:
                    signals_data[signal_id] = {
                        'timestamps': [],
                        'values': [],
                        'current_value': value,
                        'message_id': msg.arbitration_id,
                        'message_name': message_name,
                        'signal_name': signal_name,
                        'interface': interface_name
                    }
                
                # Update data
                signals_data[signal_id]['current_value'] = value
                signals_data[signal_id]['timestamps'].append(current_time)
                signals_data[signal_id]['values'].append(value)
                
                # Limit data points (keep last 1000)
                if len(signals_data[signal_id]['values']) > 1000:
                    signals_data[signal_id]['values'] = signals_data[signal_id]['values'][-1000:]
                    signals_data[signal_id]['timestamps'] = signals_data[signal_id]['timestamps'][-1000:]
                
                # Emit the update via WebSocket
                socketio.emit('signal_update', {
                    'id': signal_id,
                    'value': value,
                    'timestamp': current_time,
                    'message': message_name,
                    'signal': signal_name,
                    'interface': interface_name 
                })
    except Exception as e:
        logger.error(f"Error processing CAN message: {e}")

# Main function
def main():
    args = parse_arguments()
    
    # Load DBC file if specified
    global dbc_parser
    if args.dbc:
        dbc_parser = DBCParser()
        if dbc_parser.load_dbc(args.dbc):
            logger.info(f"DBC file loaded: {args.dbc}")
        else:
            logger.error(f"Failed to load DBC file: {args.dbc}")
    
    # Start the Flask app with SocketIO
    socketio.run(app, debug=args.debug, port=args.port, host='0.0.0.0')

if __name__ == "__main__":
    main()