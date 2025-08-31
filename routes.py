from flask import render_template, request, jsonify, session, redirect, url_for
from app import app
from ssh_manager import SSHManager
from models import QNAPCommands
import logging
import re

logger = logging.getLogger(__name__)

# Global SSH manager instance (in production, use proper session management)
ssh_managers = {}

def get_ssh_manager():
    """Get SSH manager for current session"""
    import uuid
    session_id = session.get('session_id')
    if not session_id:
        session['session_id'] = str(uuid.uuid4())
        session_id = session['session_id']
    
    if session_id not in ssh_managers:
        ssh_managers[session_id] = SSHManager()
    
    return ssh_managers[session_id]

@app.route('/')
def index():
    """Main page"""
    ssh_manager = get_ssh_manager()
    connection_info = ssh_manager.get_connection_info()
    fan_options = QNAPCommands.FAN_SPEED_OPTIONS
    
    return render_template('index.html', 
                         connection_info=connection_info,
                         fan_options=fan_options)

@app.route('/connect', methods=['POST'])
def connect():
    """Handle SSH connection"""
    try:
        data = request.get_json()
        host = data.get('host', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        port = int(data.get('port', 22))
        
        # Validate input
        if not host or not username or not password:
            return jsonify({
                'success': False,
                'message': 'All fields are required'
            })
        
        # Validate IP address format (basic validation)
        ip_pattern = re.compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        if not ip_pattern.match(host) and not re.match(r'^[a-zA-Z0-9.-]+$', host):
            return jsonify({
                'success': False,
                'message': 'Invalid IP address or hostname format'
            })
        
        # Validate port
        if not 1 <= port <= 65535:
            return jsonify({
                'success': False,
                'message': 'Port must be between 1 and 65535'
            })
        
        ssh_manager = get_ssh_manager()
        success, message = ssh_manager.connect(host, username, password, port)
        
        response_data = {
            'success': success,
            'message': message
        }
        
        if success:
            connection_info = ssh_manager.get_connection_info()
            response_data['connection_info'] = {
                'host': connection_info.host,
                'username': connection_info.username,
                'port': connection_info.port,
                'connected_at': connection_info.connected_at.strftime('%Y-%m-%d %H:%M:%S'),
                'qm2_enc_sys_id': connection_info.qm2_enc_sys_id
            }
            
            # Try to auto-detect QM2 card
            success_detect, qm2_id = ssh_manager.detect_qm2_card()
            if success_detect:
                response_data['qm2_detected'] = qm2_id
        
        return jsonify(response_data)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': 'Invalid port number'
        })
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return jsonify({
            'success': False,
            'message': f'Connection failed: {str(e)}'
        })

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Handle SSH disconnection"""
    try:
        ssh_manager = get_ssh_manager()
        ssh_manager.disconnect()
        
        return jsonify({
            'success': True,
            'message': 'Disconnected successfully'
        })
        
    except Exception as e:
        logger.error(f"Disconnection error: {e}")
        return jsonify({
            'success': False,
            'message': f'Disconnection failed: {str(e)}'
        })

@app.route('/set_fan_speed', methods=['POST'])
def set_fan_speed():
    """Set fan speed"""
    try:
        data = request.get_json()
        speed_value = data.get('speed')
        
        if not speed_value:
            return jsonify({
                'success': False,
                'message': 'Fan speed value is required'
            })
        
        ssh_manager = get_ssh_manager()
        if not ssh_manager.is_connected():
            return jsonify({
                'success': False,
                'message': 'Not connected to NAS'
            })
        
        success, message = ssh_manager.set_fan_speed(speed_value)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Set fan speed error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to set fan speed: {str(e)}'
        })

@app.route('/get_fan_status', methods=['GET'])
def get_fan_status():
    """Get current fan status"""
    try:
        ssh_manager = get_ssh_manager()
        if not ssh_manager.is_connected():
            return jsonify({
                'success': False,
                'message': 'Not connected to NAS'
            })
        
        success, status = ssh_manager.get_fan_status()
        
        return jsonify({
            'success': success,
            'status': status if success else 'Unknown',
            'message': 'Fan status retrieved' if success else status
        })
        
    except Exception as e:
        logger.error(f"Get fan status error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get fan status: {str(e)}'
        })

@app.route('/get_logs', methods=['GET'])
def get_logs():
    """Get command execution logs"""
    try:
        ssh_manager = get_ssh_manager()
        logs = ssh_manager.get_command_log()
        
        # Convert logs to JSON-serializable format
        log_data = []
        for log in logs:
            log_data.append({
                'timestamp': log.timestamp.strftime('%H:%M:%S'),
                'command': log.command,
                'response': log.response,
                'success': log.success,
                'error_message': log.error_message
            })
        
        return jsonify({
            'success': True,
            'logs': log_data
        })
        
    except Exception as e:
        logger.error(f"Get logs error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get logs: {str(e)}'
        })

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    """Clear command execution logs"""
    try:
        ssh_manager = get_ssh_manager()
        ssh_manager.clear_log()
        
        return jsonify({
            'success': True,
            'message': 'Logs cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Clear logs error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to clear logs: {str(e)}'
        })

@app.route('/connection_status', methods=['GET'])
def connection_status():
    """Get current connection status"""
    try:
        ssh_manager = get_ssh_manager()
        is_connected = ssh_manager.is_connected()
        connection_info = ssh_manager.get_connection_info()
        
        response_data = {
            'success': True,
            'is_connected': is_connected
        }
        
        if is_connected and connection_info:
            response_data['connection_info'] = {
                'host': connection_info.host,
                'username': connection_info.username,
                'port': connection_info.port,
                'connected_at': connection_info.connected_at.strftime('%Y-%m-%d %H:%M:%S'),
                'qm2_enc_sys_id': connection_info.qm2_enc_sys_id
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Connection status error: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get connection status: {str(e)}'
        })
