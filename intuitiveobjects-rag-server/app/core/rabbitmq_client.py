import aio_pika
from typing import Callable, Awaitable
from app.core.config import settings

import logging

# # Set global logging level
logging.basicConfig(level=logging.INFO)

# Suppress noisy debug logs from RabbitMQ libraries
logging.getLogger("pika").setLevel(logging.WARNING)
logging.getLogger("amqp").setLevel(logging.WARNING)

class AsyncRabbitMQClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.abc.AbstractChannel | None = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.username,
                password=self.password,
            )
            self.channel = await self.connection.channel()
            print(f"✅ Connected to RabbitMQ at {self.host}:{self.port}")
        except Exception as e:
            print(f"❌ Failed to connect to RabbitMQ: {e}")
            raise e

    async def send_message(self, queue: str, message: str):
        if not self.channel:
            raise RuntimeError("Channel is not initialized. Call `connect()` first.")

        await self.channel.declare_queue(queue, durable=True)
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue,
        )

    async def consume_message(
        self,
        queue: str,
        callback: Callable[[aio_pika.IncomingMessage], Awaitable[None]],
    ):
        if not self.channel:
            raise RuntimeError("Channel is not initialized. Call `connect()` first.")

        queue_obj = await self.channel.declare_queue(queue, durable=True)
        await queue_obj.consume(callback, no_ack=False)
        print(f"🎧 Consuming messages from queue: {queue}")

    async def close(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        print(f"✅ Closed RabbitMQ connection")


rabbitmq_client = AsyncRabbitMQClient(
    host=settings.RABBITMQ_HOST,
    port=int(settings.RABBITMQ_PORT),
    username=settings.RABBITMQ_USERNAME,
    password=settings.RABBITMQ_PASSWORD,
)
