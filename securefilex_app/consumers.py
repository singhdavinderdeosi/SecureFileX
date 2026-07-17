import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("live_logs", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("live_logs", self.channel_name)

    async def receive(self, text_data):
        # Echo test
        await self.send(text_data=json.dumps({"message": "🔁 Echo: " + text_data}))

    async def send_log(self, event):
        await self.send(text_data=json.dumps(event["log"]))
