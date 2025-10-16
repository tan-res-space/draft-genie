# DraftGinie Service Details

This document provides the necessary details for integrating with the Azure-deployed service.

- **API Base URL**: The API Base URL is dynamically generated during deployment. It follows the pattern `https://api-gateway.<environment-specific-hash>.southindia.azurecontainerapps.io`. You can retrieve the exact URL by running the following Azure CLI command:
  ```bash
  az containerapp show --name api-gateway --resource-group draftgenie-rg --query properties.configuration.ingress.fqdn -o tsv
  ```

- **Endpoint paths**:
  - `/api/v1/health`: Health check for the API Gateway.
  - `/api/v1/health/services`: Health check for all backend services.

  ### Speaker Service Endpoints (`/api/v1/speakers`)
  - `GET /`: List all speakers.
  - `POST /`: Create a new speaker.
  - `GET /{speaker_id}`: Get a specific speaker by ID.
  - `PUT /{speaker_id}`: Update a speaker's details.
  - `DELETE /{speaker_id}`: Delete a speaker.
  - `GET /{speaker_id}/profile`: Get a speaker's profile.
  - `PUT /{speaker_id}/profile`: Update a speaker's profile.

  ### Draft Service Endpoints (`/api/v1/drafts`)
  - `POST /ingest`: Trigger draft ingestion for a speaker.
  - `POST /`: Create a single draft.
  - `GET /`: List all drafts.
  - `GET /{draft_id}`: Get a specific draft by ID.
  - `GET /speaker/{speaker_id}`: Get all drafts for a speaker.
  - `DELETE /{draft_id}`: Delete a draft.

  ### Vector Service Endpoints (`/api/v1/vectors`)
  - `POST /generate`: Generate a correction vector for a draft.
  - `POST /generate/speaker/{speaker_id}`: Generate vectors for a speaker's drafts.
  - `GET /{vector_id}`: Get a specific correction vector by ID.
  - `GET /speaker/{speaker_id}`: Get all correction vectors for a speaker.
  - `GET /speaker/{speaker_id}/statistics`: Get statistics for a speaker's vectors.
  - `POST /search`: Search for similar correction vectors.

  ### RAG Service Endpoints (`/api/v1/rag`)
  - `POST /generate`: Generate a DFN from an IFN using the RAG pipeline.
  - `GET /sessions/{session_id}`: Get RAG session details.
  - `GET /sessions/speaker/{speaker_id}`: Get all RAG sessions for a speaker.

  ### Evaluation Service Endpoints (`/api/v1/evaluations`)
  - `POST /trigger`: Manually trigger an evaluation for a DFN.
  - `GET /`: Get a list of evaluations.
  - `GET /{evaluation_id}`: Get a specific evaluation by ID.

- **Documentation or OpenAPI (Swagger) file**:
  - The OpenAPI documentation is available at the `/api/docs` endpoint. For example: `https://<your-api-base-url>/api/docs`

- **Authentication method**:
  - The authentication method is **Bearer Token (JWT)**. The API gateway uses a JWT-based strategy that extracts the token from the `Authorization` header as a bearer token.

- **Any required request headers**:
  - `Content-Type: application/json` for POST/PUT requests.
  - `Authorization: Bearer <your-jwt-token>` for authenticated endpoints.

- **Example request/response payloads**:
  - These would be specific to your application's endpoints. You can find detailed models and examples in the OpenAPI documentation at `/api/docs`.
  - Below is a simple example for the health check endpoint.

  **Health Check Example**

  - **Request**:
    ```http
    GET /api/v1/health HTTP/1.1
    Host: <your-api-base-url>
    ```

  - **Response**:
    ```json
    {
      "status": "ok",
      "info": {
        "api-gateway": {
          "status": "up"
        }
      },
      "error": {},
      "details": {
        "api-gateway": {
          "status": "up"
        }
      }
    }
    ```