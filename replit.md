# QNAP NAS Fan Controller

## Overview

A web-based application for remotely controlling QNAP NAS fan speeds through SSH connections. The application provides a professional interface for network administrators to manage fan settings on QNAP devices, featuring real-time connection monitoring, command logging, and predefined fan speed options ranging from auto mode to maximum cooling.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Bootstrap 5 with dark theme for professional appearance
- **Structure**: Single-page application with real-time status updates
- **Components**: Connection panel, fan control interface, command log viewer
- **Styling**: Custom CSS with responsive design and status indicators

### Backend Architecture
- **Framework**: Flask with session management for multi-user support
- **Session Storage**: Filesystem-based sessions with signing for security
- **Architecture Pattern**: MVC with separate models, routes, and SSH management
- **Connection Management**: Per-session SSH manager instances to handle multiple concurrent users

### SSH Management
- **Library**: Paramiko for SSH client functionality
- **Connection Strategy**: Persistent connections per session with automatic reconnection
- **Command Execution**: Synchronous command execution with timeout handling
- **Error Handling**: Comprehensive error catching with user-friendly messages

### Data Models
- **SSHConnection**: Connection state and metadata tracking
- **LogEntry**: Command history with timestamps and status
- **FanSpeedOption**: Predefined fan speed configurations
- **QNAPCommands**: QNAP-specific command definitions with fallback options

### Security Considerations
- **Session Management**: Secure session handling with signed cookies
- **SSH Security**: Auto-accept host keys policy for ease of use
- **Input Validation**: Server-side validation for connection parameters
- **Password Handling**: In-memory password storage only during active sessions

## External Dependencies

### Python Libraries
- **Flask**: Web framework for HTTP handling and routing
- **Flask-Session**: Server-side session management
- **Paramiko**: SSH client library for secure shell connections
- **Logging**: Built-in Python logging for debugging and monitoring

### Frontend Dependencies
- **Bootstrap 5**: UI framework with dark theme support
- **Font Awesome 6**: Icon library for visual indicators
- **JavaScript (Vanilla)**: Client-side interaction handling

### QNAP Integration
- **SSH Protocol**: Direct SSH access to QNAP NAS devices
- **System Commands**: Hardware-level fan control through sysfs interface
- **Alternative Commands**: Fallback commands for different QNAP models
- **Fan Control Paths**: `/sys/devices/platform/pwm_fan/hwmon/hwmon0/pwm1` interface

### Development Environment
- **Replit Platform**: Cloud-based development and hosting
- **Python 3.x**: Runtime environment
- **File System**: Local file storage for session data