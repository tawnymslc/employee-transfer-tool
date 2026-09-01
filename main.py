from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import time
from fastapi.responses import StreamingResponse
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import csv
import io

app = FastAPI(
    title="Integration Platform API",
    description="Backend services for enterprise integration and migration projects."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # local
        "https://tawny-mathi.com",   # production
        "https://www.tawny-mathi.com" 
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# **** WORKDAY INTEGRATION ***
# ------------------------------------------------------------------


# Defines the expected data contract for employee transfer events received from Workday
# ------------------------------------------------------------------
class WorkdayTransferEvent(BaseModel):
    worker_id: str
    first_name: str
    last_name: str
    old_department: str
    new_department: str
    location: str
    manager_id: Optional[str] = None


# WORKDAY CANONICAL WORKER MODEL
# Normalizes Workday-specific data into a shared internal contract
# ------------------------------------------------------------------
class WorkerContract(BaseModel):
    worker_id: str
    full_name: str
    department: str
    location: str
    manager_id: Optional[str] = None


# PAYROLL DESTINATION CONTRACT
# Defines the data format expected by the downstream payroll system
# ------------------------------------------------------------------
class PayrollEmployee(BaseModel):
    employee_id: str
    full_name: str
    department_code: str
    work_location: str


# LEARNING DESTINATION CONTRACT
# Defines the data format expected by the downstream learning system
# ------------------------------------------------------------------
class LearningUser(BaseModel):
    employee_id: str
    full_name: str
    department: str
    location: str
    manager_id: Optional[str] = None
    learning_role: str

# WORKDAY/CANONICAL VALUES → PAYROLL VALUES
# Using department in to form department code for payroll system
PAYROLL_DEPARTMENT_MAP = {
    "Engineering": "ENG",
    "Sales": "SAL",
    "Marketing": "MKT",
}

# TRANSFORM WORKDAY EVENT → CANONICAL WORKER CONTRACT
# ------------------------------------------------------------------
def transform_workday_worker(event: WorkdayTransferEvent):

    return WorkerContract(

        worker_id=event.worker_id,
        full_name=f"{event.first_name} {event.last_name}",
        department=event.new_department,
        location=event.location,
        manager_id=event.manager_id
    )


# TRANSFORM CANONICAL WORKER → PAYROLL CONTRACT
# ------------------------------------------------------------------
def transform_worker_to_payroll(worker: WorkerContract):

    return PayrollEmployee(
        employee_id=worker.worker_id,
        full_name=worker.full_name,
        department_code=PAYROLL_DEPARTMENT_MAP[worker.department],
        work_location=worker.location
    )

# Tracks how many times each employee has been sent to Payroll
payroll_attempts = {}

# MOCK SEND TO PAYROLL
# Simulates sending transformed employee data to a downstream system
# ------------------------------------------------------------------
def send_to_payroll(employee: PayrollEmployee):

    employee_id = employee.employee_id

    # Increase the attempt count for this employee
    payroll_attempts[employee_id] = payroll_attempts.get(employee_id, 0) + 1
    attempt = payroll_attempts[employee_id]

    # Simulates a temporary failure that succeeds on retry
    if employee_id == "WD-1002" and attempt == 1:
        raise Exception("503 Service Unavailable")

    # Simulates a persistent failure
    if employee_id == "WD-1003":
        raise Exception("503 Service Unavailable")

    # Bad request: do NOT retry
    if employee_id == "WD-1004":
        raise Exception("400 Bad Request")

    return True

learning_attempts = {}

def send_to_learning(employee: LearningUser):

    employee_id = employee.employee_id

    learning_attempts[employee_id] = learning_attempts.get(employee_id, 0) + 1
    attempt = learning_attempts[employee_id]

    print("LEARNING:", employee_id, "ATTEMPT:", attempt)

    # Temporary failure, succeeds on retry
    if employee_id == "WD-2002" and attempt == 1:
        raise Exception("503 Service Unavailable")

    # Persistent retryable failure
    if employee_id == "WD-2003":
        raise Exception("503 Service Unavailable")

    # Non-retryable bad request
    if employee_id == "WD-2004":
        raise Exception("400 Bad Request")

    return True


# RETRY PAYROLL/LEARNING
# Attempts delivery up to 3 times before marking it as failed
# ------------------------------------------------------------------
def deliver_with_retry(send_function, employee):

    max_attempts = 3
    attempts = 0

    start_time = time.perf_counter()

    while attempts < max_attempts:
        attempts += 1

        try:
            send_function(employee)

            latency_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2
            )

            return {
                "status": "success",
                "attempts": attempts,
                "error": None,
                "latency_ms": latency_ms
            }
        
        except Exception as error:

            error_message = str(error)

            # Non-retryable error
            if "400" in error_message:
                latency_ms = round(
                    (time.perf_counter() - start_time) * 1000, 2)

                return {
                    "status": "failed",
                    "attempts": attempts,
                    "error": error_message,
                    "latency_ms": latency_ms
                }

            if attempts == max_attempts:

                latency_ms = round(
                    (time.perf_counter() - start_time) * 1000, 2) 

                return {
                    "status": "failed",
                    "attempts": attempts,
                    "error": error_message,
                    "latency_ms": latency_ms
                }

