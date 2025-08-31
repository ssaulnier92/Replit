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
    
    def set_fan_speed(self, speed_value: str) -> Tuple[bool, str]:
        """
        Set QNAP NAS fan speed
        
        Args:
            speed_value: Fan speed value (auto, low, medium, high, max)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.is_connected():
            return False, "Not connected to NAS"
        
        # Find the speed option
        speed_option = None
        for option in QNAPCommands.FAN_SPEED_OPTIONS:
            if option.value == speed_value:
                speed_option = option
                break
        
        if not speed_option:
            return False, f"Invalid fan speed value: {speed_value}"
        
        # Try primary command first
        success, stdout, stderr = self.execute_command(speed_option.command)
        if success:
            return True, f"Fan speed set to {speed_option.label}"
        
        # Try alternative commands if primary fails
        if speed_value in QNAPCommands.ALTERNATIVE_COMMANDS:
            for alt_command in QNAPCommands.ALTERNATIVE_COMMANDS[speed_value]:
                success, stdout, stderr = self.execute_command(alt_command)
                if success:
                    return True, f"Fan speed set to {speed_option.label} (using alternative command)"
        
        return False, f"Failed to set fan speed: {stderr or 'Unknown error'}"
    
    def get_fan_status(self) -> Tuple[bool, str]:
        """
        Get current fan status from QNAP NAS
        
        Returns:
            Tuple of (success: bool, status: str)
        """
        if not self.is_connected():
            return False, "Not connected to NAS"
        
        # Try different status commands
        for command in QNAPCommands.get_status_commands():
            success, stdout, stderr = self.execute_command(command)
            if success and stdout:
                return True, stdout
        
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
