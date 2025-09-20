"""Main telnet server for SAMUD - handles connections and game loop."""

import asyncio
import logging
import signal
import sys
from typing import Dict, Optional
from datetime import datetime

from config import (
    HOST, PORT, MAX_CONNECTIONS, BUFFER_SIZE, ENCODING,
    TELNET_IAC, TELNET_WILL, TELNET_WONT, TELNET_DO, TELNET_DONT,
    TELNET_ECHO, TELNET_SGA, IDLE_TIMEOUT, IDLE_WARNING_TIME
)
from database import db

logger = logging.getLogger(__name__)

# Import auth after Client is defined
auth_manager = None


class Client:
    """Represents a connected telnet client."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.address = writer.get_extra_info('peername')
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()

        # Player state
        self.player_id: Optional[int] = None
        self.username: Optional[str] = None
        self.current_room: Optional[str] = None
        self.authenticated = False

        # Connection state
        self.is_active = True
        self.input_buffer = ""
        self.echo_enabled = True

        # Rate limiting
        self.message_times = []

        logger.info(f"Client connected from {self.address}")

    async def send(self, message: str):
        """Send a message to the client."""
        if not self.is_active or self.writer.is_closing():
            return

        try:
            # Ensure message ends with newline
            if not message.endswith('\n'):
                message += '\n'

            # Convert to bytes and send
            self.writer.write(message.encode(ENCODING))
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            logger.warning(f"Failed to send to {self.address}")
            self.is_active = False

    async def send_prompt(self):
        """Send the command prompt."""
        await self.send("\n> ")

    async def readline(self, echo=True) -> Optional[str]:
        """Read a line of input from the client - character by character for telnet compatibility.

        Args:
            echo: Whether to echo characters back to the client (False for password input)
        """
        try:
            line_buffer = []

            # For password input, suppress client echo
            if not echo:
                await self.send_raw(TELNET_IAC + TELNET_WILL + TELNET_ECHO)

            while True:
                # Read one byte at a time
                data = await asyncio.wait_for(
                    self.reader.read(1),
                    timeout=IDLE_TIMEOUT
                )

                if not data:
                    return None

                # Update activity time
                self.last_activity = datetime.now()

                byte = data[0]

                # Handle telnet IAC sequences
                if byte == 255:  # IAC
                    # Read next byte for command
                    cmd_data = await self.reader.read(1)
                    if cmd_data:
                        cmd = cmd_data[0]
                        # If it's WILL/WONT/DO/DONT, read the option byte
                        if cmd in [251, 252, 253, 254]:
                            await self.reader.read(1)
                    continue

                # Handle carriage return or line feed - end of line
                if byte in [10, 13]:  # LF or CR
                    # Try to consume CR+LF or LF+CR pairs
                    try:
                        next_byte = await asyncio.wait_for(
                            self.reader.read(1),
                            timeout=0.01
                        )
                        # Only consume if it's the paired line ending
                        if not (next_byte and next_byte[0] in [10, 13] and next_byte[0] != byte):
                            # Not a pair, this is real data - handle it differently
                            # For now, just ignore since most telnet sends CR or CR+LF
                            pass
                    except asyncio.TimeoutError:
                        pass  # No paired byte, that's fine

                    # Don't echo newline - client handles it

                    # Restore client echo after password input
                    if not echo:
                        await self.send_raw(TELNET_IAC + TELNET_WONT + TELNET_ECHO)

                    # Return the completed line
                    result = ''.join(line_buffer).strip()
                    return result

                # Handle backspace
                elif byte in [8, 127]:  # BS or DEL
                    if line_buffer:
                        line_buffer.pop()
                        # Only send backspace sequence for password mode (when we control echo)
                        if not echo:
                            await self.send_raw(b'\x08 \x08')

                # Handle printable ASCII
                elif 32 <= byte <= 126:
                    char = chr(byte)
                    line_buffer.append(char)
                    # Only echo for password mode (when we control echo)
                    if not echo:
                        await self.send_raw(b'*')

                # Ignore other control characters
                else:
                    continue

        except asyncio.TimeoutError:
            logger.info(f"Client {self.address} timed out")
            return None
        except Exception as e:
            logger.debug(f"Read error: {e}")
            return None

    def filter_telnet_commands(self, data: str) -> str:
        """Remove telnet IAC command sequences."""
        filtered = []
        i = 0

        while i < len(data):
            if i < len(data):
                char_code = ord(data[i])

                # IAC (255) followed by command
                if char_code == 255 and i + 1 < len(data):
                    next_code = ord(data[i + 1])
                    # Command with parameter (WILL/WONT/DO/DONT)
                    if next_code in [251, 252, 253, 254] and i + 2 < len(data):
                        i += 3  # Skip IAC, command, and parameter
                    # Two-byte command
                    else:
                        i += 2  # Skip IAC and command
                # Regular character
                else:
                    filtered.append(data[i])
                    i += 1

        return ''.join(filtered)

    async def setup_telnet(self):
        """Send initial telnet configuration."""
        # Suppress Go Ahead for better responsiveness
        await self.send_raw(TELNET_IAC + TELNET_WILL + TELNET_SGA)
        # Don't send WILL ECHO initially - let client echo locally by default

    async def send_raw(self, data: bytes):
        """Send raw bytes to client."""
        if not self.is_active or self.writer.is_closing():
            return

        try:
            self.writer.write(data)
            await self.writer.drain()
        except:
            self.is_active = False

    async def disconnect(self):
        """Clean disconnect of client."""
        self.is_active = False

        try:
            if self.player_id:
                await db.end_session(self.player_id)

            self.writer.close()
            await self.writer.wait_closed()
        except:
            pass

        logger.info(f"Client {self.address} disconnected")


class MudServer:
    """Main MUD server managing all connections and game state."""

    def __init__(self):
        self.clients: Dict[asyncio.Task, Client] = {}
        self.active_players: Dict[int, Client] = {}  # player_id -> Client
        self.server = None
        self.running = False

    async def start_server(self):
        """Start the telnet server."""
        # Initialize database
        logger.info("Initializing database...")
        await db.init_database()

        # Start server
        self.server = await asyncio.start_server(
            self.handle_client,
            HOST,
            PORT,
            limit=BUFFER_SIZE
        )

        self.running = True
        addr = self.server.sockets[0].getsockname()
        logger.info(f"SAMUD server running on {addr[0]}:{addr[1]}")
        logger.info(f"Connect with: telnet {addr[0]} {addr[1]}")

        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

        # Start background tasks
        asyncio.create_task(self.idle_check_task())

        async with self.server:
            await self.server.serve_forever()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        asyncio.create_task(self.shutdown())

    async def shutdown(self):
        """Graceful shutdown of the server."""
        self.running = False

        # Notify all clients
        for client in list(self.clients.values()):
            await client.send("\n[System] Server is shutting down. Goodbye!\n")
            await client.disconnect()

        # Close server
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        logger.info("Server shutdown complete")
        sys.exit(0)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a new client connection."""
        client = Client(reader, writer)
        task = asyncio.current_task()
        self.clients[task] = client

        try:
            # Check connection limit
            if len(self.clients) > MAX_CONNECTIONS:
                await client.send("Server is full. Please try again later.\n")
                return

            # Setup telnet
            await client.setup_telnet()

            # Send welcome message
            await self.send_welcome(client)

            # Authentication loop
            while client.is_active and self.running and not client.authenticated:
                # Send prompt
                await client.send_prompt()

                # Get input
                line = await client.readline()
                if line is None:
                    break

                # Handle pre-auth commands
                from auth import auth_manager
                success = await auth_manager.handle_welcome_choice(client, self, line)
                if success:
                    break

            # Main game loop (after authentication)
            while client.is_active and self.running and client.authenticated:
                # Send prompt
                await client.send_prompt()

                # Get input
                line = await client.readline()
                if line is None:
                    break

                # Process game commands
                if line:
                    from commands import command_processor
                    await command_processor.process_command(client, line)

        except Exception as e:
            logger.error(f"Error handling client {client.address}: {e}")

        finally:
            # Clean up player if authenticated
            if client.player_id:
                from player import player_manager
                await player_manager.remove_player(client.player_id)

            # Clean up connection
            await client.disconnect()
            if task in self.clients:
                del self.clients[task]
            if client.player_id and client.player_id in self.active_players:
                del self.active_players[client.player_id]

    async def send_welcome(self, client: Client):
        """Send welcome message to new connection."""
        welcome = """
================================================================
           Welcome to the San Antonio MUD (SAMUD)

   Experience the Alamo City through text-based adventure!

   Commands:
   * 'login' - Log in to existing account
   * 'signup' - Create a new account
   * 'help' - Show available commands
   * 'quit' - Disconnect from the server
================================================================

Type 'login' or 'signup' to begin your adventure!
"""
        await client.send(welcome)

    async def idle_check_task(self):
        """Background task to check for idle clients."""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute

                current_time = datetime.now()
                for client in list(self.clients.values()):
                    if not client.authenticated:
                        continue

                    idle_time = (current_time - client.last_activity).total_seconds()

                    # Send warning
                    if idle_time > IDLE_WARNING_TIME and idle_time < IDLE_TIMEOUT:
                        await client.send("\n[System] You will be disconnected in 5 minutes due to inactivity.\n")

                    # Disconnect idle clients
                    elif idle_time > IDLE_TIMEOUT:
                        await client.send("\n[System] Disconnected due to inactivity.\n")
                        client.is_active = False

            except Exception as e:
                logger.error(f"Error in idle check: {e}")

    def get_online_players(self):
        """Get list of online player usernames."""
        return [client.username for client in self.active_players.values()
                if client.username]


async def main():
    """Main entry point for the server."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    server = MudServer()
    try:
        await server.start_server()
    except KeyboardInterrupt:
        await server.shutdown()
    except Exception as e:
        logger.error(f"Fatal server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