# CANONICAL VALUES → LEARNING VALUES
# ------------------------------------------------------------------
LEARNING_ROLE_MAP = {
    "Engineering": "Technical Learner",
    "Sales": "Sales Learner",
    "Marketing": "Marketing Learner",
}

# TRANSFORM CANONICAL WORKER → LEARNING CONTRACT
# ------------------------------------------------------------------
def transform_worker_to_learning(worker: WorkerContract):

    return LearningUser(
        employee_id=worker.worker_id,
        full_name=worker.full_name,
        department=worker.department,
        location=worker.location,
        manager_id=worker.manager_id,
        learning_role=LEARNING_ROLE_MAP[worker.department]
    )

# Stores delivery results for observability and troubleshooting / future database integration
integration_log = []


# ------------------------------------------------------------------
# **** WORKSTREAM EMPLOYEE TRANSFER TOOL INTEGRATION ****
# ------------------------------------------------------------------

# MOCK WORKSTREAM DATA
# Later this becomes: GET employees from Workstream API
workstream_employees = [
    {
        "employee_id": "WS-1001",
        "first_name": "Maria",
        "last_name": "Lopez",
        "email": "maria@example.com",
        "location": "Downtown SLC",
        "position": "Server",
        "phone": "801-555-1001",
        "hire_date": "2025-05-01",
        "status": "active",
    },
    {
        "employee_id": "WS-1002",
        "first_name": "James",
        "last_name": "Smith",
        "email": "james@example.com",
        "location": "Sugarhouse",
        "position": "Cook",
        "phone": None,
        "hire_date": "2026-01-15",
        "status": "active",
    },
    {
        "employee_id": "WS-1003",
        "first_name": "Emily",
        "last_name": "Jones",
        "email": None,  # intentionally missing required data
        "location": "Downtown SLC",
        "position": "Server",
        "phone": "801-555-1003",
        "hire_date": None,
        "status": "active",
    },
    {
        "employee_id": "WS-1004",
        "first_name": "Carlos",
        "last_name": "Martinez",
        "email": "carlos@example.com",
        "location": "Downtown SLC",
        "position": "Server",
        "phone": None,
        "hire_date": None,
        "status": "inactive",
    },
]



# MOCK TOAST DATA
# Later this becomes: GET /labor/v1/employees
toast_employees = [
    {
        "externalEmployeeId": "WS-1002",
        "email": "james@example.com",
        "firstName": "James",
        "lastName": "Smith",
    }
]


# DATA MAPPINGS
# Workstream values → Toast values
LOCATION_MAP = {
    "Downtown SLC": "toast-location-001",
    "Sugarhouse": "toast-location-002",
}

POSITION_MAP = {
    "Server": "toast-job-server",
    "Cook": "toast-job-cook",
}


# This will eventually be persisted in a database.
migration_log = []


# ---------------------------VALIDATION---------------------------------------
REQUIRED_FIELDS = [
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "location",
    "position",
]

def validate_employee(employee):

    missing_fields = []

    for field in REQUIRED_FIELDS:
        if not employee.get(field):
            missing_fields.append(field)

    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"

    if employee["location"] not in LOCATION_MAP:
        return False, f"No Toast mapping for location: {employee['location']}"

    if employee["position"] not in POSITION_MAP:
        return False, f"No Toast mapping for position: {employee['position']}"

    return True, None


# DUPLICATE CHECK
def employee_exists_in_toast(employee):

    for toast_employee in toast_employees:

        same_id = (
            toast_employee.get("externalEmployeeId")
            == employee["employee_id"]
        )

        same_email = (
            toast_employee.get("email")
            == employee["email"]
        )

        if same_id or same_email:
            return True

    return False


