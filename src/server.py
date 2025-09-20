"""Main telnet server for SAMUD - handles connections and game loop using telnetlib3."""

import asyncio
import logging
import signal
import sys
from typing import Dict, Optional
from datetime import datetime
import telnetlib3

from config import (
    HOST, PORT, MAX_CONNECTIONS, ENCODING,
    IDLE_TIMEOUT, IDLE_WARNING_TIME
)
from database import db
from npc_loader import npc_loader
from tick_scheduler import tick_scheduler
from npcs import npc_manager

logger = logging.getLogger(__name__)


class Client:
    """Represents a connected telnet client using telnetlib3."""

    def __init__(self, reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
        self.reader = reader
        self.writer = writer
        self.address = writer.transport.get_extra_info('peername')
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()

        # Player state
        self.player_id: Optional[int] = None
        self.username: Optional[str] = None
        self.current_room: Optional[str] = None
        self.authenticated = False

        # Connection state
        self.is_active = True

        # Rate limiting
        self.message_times = []

        logger.info(f"Client connected from {self.address}")

    async def send(self, message: str):
        """Send a message to the client."""
        if not self.is_active or self.writer.transport.is_closing():
            return

        try:
            # Convert message to proper line endings for telnet
            message = message.replace('\n', '\r\n')
            # Convert to bytes for binary mode
            self.writer.write(message.encode(ENCODING))
            await self.writer.drain()
        except (ConnectionError, BrokenPipeError):
            logger.warning(f"Failed to send to {self.address}")
            self.is_active = False

    async def send_prompt(self):
        """Send the command prompt."""
        self.writer.write(b"\r\n> ")
        await self.writer.drain()

    async def readline(self, echo=True) -> Optional[str]:
        """Read a line of input from the client with proper backspace handling.

        Args:
            echo: Whether to echo characters back to the client (False for password input)
        """
        try:
            # Update activity time
            self.last_activity = datetime.now()

            # Tell the client we will handle echo (suppress local echo)
            self.writer.iac(telnetlib3.WILL, telnetlib3.ECHO)
            await self.writer.drain()

            # Read character by character to handle backspace properly
            line_buffer = []

            while True:
                # telnetlib3 reader provides readexactly for raw bytes
                try:
                    char = await asyncio.wait_for(
                        self.reader.readexactly(1),
                        timeout=IDLE_TIMEOUT
                    )
                except asyncio.IncompleteReadError:
                    # Connection closed
                    return None

                if not char:
                    return None

                # Handle telnet IAC sequences
                if char == bytes([255]):  # IAC
                    # Read command byte
                    try:
                        cmd = await self.reader.readexactly(1)
                        # If it's WILL/WONT/DO/DONT, read option byte
                        if cmd[0] in [251, 252, 253, 254]:
                            await self.reader.readexactly(1)
                    except:
                        pass
                    continue

                # Check for newline (Enter key)
                if char in (b'\r', b'\n'):
                    # Consume any following CR/LF
                    try:
                        next_char = await asyncio.wait_for(
                            self.reader.readexactly(1),
                            timeout=0.01
                        )
                        # If it's not a paired line ending, we've consumed it
                        # but that's okay for line endings
                    except (asyncio.TimeoutError, asyncio.IncompleteReadError):
                        pass

                    # Send newline to client
                    self.writer.write(b'\r\n')
                    await self.writer.drain()
                    break

                # Handle backspace
                if char in (b'\x08', b'\x7f'):  # BS or DEL
                    if line_buffer:
                        line_buffer.pop()
                        # Send backspace sequence to erase the character
                        self.writer.write(b'\b \b')
                        await self.writer.drain()
                # Handle regular printable characters
                elif 32 <= char[0] <= 126:
                    char_str = chr(char[0])
                    line_buffer.append(char_str)

                    if echo:
                        # Echo the character back
                        self.writer.write(char)  # char is already bytes
                        await self.writer.drain()
                    else:
                        # Echo an asterisk for password
                        self.writer.write(b'*')
                        await self.writer.drain()
                # Ignore other control characters
                else:
                    continue

            # Tell client to resume local echo
            self.writer.iac(telnetlib3.WONT, telnetlib3.ECHO)
            await self.writer.drain()

            return ''.join(line_buffer).strip()

        except asyncio.TimeoutError:
            logger.info(f"Client {self.address} timed out")
            return None
        except Exception as e:
            logger.debug(f"Read error: {e}")
            return None

    async def disconnect(self):
        """Clean disconnect of client."""
        self.is_active = False

        try:
            if self.player_id:
                await db.end_session(self.player_id)

            self.writer.close()
        except:
            pass

        logger.info(f"Client {self.address} disconnected")


class MudServer:
    """Main MUD server managing all connections and game state."""

    def __init__(self):
        self.clients: Dict[asyncio.Task, Client] = {}
        self.active_players: Dict[int, Client] = {}  # player_id -> Client
        self.running = False

    async def _initialize_npcs(self):
        """Initialize NPC system."""
        from world import world
        from room_loader import RoomLoader

        # Load room NPCs configuration
        room_loader = RoomLoader()
        room_loader.load_all_rooms()  # This loads room configurations
        room_npcs = room_loader.get_room_npcs()

        # Pass room NPCs to NPC loader
        npc_loader.room_npcs = room_npcs

        # Load and initialize NPCs
        num_npcs = await npc_loader.initialize_npcs()
        logger.info(f"Loaded {num_npcs} NPCs")

        # Register NPCs with tick scheduler for movement and ambient actions
        for npc_id, npc in npc_manager.npcs.items():
            if npc.movement and 'tick_interval' in npc.movement:
                tick_interval = npc.movement['tick_interval']
                await tick_scheduler.register_npc_movement(npc_id, tick_interval)

            if npc.ambient_actions:
                await tick_scheduler.register_npc_ambient(npc_id)

        # Start the tick scheduler
        await tick_scheduler.start()
        logger.info("Tick scheduler started for NPC behaviors")

    async def start_server(self):
        """Start the telnet server."""
        # Initialize database
        logger.info("Initializing database...")
        await db.init_database()

        # Initialize NPCs
        logger.info("Loading NPCs...")
        await self._initialize_npcs()

        # Start telnetlib3 server
        self.running = True

        logger.info(f"SAMUD server starting on {HOST}:{PORT}")
        logger.info(f"Connect with: telnet {HOST} {PORT}")

        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))

        # Start background tasks
        asyncio.create_task(self.idle_check_task())

        # Create and run the telnetlib3 server with proper settings
        await telnetlib3.create_server(
            host=HOST,
            port=PORT,
            shell=self.handle_client_shell,
            encoding=False,  # Use binary mode for full control
            connect_maxwait=0.5,  # Reduce connection negotiation wait time
            limit=65536  # Increase buffer limit for better performance
        )

        # Keep the server running
        while self.running:
            await asyncio.sleep(1)

    async def shutdown(self):
        """Graceful shutdown of the server."""
        self.running = False

        # Stop tick scheduler
        await tick_scheduler.stop()

        # Save NPC states
        await npc_manager.save_all_states()

        # Notify all clients
        for client in list(self.clients.values()):
            await client.send("\n[System] Server is shutting down. Goodbye!\n")
            await client.disconnect()

        # Cleanup NPC manager
        npc_manager.shutdown()

        logger.info("Server shutdown complete")
        sys.exit(0)

    async def handle_client_shell(self, reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter):
        """Handle a new client connection - this is the shell function for telnetlib3.

        Args:
            reader: telnetlib3 TelnetReader for receiving data
            writer: telnetlib3 TelnetWriter for sending data
        """
        client = Client(reader, writer)
        task = asyncio.current_task()
        self.clients[task] = client

        try:
            # Set up initial telnet options
            # Tell the client we support SGA for better responsiveness
            writer.iac(telnetlib3.WILL, telnetlib3.SGA)
            await writer.drain()

            # Check connection limit
            if len(self.clients) > MAX_CONNECTIONS:
                await client.send("Server is full. Please try again later.\n")
                return

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
            logger.error(f"Error handling client {client.address}: {e}", exc_info=True)

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