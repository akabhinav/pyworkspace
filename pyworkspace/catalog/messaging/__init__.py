"""Messaging service catalog — auto-imports all messaging service definitions."""

from __future__ import annotations

from pyworkspace.catalog.messaging.kafka import KafkaService
from pyworkspace.catalog.messaging.nats import NATSService
from pyworkspace.catalog.messaging.rabbitmq import RabbitMQService

__all__ = [
    "KafkaService",
    "NATSService",
    "RabbitMQService",
]
