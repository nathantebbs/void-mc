import asyncio
import os
import re
import json
from pathlib import Path

class PlayerEventsMonitor:
    def __init__(self, client, channel_id, log_path):
        self.client = client
        self.channel_id = channel_id
        self.log_path = Path(log_path)
        self.monitoring = False
        self.last_position = 0
        self.death_counts = {}
        self.death_counts_file = Path("discord-bot/data/death_counts.json")
        
        # Regex patterns for Minecraft log events
        self.join_pattern = re.compile(r'\[Server thread/INFO\]: (\w+) joined the game')
        self.leave_pattern = re.compile(r'\[Server thread/INFO\]: (\w+) left the game')
        
        # Death message patterns (covers most Minecraft death messages)
        self.death_patterns = [
            re.compile(r'\[Server thread/INFO\]: (\w+) (was .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (tried to .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (died .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (fell .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (drowned .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (burned .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (blew up)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (went up in flames)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (walked into .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (suffocated .+)'),
            re.compile(r'\[Server thread/INFO\]: (\w+) (withered away)'),
        ]
        
        self._load_death_counts()

    def _load_death_counts(self):
        if self.death_counts_file.exists():
            try:
                with open(self.death_counts_file, 'r') as f:
                    self.death_counts = json.load(f)
            except Exception as e:
                print(f"Error loading death counts: {e}")
                self.death_counts = {}
        else:
            self.death_counts_file.parent.mkdir(parents=True, exist_ok=True)

    def _save_death_counts(self):
        try:
            with open(self.death_counts_file, 'w') as f:
                json.dump(self.death_counts, f, indent=2)
        except Exception as e:
            print(f"Error saving death counts: {e}")

    def _increment_death_count(self, player):
        if player not in self.death_counts:
            self.death_counts[player] = 0
        self.death_counts[player] += 1
        self._save_death_counts()
        return self.death_counts[player]

    async def send_notification(self, message):
        if self.channel_id == 0:
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            print(f"Warning: Could not find channel with ID {self.channel_id}")
            return

        try:
            await channel.send(message)
        except Exception as e:
            print(f"Failed to send player event notification: {e}")

    def _process_line(self, line):
        # Check for player join
        match = self.join_pattern.search(line)
        if match:
            player = match.group(1)
            return ("join", player)

        # Check for player leave
        match = self.leave_pattern.search(line)
        if match:
            player = match.group(1)
            return ("leave", player)

        # Check for player death
        for pattern in self.death_patterns:
            match = pattern.search(line)
            if match:
                player = match.group(1)
                death_message = match.group(2)
                return ("death", player, death_message)

        return None

    async def process_new_lines(self):
        if not self.log_path.exists():
            return

        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Move to last known position
                f.seek(self.last_position)
                
                # Read new lines
                new_lines = f.readlines()
                self.last_position = f.tell()

                # Process each new line
                for line in new_lines:
                    event = self._process_line(line)
                    if event:
                        await self._handle_event(event)

        except Exception as e:
            print(f"Error processing log file: {e}")

    async def _handle_event(self, event):
        event_type = event[0]
        
        if event_type == "join":
            player = event[1]
            message = f"➡️ **{player}** joined the server"
            await self.send_notification(message)
        
        elif event_type == "leave":
            player = event[1]
            message = f"⬅️ **{player}** left the server"
            await self.send_notification(message)
        
        elif event_type == "death":
            player = event[1]
            death_message = event[2]
            death_count = self._increment_death_count(player)
            message = f"💀 **{player}** {death_message}\n*Total deaths: {death_count}*"
            await self.send_notification(message)

    async def monitor_loop(self):
        self.monitoring = True
        await self.client.wait_until_ready()

        # Initialize position at end of file if it exists
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    f.seek(0, 2)  # Seek to end
                    self.last_position = f.tell()
            except Exception as e:
                print(f"Error initializing log position: {e}")

        while self.monitoring:
            try:
                await self.process_new_lines()
                await asyncio.sleep(1)  # Check every second for new events

            except Exception as e:
                print(f"Error in player events monitor loop: {e}")
                await asyncio.sleep(1)

    def start(self):
        if not self.monitoring:
            asyncio.create_task(self.monitor_loop())

    def stop(self):
        self.monitoring = False
