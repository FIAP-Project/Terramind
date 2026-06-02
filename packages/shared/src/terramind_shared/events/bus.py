"""Barramento de eventos sobre RabbitMQ (topic exchange).

Padrões:
- Exchange `terramind.events` (TOPIC, durável).
- Cada serviço declara seu próprio queue durável e binda às routing keys.
- Mensagens persistentes; consumer com prefetch=10.
- Cada mensagem leva header `x-signature` com HMAC-SHA256.

`publish` falha silenciosamente (apenas loga) se o barramento estiver
indisponível — o domínio não deve quebrar por problema transitório de infra.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

import aio_pika
from aio_pika.abc import AbstractIncomingMessage, AbstractRobustConnection

from terramind_shared.events.signing import sign_payload, verify_signature

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "terramind.events"
SIGNATURE_HEADER = "x-signature"


@dataclass(frozen=True)
class EventEnvelope:
    """Mensagem recebida pelo consumidor."""

    routing_key: str
    payload: dict[str, Any]
    raw_body: bytes


Handler = Callable[[EventEnvelope], Awaitable[None]]


class EventBus:
    def __init__(self, amqp_url: str, signing_secret: str) -> None:
        self._url = amqp_url
        self._secret = signing_secret
        self._connection: AbstractRobustConnection | None = None
        self._channel: aio_pika.abc.AbstractRobustChannel | None = None
        self._exchange: aio_pika.abc.AbstractRobustExchange | None = None

    async def connect(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()
        await self._channel.set_qos(prefetch_count=10)
        self._exchange = await self._channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("event bus connected to %s", EXCHANGE_NAME)

    async def close(self) -> None:
        if self._connection is not None:
            await self._connection.close()

    async def publish(self, routing_key: str, payload: dict[str, Any]) -> None:
        if self._exchange is None:
            logger.warning("event bus not connected; dropping event %s", routing_key)
            return
        body = json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8")
        signature = sign_payload(self._secret, body)
        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers={SIGNATURE_HEADER: signature},
        )
        try:
            await self._exchange.publish(message, routing_key=routing_key)
            logger.debug("published %s", routing_key)
        except Exception:
            logger.exception("failed to publish event %s", routing_key)

    async def subscribe(
        self,
        queue_name: str,
        routing_keys: list[str],
        handler: Handler,
    ) -> None:
        if self._channel is None or self._exchange is None:
            raise RuntimeError("event bus not connected")
        queue = await self._channel.declare_queue(queue_name, durable=True)
        for key in routing_keys:
            await queue.bind(self._exchange, routing_key=key)

        async def _on_message(msg: AbstractIncomingMessage) -> None:
            async with msg.process(requeue=False):
                body = msg.body
                signature = (msg.headers or {}).get(SIGNATURE_HEADER, "")
                if not isinstance(signature, str) or not verify_signature(
                    self._secret, body, signature
                ):
                    logger.warning("dropping unsigned/invalid event on %s", msg.routing_key)
                    return
                try:
                    payload = json.loads(body.decode("utf-8"))
                except json.JSONDecodeError:
                    logger.exception("invalid JSON on %s", msg.routing_key)
                    return
                envelope = EventEnvelope(
                    routing_key=msg.routing_key or "",
                    payload=payload,
                    raw_body=body,
                )
                try:
                    await handler(envelope)
                except Exception:
                    logger.exception("handler failed for %s", msg.routing_key)

        await queue.consume(_on_message)
        logger.info("subscribed to %s on queue %s", routing_keys, queue_name)
