import paramiko
import socket
import logging
from typing import Optional, Tuple, List
from models import SSHConnection, LogEntry, QNAPCommands
import datetime

logger = logging.getLogger(__name__)

class SSHManager:
    """Manages SSH connections to QNAP NAS devices"""
    
    def __init__(self):
        self.client: Optional[paramiko.SSHClient] = None
        self.connection_info: Optional[SSHConnection] = None
        self.command_log: List[LogEntry] = []
    
    def connect(self, host: str, username: str, password: str, port: int = 22) -> Tuple[bool, str]:
        """
        Establish SSH connection to QNAP NAS
        
        Args:
            host: IP address or hostname of the NAS
            username: SSH username
            password: SSH password
            port: SSH port (default 22)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Disconnect existing connection if any
            self.disconnect()
            
            # Create new SSH client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Attempt connection with timeout
            self.client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10,
                auth_timeout=10
            )
            
            # Test connection with a simple command
            success, output, error = self.execute_command("echo 'Connection test'")
            if not success:
                self.disconnect()
                return False, f"Connection test failed: {error}"
            
            # Store connection info
            self.connection_info = SSHConnection(
                host=host,
                username=username,
                port=port,
                is_connected=True,
                connected_at=datetime.datetime.now()
            )
            
            logger.info(f"SSH connection established to {host}:{port} as {username}")
            return True, f"Successfully connected to {host}"
            
        except paramiko.AuthenticationException:
            error_msg = "Authentication failed. Please check username and password."
            logger.error(error_msg)
            return False, error_msg
            
        except paramiko.SSHException as e:
            error_msg = f"SSH connection error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
        except socket.timeout:
            error_msg = "Connection timeout. Please check the IP address and network connectivity."
            logger.error(error_msg)
            return False, error_msg
            
        except socket.gaierror:
            error_msg = "Could not resolve hostname. Please check the IP address."
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("SSH connection closed")
            except Exception as e:
                logger.error(f"Error closing SSH connection: {e}")
            finally:
                self.client = None
                
        if self.connection_info:
            self.connection_info.is_connected = False
            self.connection_info = None
    
    def is_connected(self) -> bool:
        """Check if SSH connection is active"""
        if not self.client or not self.connection_info:
            return False
            
        try:
            # Test connection with a simple command
            transport = self.client.get_transport()
            return transport is not None and transport.is_active()
        except:
            return False
    
    def execute_command(self, command: str) -> Tuple[bool, str, str]:
        """
        Execute a command on the remote QNAP NAS
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        if not self.is_connected():
            return False, "", "Not connected to NAS"
        
        try:
            if not self.client:
                return False, "", "SSH client not initialized"
            stdin, stdout, stderr = self.client.exec_command(command, timeout=30)
            stdout_data = stdout.read().decode('utf-8').strip()
            stderr_data = stderr.read().decode('utf-8').strip()
            exit_status = stdout.channel.recv_exit_status()
            
            success = exit_status == 0
            
            # Log the command execution
            log_entry = LogEntry(
                timestamp=datetime.datetime.now(),
                command=command,
                response=stdout_data if success else stderr_data,
                success=success,
                error_message=stderr_data if not success else None
            )
            self.command_log.append(log_entry)
            
            # Keep only last 100 log entries
            if len(self.command_log) > 100:
                self.command_log = self.command_log[-100:]
            
            logger.debug(f"Command executed: {command}, Success: {success}")
            return success, stdout_data, stderr_data
            
        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            log_entry = LogEntry(
                timestamp=datetime.datetime.now(),
                command=command,
                response="",
                success=False,
                error_message=error_msg
            )
            self.command_log.append(log_entry)
            logger.error(error_msg)
            return False, "", error_msg
    
    def detect_qm2_card(self) -> Tuple[bool, str]:
        """
        Detect QM2 card enc_sys_id automatically
        
        Returns:
            Tuple of (success: bool, enc_sys_id or error_message: str)
        """
        if not self.is_connected():
            return False, "Not connected to NAS"
        
        success, stdout, stderr = self.execute_command(QNAPCommands.get_enum_command())
        if not success:
            return False, f"Failed to enumerate devices: {stderr}"
        
        # Parse output to find QM2 card
        lines = stdout.split('\n')
        for line in lines:
            if 'qm2' in line.lower() and 'QM2' in line:
                # Extract enc_sys_id (typically the 3rd column)
                parts = line.split()
                if len(parts) >= 3:
                    enc_sys_id = parts[2]  # qm2_1_11.32 format
                    if self.connection_info is not None:
                        self.connection_info.qm2_enc_sys_id = enc_sys_id
                    return True, enc_sys_id
        
        return False, "No QM2 card found. Make sure you have a QM2 expansion card installed."
    
    def set_fan_speed(self, speed_value: str, enc_sys_id: str = None) -> Tuple[bool, str]:
        """
        Set QNAP QM2 fan speed using hal_app commands
        
        Args:
            speed_value: Fan speed value (auto, silent, low, medium, high, max)
            enc_sys_id: QM2 card identifier (if None, will try to detect)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_connected():
            return False, "Not connected to NAS"
        
        # Auto-detect QM2 card if not provided
        if not enc_sys_id:
            if self.connection_info and self.connection_info.qm2_enc_sys_id:
                enc_sys_id = self.connection_info.qm2_enc_sys_id
            else:
                success, detected_id = self.detect_qm2_card()
                if not success:
                    return False, detected_id
                enc_sys_id = detected_id
        
        # Ensure enc_sys_id is not None at this point
        if not enc_sys_id:
            return False, "Could not determine QM2 card identifier"
        
        # Find the speed option
        speed_option = None
        for option in QNAPCommands.FAN_SPEED_OPTIONS:
            if option.value == speed_value:
                speed_option = option
                break
        
        if not speed_option:
            return False, f"Invalid fan speed value: {speed_value}"
        
        # Execute appropriate command
        if speed_option.command == "restore_default":
            # Restore default fan settings
            command = QNAPCommands.restore_default_fan_command(enc_sys_id)
        else:
            # Set manual PWM mode first, then set PWM value
            mode_command = QNAPCommands.set_fan_mode_command(enc_sys_id, 1)
            success, stdout, stderr = self.execute_command(mode_command)
            if not success:
                return False, f"Failed to set fan mode: {stderr}"
            
            # Set PWM value
            pwm_value = int(speed_option.command)
            command = QNAPCommands.set_fan_pwm_command(enc_sys_id, pwm_value)
        
        success, stdout, stderr = self.execute_command(command)
        if success:
            return True, f"Fan speed set to {speed_option.label} (QM2: {enc_sys_id or 'Unknown'})"
        else:
            return False, f"Failed to set fan speed: {stderr or 'Unknown error'}"
    
    def get_fan_status(self, enc_sys_id: str = None) -> Tuple[bool, str]:
        """
        Get current fan status from QNAP QM2 card
        
        Args:
            enc_sys_id: QM2 card identifier (if None, will try to detect)
        
        Returns:
            Tuple of (success: bool, status: str)
        """
        if not self.is_connected():
            return False, "Not connected to NAS"
        
        # Auto-detect QM2 card if not provided
        if not enc_sys_id:
            if self.connection_info and self.connection_info.qm2_enc_sys_id:
                enc_sys_id = self.connection_info.qm2_enc_sys_id
            else:
                success, detected_id = self.detect_qm2_card()
                if not success:
                    return False, detected_id
                enc_sys_id = detected_id
        
        # Ensure enc_sys_id is not None at this point
        if not enc_sys_id:
            return False, "Could not determine QM2 card identifier"
        
        # Get fan status and PWM
        status_info = []
        
        # Get general fan status
        status_cmd = QNAPCommands.get_fan_status_command(enc_sys_id)
        success, stdout, stderr = self.execute_command(status_cmd)
        if success and stdout:
            status_info.append(f"Fan Status: {stdout.strip()}")
        
        # Get PWM value
        pwm_cmd = QNAPCommands.get_fan_pwm_command(enc_sys_id)
        success, stdout, stderr = self.execute_command(pwm_cmd)
        if success and stdout:
            status_info.append(f"PWM: {stdout.strip()}")
        
        if status_info:
            return True, " | ".join(status_info)
        else:
            return False, "Could not retrieve fan status"
    
    def get_connection_info(self) -> Optional[SSHConnection]:
        """Get current connection information"""
        return self.connection_info
    
    def get_command_log(self) -> List[LogEntry]:
        """Get command execution log"""
        return self.command_log.copy()
    
    def clear_log(self):
        """Clear command execution log"""
        self.command_log.clear()
