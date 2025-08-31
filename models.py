from dataclasses import dataclass
from typing import Optional, List, Dict
import datetime

@dataclass
class SSHConnection:
    """Data class for SSH connection information"""
    host: str
    username: str
    port: int = 22
    is_connected: bool = False
    connected_at: Optional[datetime.datetime] = None
    qm2_enc_sys_id: Optional[str] = None  # Store detected QM2 card ID

@dataclass
class LogEntry:
    """Data class for command log entries"""
    timestamp: datetime.datetime
    command: str
    response: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class FanSpeedOption:
    """Data class for fan speed options"""
    label: str
    value: str
    command: str

class QNAPCommands:
    """QNAP-specific commands for QM2 card fan control using hal_app"""
    
    # PWM values for different fan speeds (adjust based on your needs)
    FAN_SPEED_OPTIONS = [
        FanSpeedOption("Auto/Default", "auto", "restore_default"),  # Special command
        FanSpeedOption("Silent (PWM 50)", "silent", "50"),
        FanSpeedOption("Low (PWM 75)", "low", "75"), 
        FanSpeedOption("Medium (PWM 100)", "medium", "100"),
        FanSpeedOption("High (PWM 150)", "high", "150"),
        FanSpeedOption("Maximum (PWM 200)", "max", "200")
    ]
    
    @classmethod
    def get_enum_command(cls):
        """Command to enumerate QM2 cards"""
        return "hal_app --se_enum"
    
    @classmethod
    def get_fan_status_command(cls, enc_sys_id: str):
        """Command to get current fan status"""
        return f"hal_app --se_sys_get_fan enc_sys_id={enc_sys_id},obj_index=0"
    
    @classmethod
    def get_fan_pwm_command(cls, enc_sys_id: str):
        """Command to get current fan PWM"""
        return f"hal_app --se_sys_get_fan_pwm enc_sys_id={enc_sys_id},obj_index=0"
    
    @classmethod
    def set_fan_mode_command(cls, enc_sys_id: str, mode: int = 1):
        """Command to set fan mode"""
        return f"hal_app --se_sys_set_fan_mode enc_sys_id={enc_sys_id},obj_index=0,mode={mode}"
    
    @classmethod
    def set_fan_pwm_command(cls, enc_sys_id: str, pwm: int):
        """Command to set fan PWM"""
        return f"hal_app --se_sys_set_fan_pwm enc_sys_id={enc_sys_id},pwm={pwm}"
    
    @classmethod
    def restore_default_fan_command(cls, enc_sys_id: str):
        """Command to restore default fan settings"""
        return f"hal_app --se_sys_sys_restore_default_fan enc_sys_id={enc_sys_id}"
