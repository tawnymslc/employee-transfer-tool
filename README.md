# Integration Platform API

FastAPI backend supporting integration-focused portfolio projects that demonstrate client implementation, data transformation, persistence, error handling, and integration observability.

The API currently powers two integration applications:

- **Client Employee Transfer Tool** — Workstream → Toast
- **Workday Integration Platform** — Workday → Payroll / Learning

---

## Backend Architecture

The backend is being organized by integration so each project can maintain its own routes, schemas, source data, and business logic while sharing the core FastAPI application and common infrastructure.

The **Workday integration has been separated into its own module**:

```text
workday/
├── __init__.py
├── data.py
├── schemas.py
├── services.py
└── routes.py
```

Responsibilities are separated across:

- `data.py` — simulated Workday source events
- `schemas.py` — Pydantic API and integration contracts
- `services.py` — transformation, delivery, retry, and integration logic
- `routes.py` — Workday FastAPI endpoints

The **Workstream integration is currently functional in its existing structure** and will be refactored next using the same modular approach.

Planned structure:

```text
workstream/
├── __init__.py
├── data.py
├── schemas.py
├── services.py
└── routes.py
```

Shared database configuration and SQLAlchemy persistence models remain at the application level.

---

## Projects

## Client Employee Transfer Tool

A client-focused integration that simulates migrating employee records from Workstream to Toast based on defined business requirements and customer-configured mappings.

### Migration Flow

**Workstream → Validation → Duplicate Check → Mapping / Transformation → Toast → PostgreSQL → Reporting**

Key functionality includes:

- Active employee filtering
- Required-field validation
- Duplicate detection using employee ID or email
- Database-backed location mappings
- Database-backed position mappings
- Workstream-to-Toast employee transformation
- Transferred, skipped, and failed result classification
- Persistent migration runs and employee results
- Migration history retrieval
- CSV report generation
- REST endpoints for managing customer mappings

### Business Validation

Employee records are evaluated before transfer.

The migration can identify conditions such as:

- Missing required employee data
- Existing employees in the destination system
- Missing location mappings
- Missing position mappings
- Inactive employees that should not be migrated

Successful records are transformed using customer-approved mappings before being sent to the simulated Toast destination.

### Persistence

Migration data and customer mappings are persisted in PostgreSQL using SQLAlchemy.

Stored data includes:

- Migration runs
- Individual migration results
- Location mappings
- Position mappings
- Migration timestamps
- Status and failure/skip reasons

This allows migration history and reporting to survive application restarts and deployments.

### Employee Transfer API

Primary endpoints include:

```text
POST /workstream/migrations
GET  /workstream/migrations
GET  /workstream/migrations/{migration_run_id}/report

GET  /workstream/mappings
POST /workstream/mappings/location
POST /workstream/mappings/position
```

---

## Workday Integration Platform

An event-driven integration that simulates processing Workday worker-transfer events and delivering transformed employee data independently to Payroll and Learning systems.

Unlike the batch-oriented employee migration workflow, each Workday request represents a single worker event moving through the integration platform.

### Integration Flow

**Workday Event → Canonical Worker Model → Destination Transformations → Delivery → Retry / Error Handling → Integration Logging**

A Workday event is first normalized into a shared worker contract. The canonical worker is then transformed into destination-specific payloads for Payroll and Learning.

Each destination is processed independently.

### Canonical Data Model

Incoming Workday data is normalized before downstream processing.

The shared worker contract includes information such as:

- Worker ID
- Employee name
- Department
- Location
- Manager ID

This separates the source-system event structure from the contracts required by downstream systems.

### Destination Transformations

The canonical worker is transformed separately for each destination.

**Payroll** receives fields such as:

- Employee ID
- Full name
- Payroll department code
- Work location

**Learning** receives fields such as:

- Employee ID
- Full name
- Department
- Location
- Manager ID
- Learning role

Department mappings translate Workday values into the values expected by each downstream system.

### Retry and Error Handling

Delivery logic distinguishes between retryable and non-retryable failures.

The demo includes scenarios for:

- Successful delivery
- Temporary failures that succeed after retry
- Persistent retryable failures
- Non-retryable failures

Retryable deliveries can be attempted up to three times before being classified as failed.

### Integration Observability

Each downstream delivery produces an integration log entry.

Logged information includes:

- Worker ID
- Destination system
- Delivery status
- Number of attempts
- Error information
- Latency
- Timestamp

The API also provides a summary of integration activity so delivery success, failures, and retries can be viewed from the frontend.

### Demo Event Runner

The Workday platform includes predefined worker-transfer events for demonstrating different integration outcomes.

The demo runner processes the events through the same single-event integration logic used by the Workday event endpoint.

This allows the frontend to demonstrate successful deliveries, retries, failures, transformations, and integration logging without requiring access to a production Workday environment.

### Workday Integration API

Primary endpoints include:

```text
POST /workday/events/worker-transfer
POST /workday/demo/run
POST /workday/demo/reset

GET  /workday/integrations
GET  /workday/integrations/summary
```

---

## Technology

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- REST APIs
- Render

---

## Portfolio Environment

This project is designed as an integration engineering and solution design portfolio environment.

External systems such as Workstream, Toast, Workday, Payroll, and Learning are simulated for demonstration purposes. The project does not connect to production customer systems or use production customer credentials.

The focus is on demonstrating integration patterns and engineering decisions including:

- Business requirement translation
- API design
- Data validation
- Data mapping and transformation
- Canonical data models
- Batch and event-driven integration patterns
- Persistence
- Retry and error handling
- Reporting
- Integration observability