# Integration Platform API

This repository contains backend services for two integration projects built with FastAPI.

## Projects

### Workstream Employee Transfer Tool

Simulates migrating employee data from Workstream to Toast.

Key functionality includes:
- Employee validation
- Duplicate detection
- Workstream-to-Toast data transformation
- Migration logging
- CSV report generation

### Workday Integration Platform

Simulates Workday worker transfer events flowing through an integration layer to downstream Payroll and Learning systems.

Key functionality includes:
- Canonical worker data model
- Destination-specific transformations
- Payroll and Learning delivery
- Retryable and non-retryable error handling
- Integration logging
- Success, failure, retry, and latency metrics
- Demo reset endpoint for repeatable testing

## Technology

- Python
- FastAPI
- Pydantic
- REST APIs
- React frontend