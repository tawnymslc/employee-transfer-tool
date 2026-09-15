# Integration Platform API

FastAPI backend supporting integration-focused portfolio projects that demonstrate client implementation, data transformation, persistence, error handling, and integration observability.

The API currently powers two integration applications:

- Client Employee Transfer Tool — Workstream → Toast
- Workday Integration Platform — Workday → Payroll / Learning

---

## Projects

### Client Employee Transfer Tool

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