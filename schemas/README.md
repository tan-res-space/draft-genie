# Draft Genie Schemas

This directory contains schema definitions for the Draft Genie application.

## Directory Structure

```
schemas/
├── openapi/          # OpenAPI 3.0 specifications for REST APIs
│   ├── common.yaml   # Common schemas and components
│   └── speaker-service.yaml  # Speaker Service API
└── events/           # JSON Schema definitions for domain events
    ├── domain-event.schema.json  # Base domain event schema
    ├── speaker-events.schema.json  # Speaker-related events
    ├── draft-events.schema.json  # Draft-related events
    └── evaluation-events.schema.json  # Evaluation-related events
```

## OpenAPI Schemas

OpenAPI schemas define the REST API contracts for each service. They include:

- Request/response models
- Validation rules
- Error responses
- Authentication requirements
- API documentation

### Usage

OpenAPI schemas can be used to:

1. **Generate API documentation** - Use tools like Swagger UI or Redoc
2. **Validate requests/responses** - Use OpenAPI validators in your code
3. **Generate client SDKs** - Use OpenAPI generators
4. **Contract testing** - Ensure API compatibility

### Example

```yaml
# Reference common schemas
$ref: './common.yaml#/components/schemas/UUID'
```

## Event Schemas

Event schemas define the structure of domain events published to RabbitMQ. They use JSON Schema format for validation.

### Event Types

#### Speaker Events
- `speaker.onboarded` - New speaker onboarded
- `speaker.updated` - Speaker information updated
- `speaker.bucket_reassigned` - Speaker moved to different quality bucket

#### Draft Events
- `draft.ingested` - New draft ingested
- `draft.correction_vector_created` - Correction vector created
- `draft.correction_vector_updated` - Correction vector updated

#### Evaluation Events
- `evaluation.started` - Evaluation process started
- `evaluation.completed` - Evaluation completed successfully
- `evaluation.failed` - Evaluation failed

### Event Routing

Events are published to the `draft-genie.events` exchange with topic routing:

- `speaker.*` → `speaker.events` queue
- `draft.*` → `draft.events` queue
- `rag.*` → `rag.events` queue
- `evaluation.*` → `evaluation.events` queue

### Usage

Event schemas can be used to:

1. **Validate events** - Before publishing or after consuming
2. **Generate types** - Use JSON Schema to TypeScript/Python converters
3. **Documentation** - Understand event structure and requirements
4. **Contract testing** - Ensure event compatibility between services

### Example

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$ref": "domain-event.schema.json"
}
```

## Schema Validation

### Python

```python
import json
import jsonschema

# Load schema
with open('schemas/events/speaker-events.schema.json') as f:
    schema = json.load(f)

# Validate event
jsonschema.validate(event_data, schema)
```

### TypeScript

```typescript
import Ajv from 'ajv';
import schema from './schemas/events/speaker-events.schema.json';

const ajv = new Ajv();
const validate = ajv.compile(schema);

if (!validate(eventData)) {
  console.error(validate.errors);
}
```

## Best Practices

1. **Version your schemas** - Use semantic versioning
2. **Backward compatibility** - Don't break existing consumers
3. **Document changes** - Keep a changelog
4. **Validate early** - Validate at the source before publishing
5. **Use references** - DRY principle with `$ref`
6. **Test schemas** - Write tests for schema validation

## Tools

- **OpenAPI**: Swagger UI, Redoc, OpenAPI Generator
- **JSON Schema**: ajv (JS), jsonschema (Python)
- **Validation**: express-openapi-validator, fastapi-openapi-validator
- **Documentation**: Swagger UI, Redoc, Stoplight

## Contributing

When adding new schemas:

1. Follow existing naming conventions
2. Add proper descriptions and examples
3. Use references for common types
4. Update this README
5. Test schema validation

