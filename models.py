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
    """QNAP-specific commands for fan control"""
    
    # Common QNAP fan control commands
    FAN_SPEED_OPTIONS = [
        FanSpeedOption("Auto", "auto", "echo 0 > /sys/devices/platform/pwm_fan/hwmon/hwmon0/pwm1"),
        FanSpeedOption("Low (25%)", "low", "echo 1 > /sys/devices/platform/pwm_fan/hwmon/hwmon0/pwm1"),
        FanSpeedOption("Medium (50%)", "medium", "echo 2 > /sys/devices/platform/pwm_fan/hwmon/hwmon0/pwm1"),
        FanSpeedOption("High (75%)", "high", "echo 3 > /sys/devices/platform/pwm_fan/hwmon/hwmon0/pwm1"),
        FanSpeedOption("Maximum (100%)", "max", "echo 4 > /sys/devices/platform/pwm_fan/hwmon/hwmon0/pwm1")
    ]
    
    # Alternative commands for different QNAP models
    ALTERNATIVE_COMMANDS = {
        "auto": [
            "qcontrol fan auto",
            "/usr/bin/qcontrol fan auto",
            "echo auto > /proc/qnap/fan_speed"
        ],
        "low": [
            "qcontrol fan 1",
            "/usr/bin/qcontrol fan 1",
            "echo 1 > /proc/qnap/fan_speed"
        ],
        "medium": [
            "qcontrol fan 2",
            "/usr/bin/qcontrol fan 2",
            "echo 2 > /proc/qnap/fan_speed"
        ],
        "high": [
            "qcontrol fan 3",
            "/usr/bin/qcontrol fan 3",
            "echo 3 > /proc/qnap/fan_speed"
        ],
        "max": [
            "qcontrol fan 4",
            "/usr/bin/qcontrol fan 4",
            "echo 4 > /proc/qnap/fan_speed"
        ]
    }
    
    @classmethod
    def get_status_commands(cls):
        """Commands to check current fan status"""
        return [
            "cat /sys/devices/platform/pwm_fan/hwmon/hwmon0/pwm1",
            "qcontrol fan status",
            "cat /proc/qnap/fan_speed"
        ]
