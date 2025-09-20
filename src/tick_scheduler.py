"""Tick scheduler module for SAMUD - manages timed events and NPC movements."""

import asyncio
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Represents a scheduled task in the tick system."""

    id: str
    callback: Callable
    interval: float  # seconds between ticks
    last_run: datetime = field(default_factory=datetime.now)
    enabled: bool = True
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    def should_run(self) -> bool:
        """Check if this task should run now."""
        if not self.enabled:
            return False
        elapsed = (datetime.now() - self.last_run).total_seconds()
        return elapsed >= self.interval

    async def run(self):
        """Execute the task."""
        try:
            self.last_run = datetime.now()
            if asyncio.iscoroutinefunction(self.callback):
                await self.callback(*self.args, **self.kwargs)
            else:
                self.callback(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(f"Error in scheduled task {self.id}: {e}")


class TimeOfDay:
    """Manages time-of-day calculations for the game world."""

    @staticmethod
    def get_period(current_time: Optional[datetime] = None) -> str:
        """Get the current time period.

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            Time period: 'morning', 'afternoon', 'evening', or 'night'
        """
        if current_time is None:
            current_time = datetime.now()

        hour = current_time.hour

        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        elif 18 <= hour < 24:
            return 'evening'
        else:  # 0-6
            return 'night'

    @staticmethod
    def get_next_period_change() -> float:
        """Get seconds until the next time period change.

        Returns:
            Seconds until next period change
        """
        now = datetime.now()
        hour = now.hour

        # Find next period boundary
        if hour < 6:
            next_hour = 6
        elif hour < 12:
            next_hour = 12
        elif hour < 18:
            next_hour = 18
        else:
            next_hour = 0  # Next day

        # Calculate time until next boundary
        if next_hour == 0:
            # Tomorrow at midnight
            next_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_time = next_time.replace(day=next_time.day + 1)
        else:
            next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)

        if next_time <= now:
            # Already past, add a day
            next_time = next_time.replace(day=next_time.day + 1)

        return (next_time - now).total_seconds()


class TickScheduler:
    """Manages scheduled tasks and NPC movements."""

    def __init__(self, tick_interval: float = 1.0):
        """Initialize the tick scheduler.

        Args:
            tick_interval: Base tick interval in seconds
        """
        self.tick_interval = tick_interval
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.tick_task: Optional[asyncio.Task] = None
        self.current_period = TimeOfDay.get_period()
        self.tick_count = 0

        logger.info(f"TickScheduler initialized with {tick_interval}s interval")

    def register_task(self, task_id: str, callback: Callable, interval: float,
                      *args, **kwargs) -> bool:
        """Register a new scheduled task.

        Args:
            task_id: Unique identifier for the task
            callback: Function to call on tick
            interval: Seconds between executions
            *args: Positional arguments for callback
            **kwargs: Keyword arguments for callback

        Returns:
            True if task was registered successfully
        """
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already registered")
            return False

        task = ScheduledTask(
            id=task_id,
            callback=callback,
            interval=interval,
            args=args,
            kwargs=kwargs
        )

        self.tasks[task_id] = task
        logger.debug(f"Registered task {task_id} with {interval}s interval")
        return True

    def unregister_task(self, task_id: str) -> bool:
        """Remove a scheduled task.

        Args:
            task_id: Task to remove

        Returns:
            True if task was removed
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.debug(f"Unregistered task {task_id}")
            return True
        return False

    def enable_task(self, task_id: str) -> bool:
        """Enable a scheduled task.

        Args:
            task_id: Task to enable

        Returns:
            True if task was enabled
        """
        if task_id in self.tasks:
            self.tasks[task_id].enabled = True
            return True
        return False

    def disable_task(self, task_id: str) -> bool:
        """Disable a scheduled task.

        Args:
            task_id: Task to disable

        Returns:
            True if task was disabled
        """
        if task_id in self.tasks:
            self.tasks[task_id].enabled = False
            return True
        return False

    async def register_npc_movement(self, npc_id: str, tick_interval: float):
        """Register an NPC for movement ticks.

        Args:
            npc_id: NPC to register
            tick_interval: Seconds between movement checks
        """
        from npcs import npc_manager

        async def check_npc_movement():
            """Check if NPC should move."""
            npc = npc_manager.get_npc(npc_id)
            if not npc:
                self.unregister_task(f"npc_move_{npc_id}")
                return

            # Check if NPC wants to move
            next_room = npc.get_next_room(datetime.now())
            if next_room and next_room != npc.current_room:
                # Check if players are interacting
                if not npc_manager.check_player_interaction(npc_id, npc.current_room):
                    await npc_manager.move_npc(npc_id, next_room)

        self.register_task(
            f"npc_move_{npc_id}",
            check_npc_movement,
            tick_interval
        )

    async def register_npc_ambient(self, npc_id: str, min_interval: float = 30.0):
        """Register an NPC for ambient actions.

        Args:
            npc_id: NPC to register
            min_interval: Minimum seconds between ambient actions
        """
        from npcs import npc_manager
        from broadcast import broadcast_manager
        from player import player_manager

        async def perform_ambient_action():
            """Perform an ambient action if conditions are met."""
            npc = npc_manager.get_npc(npc_id)
            if not npc or not npc.current_room:
                self.unregister_task(f"npc_ambient_{npc_id}")
                return

            # Only perform actions if players are present
            players = player_manager.get_players_in_room(npc.current_room)
            if not players:
                return

            # Pass player count for contextual actions
            action = npc.get_ambient_action(player_count=len(players))
            if action:
                await broadcast_manager.broadcast_to_room(
                    npc.current_room, action, is_system=False
                )

        # Add some randomness to ambient action timing
        import random
        interval = min_interval + random.uniform(0, min_interval)

        self.register_task(
            f"npc_ambient_{npc_id}",
            perform_ambient_action,
            interval
        )

    async def _tick_loop(self):
        """Main tick loop."""
        logger.info("Tick scheduler started")

        while self.running:
            try:
                self.tick_count += 1

                # Check for time period changes
                new_period = TimeOfDay.get_period()
                if new_period != self.current_period:
                    old_period = self.current_period
                    self.current_period = new_period
                    logger.info(f"Time period changed: {old_period} -> {new_period}")

                    # Notify NPCs of time change
                    await self._notify_time_change(new_period)

                # Run scheduled tasks
                tasks_to_run = []
                for task in self.tasks.values():
                    if task.should_run():
                        tasks_to_run.append(task.run())

                if tasks_to_run:
                    await asyncio.gather(*tasks_to_run, return_exceptions=True)

                # Wait for next tick
                await asyncio.sleep(self.tick_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in tick loop: {e}")
                await asyncio.sleep(self.tick_interval)

        logger.info("Tick scheduler stopped")

    async def _notify_time_change(self, new_period: str):
        """Notify all NPCs of a time period change.

        Args:
            new_period: The new time period
        """
        from npcs import npc_manager

        # NPCs may want to move based on schedule
        for npc_id in list(npc_manager.npcs.keys()):
            npc = npc_manager.get_npc(npc_id)
            if npc and npc.movement and 'schedule' in npc.movement:
                # Check if NPC should be somewhere else this period
                schedule = npc.movement['schedule']
                if new_period in schedule:
                    target_room = schedule[new_period]
                    if target_room != npc.current_room:
                        # Schedule immediate movement check
                        if f"npc_move_{npc_id}" in self.tasks:
                            self.tasks[f"npc_move_{npc_id}"].last_run = datetime.min

    async def start(self):
        """Start the tick scheduler."""
        if self.running:
            logger.warning("Tick scheduler already running")
            return

        self.running = True
        self.tick_task = asyncio.create_task(self._tick_loop())
        logger.info("Tick scheduler started")

    async def stop(self):
        """Stop the tick scheduler."""
        if not self.running:
            return

        self.running = False

        if self.tick_task:
            self.tick_task.cancel()
            try:
                await self.tick_task
            except asyncio.CancelledError:
                pass
            self.tick_task = None

        logger.info("Tick scheduler stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status information.

        Returns:
            Status dictionary
        """
        return {
            'running': self.running,
            'tick_count': self.tick_count,
            'current_period': self.current_period,
            'task_count': len(self.tasks),
            'active_tasks': sum(1 for t in self.tasks.values() if t.enabled),
            'tasks': {
                task_id: {
                    'enabled': task.enabled,
                    'interval': task.interval,
                    'last_run': task.last_run.isoformat()
                }
                for task_id, task in self.tasks.items()
            }
        }


# Singleton instance
tick_scheduler = TickScheduler()