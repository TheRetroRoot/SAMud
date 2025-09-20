"""Configuration module for SAMUD - loads settings from environment variables."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 2323))
MAX_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', 50))
BUFFER_SIZE = int(os.getenv('BUFFER_SIZE', 4096))
ENCODING = 'utf-8'

# Database Configuration
DB_PATH = Path(os.getenv('DB_PATH', 'data/samud.db'))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Game Configuration
IDLE_TIMEOUT = int(os.getenv('IDLE_TIMEOUT', 1800))  # 30 minutes in seconds
IDLE_WARNING_TIME = IDLE_TIMEOUT - 300  # Warn 5 minutes before timeout
DEFAULT_ROOM = 'alamo_plaza'
MAX_MESSAGE_LENGTH = 250
MAX_INPUT_LENGTH = 1024
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 20
MIN_PASSWORD_LENGTH = 6

# Telnet Configuration
TELNET_IAC = bytes([255])  # Interpret as Command
TELNET_WILL = bytes([251])
TELNET_WONT = bytes([252])
TELNET_DO = bytes([253])
TELNET_DONT = bytes([254])
TELNET_ECHO = bytes([1])
TELNET_SGA = bytes([3])  # Suppress Go Ahead

# Room IDs - used throughout the application
ROOM_IDS = {
    'alamo_plaza': 'The Alamo Plaza',
    'river_walk_north': 'River Walk North',
    'river_walk_south': 'River Walk South',
    'pearl': 'The Pearl',
    'tower': 'Tower of the Americas',
    'mission': 'Mission San Jose',
    'southtown': 'Southtown'
}

# Command List - all available commands
COMMANDS = {
    'look': 'Show room description, exits, and players',
    'say': 'Say something to everyone in the room',
    'shout': 'Shout a message to all players',
    'move': 'Move in a direction (e.g., move north)',
    'n': 'Move north',
    's': 'Move south',
    'e': 'Move east',
    'w': 'Move west',
    'who': 'Show all online players',
    'where': 'Show your current location',
    'help': 'Show this help message',
    'quit': 'Save and disconnect'
}

# Movement shortcuts
MOVEMENT_SHORTCUTS = {
    'n': 'north',
    's': 'south',
    'e': 'east',
    'w': 'west'
}

# Message formatting
ROOM_MESSAGE_FORMAT = "[Room] {username}: {message}"
GLOBAL_MESSAGE_FORMAT = "[Global] {username}: {message}"
SYSTEM_MESSAGE_FORMAT = "[System] {message}"

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)

# Rate limiting
MESSAGE_RATE_LIMIT = 5  # messages
MESSAGE_RATE_WINDOW = 10  # seconds