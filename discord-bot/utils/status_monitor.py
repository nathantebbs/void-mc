import asyncio
from utils.mc import get_server_status

class ServerStatusMonitor:
    def __init__(self, client, channel_id, check_interval=30):
        self.client = client
        self.channel_id = channel_id
        self.check_interval = check_interval
        self.is_online = None
        self.monitoring = False

    def _check_server_online(self):
        try:
            get_server_status()
            return True
        except Exception:
            return False

    async def send_notification(self, is_online):
        if self.channel_id == 0:
            return

        channel = self.client.get_channel(self.channel_id)
        if not channel:
            print(f"Warning: Could not find channel with ID {self.channel_id}")
            return

        if is_online:
            message = "@everyone 🟢 **void-mc server is now ONLINE!**"
        else:
            message = "@everyone 🔴 **void-mc server is now OFFLINE.**"

        try:
            await channel.send(message)
        except Exception as e:
            print(f"Failed to send status notification: {e}")

    async def monitor_loop(self):
        self.monitoring = True
        await self.client.wait_until_ready()

        while self.monitoring:
            try:
                current_status = self._check_server_online()

                if self.is_online is None:
                    self.is_online = current_status
                elif self.is_online != current_status:
                    self.is_online = current_status
                    await self.send_notification(current_status)

                await asyncio.sleep(self.check_interval)

            except Exception as e:
                print(f"Error in status monitor loop: {e}")
                await asyncio.sleep(self.check_interval)

    def start(self):
        if not self.monitoring:
            asyncio.create_task(self.monitor_loop())

    def stop(self):
        self.monitoring = False
