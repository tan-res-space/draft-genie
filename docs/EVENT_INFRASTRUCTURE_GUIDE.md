# Event Infrastructure Guide

This guide explains how to use the event publishing and consuming infrastructure in Draft Genie.

## Table of Contents
- [Overview](#overview)
- [Python Usage](#python-usage)
- [TypeScript Usage](#typescript-usage)
- [Event Routing](#event-routing)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

Draft Genie uses RabbitMQ for event-driven communication between services. Events are published to a topic exchange and routed to service-specific queues based on routing keys.

### Architecture

```
┌─────────────┐
│   Service   │
└──────┬──────┘
       │ publish
       ▼
┌─────────────────────┐
│  EventPublisher     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ RabbitMQ Exchange   │
│ (draft-genie.events)│
└──────┬──────────────┘
       │ route by topic
       ▼
┌─────────────────────┐
│   Service Queue     │
│ (speaker.events)    │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  EventConsumer      │
└──────┬──────────────┘
       │ handle
       ▼
┌─────────────────────┐
│   Event Handler     │
└─────────────────────┘
```

---

## Python Usage

### Publishing Events

```python
from events import init_event_publisher, get_event_publisher
from domain.events import SpeakerOnboardedEvent

# Initialize publisher (once at startup)
publisher = init_event_publisher(
    rabbitmq_url="amqp://user:pass@localhost:5672/",
    exchange_name="draft-genie.events",
)
await publisher.connect()

# Create and publish event
event = SpeakerOnboardedEvent.create(
    speaker_id="123",
    external_id="ext-123",
    name="John Doe",
    bucket="GOOD",
)

# Publish with automatic routing key (uses event_type)
await publisher.publish(event)

# Or specify custom routing key
await publisher.publish(event, routing_key="speaker.onboarded")

# Publish from dictionary
await publisher.publish_dict(
    event_data={
        "event_id": "uuid",
        "event_type": "speaker.onboarded",
        "aggregate_id": "123",
        "aggregate_type": "Speaker",
        "timestamp": "2024-01-15T10:30:00Z",
        "version": 1,
        "payload": {...},
    },
    routing_key="speaker.onboarded",
)
```

### Consuming Events

```python
from events import EventConsumer

# Initialize consumer
consumer = EventConsumer(
    rabbitmq_url="amqp://user:pass@localhost:5672/",
    queue_name="speaker.events",
    prefetch_count=10,
)
await consumer.connect()

# Define event handler
async def handle_speaker_onboarded(event_data: dict) -> None:
    speaker_id = event_data["payload"]["speaker_id"]
    print(f"Speaker onboarded: {speaker_id}")
    # Process event...

# Register handler
consumer.register_handler("speaker.onboarded", handle_speaker_onboarded)

# Start consuming (blocks until stopped)
await consumer.start()

# Stop consuming
await consumer.stop()
await consumer.disconnect()
```

### Complete Example

```python
import asyncio
from events import init_event_publisher, EventConsumer
from domain.events import SpeakerOnboardedEvent

async def main():
    # Setup publisher
    publisher = init_event_publisher(
        rabbitmq_url="amqp://draftgenie:draftgenie123@localhost:5672/",
    )
    await publisher.connect()
    
    # Setup consumer
    consumer = EventConsumer(
        rabbitmq_url="amqp://draftgenie:draftgenie123@localhost:5672/",
        queue_name="speaker.events",
    )
    await consumer.connect()
    
    # Register handlers
    async def handle_event(event_data: dict):
        print(f"Received: {event_data['event_type']}")
    
    consumer.register_handler("speaker.onboarded", handle_event)
    
    # Start consumer in background
    consumer_task = asyncio.create_task(consumer.start())
    
    # Publish event
    event = SpeakerOnboardedEvent.create(
        speaker_id="123",
        external_id="ext-123",
        name="John Doe",
        bucket="GOOD",
    )
    await publisher.publish(event)
    
    # Wait a bit for processing
    await asyncio.sleep(2)
    
    # Cleanup
    await consumer.stop()
    await consumer.disconnect()
    await publisher.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## TypeScript Usage

### Publishing Events

```typescript
import { initEventPublisher, getEventPublisher } from '@draft-genie/common';

// Initialize publisher (once at startup)
const publisher = initEventPublisher({
  url: 'amqp://user:pass@localhost:5672',
  exchange: 'draft-genie.events',
});
await publisher.connect();

// Create and publish event
const event = {
  eventId: 'uuid',
  eventType: 'speaker.onboarded',
  aggregateId: '123',
  aggregateType: 'Speaker',
  timestamp: new Date().toISOString(),
  version: 1,
  correlationId: 'correlation-uuid',
  payload: {
    speaker_id: '123',
    external_id: 'ext-123',
    name: 'John Doe',
    bucket: 'GOOD',
  },
};

// Publish with automatic routing key
await publisher.publish(event);

// Or specify custom routing key
await publisher.publish(event, 'speaker.onboarded');

// Publish from plain object
await publisher.publishObject(event, 'speaker.onboarded');
```

### Consuming Events

```typescript
import { EventConsumer } from '@draft-genie/common';

// Initialize consumer
const consumer = new EventConsumer({
  url: 'amqp://user:pass@localhost:5672',
  queue: 'speaker.events',
  prefetchCount: 10,
});
await consumer.connect();

// Define event handler
async function handleSpeakerOnboarded(eventData: any): Promise<void> {
  const speakerId = eventData.payload.speaker_id;
  console.log(`Speaker onboarded: ${speakerId}`);
  // Process event...
}

// Register handler
consumer.registerHandler('speaker.onboarded', handleSpeakerOnboarded);

// Start consuming
await consumer.start();

// Stop consuming
await consumer.stop();
await consumer.disconnect();
```

### Complete Example

```typescript
import { initEventPublisher, EventConsumer } from '@draft-genie/common';

async function main() {
  // Setup publisher
  const publisher = initEventPublisher({
    url: 'amqp://draftgenie:draftgenie123@localhost:5672',
    exchange: 'draft-genie.events',
  });
  await publisher.connect();
  
  // Setup consumer
  const consumer = new EventConsumer({
    url: 'amqp://draftgenie:draftgenie123@localhost:5672',
    queue: 'speaker.events',
  });
  await consumer.connect();
  
  // Register handlers
  consumer.registerHandler('speaker.onboarded', async (eventData) => {
    console.log(`Received: ${eventData.eventType}`);
  });
  
  // Start consumer
  await consumer.start();
  
  // Publish event
  const event = {
    eventId: crypto.randomUUID(),
    eventType: 'speaker.onboarded',
    aggregateId: '123',
    aggregateType: 'Speaker',
    timestamp: new Date().toISOString(),
    version: 1,
    payload: {
      speaker_id: '123',
      external_id: 'ext-123',
      name: 'John Doe',
      bucket: 'GOOD',
    },
  };
  await publisher.publish(event);
  
  // Wait for processing
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // Cleanup
  await consumer.stop();
  await consumer.disconnect();
  await publisher.disconnect();
}

main().catch(console.error);
```

---

## Event Routing

### Routing Keys

Events are routed based on topic patterns:

| Routing Key Pattern | Queue | Description |
|---------------------|-------|-------------|
| `speaker.*` | `speaker.events` | All speaker-related events |
| `draft.*` | `draft.events` | All draft-related events |
| `rag.*` | `rag.events` | All RAG-related events |
| `evaluation.*` | `evaluation.events` | All evaluation-related events |

### Event Types

#### Speaker Events
- `speaker.onboarded` - New speaker onboarded
- `speaker.updated` - Speaker information updated
- `speaker.bucket_reassigned` - Bucket changed

#### Draft Events
- `draft.ingested` - New draft ingested
- `draft.correction_vector_created` - Correction vector created
- `draft.correction_vector_updated` - Correction vector updated

#### RAG Events
- `rag.dfn_generated` - Draft Genie Note generated

#### Evaluation Events
- `evaluation.started` - Evaluation started
- `evaluation.completed` - Evaluation completed
- `evaluation.failed` - Evaluation failed

---

## Best Practices

### 1. Use Correlation IDs
Always include correlation IDs for distributed tracing:

```python
event = SpeakerOnboardedEvent.create(
    speaker_id="123",
    external_id="ext-123",
    name="John Doe",
    bucket="GOOD",
    correlation_id=request_correlation_id,  # Pass through from request
)
```

### 2. Handle Errors Gracefully
```python
async def handle_event(event_data: dict) -> None:
    try:
        # Process event
        pass
    except Exception as e:
        logger.error("Failed to process event", error=str(e))
        # Re-raise to trigger message requeue
        raise
```

### 3. Idempotent Handlers
Make handlers idempotent to handle duplicate messages:

```python
async def handle_speaker_onboarded(event_data: dict) -> None:
    speaker_id = event_data["payload"]["speaker_id"]
    
    # Check if already processed
    if await is_already_processed(speaker_id):
        logger.info("Event already processed", speaker_id=speaker_id)
        return
    
    # Process event
    await process_speaker(speaker_id)
    
    # Mark as processed
    await mark_as_processed(speaker_id)
```

### 4. Use Health Checks
Monitor publisher and consumer health:

```python
health = await publisher.health_check()
if not health["healthy"]:
    logger.error("Publisher unhealthy", **health)
```

### 5. Graceful Shutdown
```python
import signal

async def shutdown(publisher, consumer):
    await consumer.stop()
    await consumer.disconnect()
    await publisher.disconnect()

# Register signal handlers
signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(shutdown()))
```

---

## Troubleshooting

### Connection Issues
```
Error: Failed to connect to RabbitMQ
```
**Solution**: Check RabbitMQ is running and credentials are correct:
```bash
docker-compose ps rabbitmq
docker-compose logs rabbitmq
```

### Messages Not Being Consumed
**Check**:
1. Consumer is connected and started
2. Handler is registered for the event type
3. Queue bindings are correct in RabbitMQ

**Debug**:
```bash
# Check RabbitMQ management UI
open http://localhost:15672
# Login: draftgenie / draftgenie123
```

### Message Requeue Loop
**Cause**: Handler keeps failing and message is requeued

**Solution**: Add dead letter queue or fix handler logic

### Memory Issues
**Cause**: Too many messages prefetched

**Solution**: Reduce prefetch count:
```python
consumer = EventConsumer(
    rabbitmq_url="...",
    queue_name="speaker.events",
    prefetch_count=5,  # Reduce from default 10
)
```

---

## Environment Variables

```bash
# RabbitMQ connection
RABBITMQ_URL=amqp://draftgenie:draftgenie123@localhost:5672/
RABBITMQ_EXCHANGE=draft-genie.events

# Service-specific queues
SPEAKER_QUEUE=speaker.events
DRAFT_QUEUE=draft.events
RAG_QUEUE=rag.events
EVALUATION_QUEUE=evaluation.events
```

---

## Additional Resources

- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [aio-pika Documentation](https://aio-pika.readthedocs.io/)
- [amqplib Documentation](https://amqp-node.github.io/amqplib/)
- [Event Schemas](../schemas/events/)
- [System Architecture](./system_architecture_and_implementation_plan.md)