# TRANSFORM WORKSTREAM → TOAST
def transform_employee(employee):

    toast_employee = {
        "entityType": "RestaurantUser",
        "externalEmployeeId": employee["employee_id"],
        "firstName": employee["first_name"],
        "lastName": employee["last_name"],
        "email": employee["email"],
        "location": LOCATION_MAP[employee["location"]],
        "jobReferences": [
            {
                "guid": POSITION_MAP[employee["position"]],
                "entityType": "RestaurantJob",
            }
        ],
    }

    # OPTIONAL DATA

    if employee.get("phone"):
        toast_employee["phoneNumber"] = employee["phone"]

    if employee.get("hire_date"):
        toast_employee["hireDate"] = employee["hire_date"]

    return toast_employee


# MOCK SEND TO TOAST
# Eventually becomes POST /labor/v1/employees

def send_to_toast(employee):

    toast_employees.append(employee)

    return True


#****ENDPOINTS****#

# ------------------WORKSTREAM ENDPOINTS-------------------

# MIGRATION
# ------------------------------------------------------------------
@app.post("/migrate")
def migrate_employees():

    transferred = 0
    skipped = 0
    failed = 0

    run_results = []

    active_employees = [
        employee
        for employee in workstream_employees
        if employee["status"] == "active"
    ]

    for employee in active_employees:

        result = {
            "employee_id": employee["employee_id"],
            "name": f"{employee['first_name']} {employee['last_name']}",
            "migration_date": datetime.utcnow().isoformat(),
        }

        # Validate employee

        valid, error = validate_employee(employee)

        if not valid:

            failed += 1

            result["status"] = "failed"
            result["reason"] = error

            migration_log.append(result)
            run_results.append(result)

            continue

        # Duplicate check

        if employee_exists_in_toast(employee):

            skipped += 1

            result["status"] = "skipped"
            result["reason"] = "Employee already exists in Toast"

            migration_log.append(result)
            run_results.append(result)

            continue

        # Transform

        toast_employee = transform_employee(employee)

        # Send

        try:

            send_to_toast(toast_employee)

            transferred += 1

            result["status"] = "transferred"
            result["reason"] = None

        except Exception as error:

            failed += 1

            result["status"] = "failed"
            result["reason"] = str(error)

        migration_log.append(result)
        run_results.append(result)

    return {
        "summary": {
            "transferred": transferred,
            "skipped": skipped,
            "failed": failed,
        },
        "employees": run_results,
    }



# VIEW MIGRATION HISTORY
# ------------------------------------------------------------------
@app.get("/migrations")
def get_migrations():

    return migration_log



# DOWNLOAD REPORT
# ------------------------------------------------------------------
@app.get("/report")
def download_report():

    output = io.StringIO()

    writer = csv.DictWriter(
        output,
        fieldnames=[
            "employee_id",
            "name",
            "migration_date",
            "status",
            "reason",
        ],
    )

    writer.writeheader()

    for record in migration_log:
        writer.writerow(record)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=employee_migration_report.csv"
        },
    )



# ------------------WORKDAY ENDPOINTS-------------------


# ------------------------------------------------------------------
# PROCESS WORKDAY EMPLOYEE TRANSFER EVENT
# ------------------------------------------------------------------

@app.post("/workday/events/worker-transfer")
def process_worker_transfer(event: WorkdayTransferEvent):

    worker = transform_workday_worker(event)

    # for payroll destination
    payroll_employee = transform_worker_to_payroll(worker)
    payroll_result = deliver_with_retry(send_to_payroll, payroll_employee)

    # for learning destination
    learning_user = transform_worker_to_learning(worker)
    print("ABOUT TO CALL LEARNING")
    learning_result = deliver_with_retry(send_to_learning, learning_user)

    log_entry = {
        "worker_id": worker.worker_id,
        "destination": "payroll",
        "status": payroll_result["status"],
        "attempts": payroll_result["attempts"],
        "error": payroll_result["error"],
        "latency_ms": payroll_result["latency_ms"],
        "timestamp": datetime.utcnow().isoformat()
    }

    integration_log.append(log_entry)

    learning_log_entry = {
        "worker_id": worker.worker_id,
        "destination": "learning",
        "status": learning_result["status"],
        "attempts": learning_result["attempts"],
        "error": learning_result["error"],
        "latency_ms": learning_result["latency_ms"],
        "timestamp": datetime.utcnow().isoformat()

    }

    integration_log.append(learning_log_entry)

    return {
        "worker": worker,
        "payroll": payroll_employee,
        "payroll_delivery": payroll_result,
        "learning": learning_user,
        "learning_delivery": learning_result
    }

# ------------------------------------------------------------------
# VIEW WORKDAY INTEGRATION HISTORY
# ------------------------------------------------------------------

@app.get("/workday/integrations")
def get_workday_integrations():

    return integration_log