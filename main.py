from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional
import time
from fastapi.responses import StreamingResponse
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import csv
import io

from database import get_db # database.py
from models import LocationMapping, PositionMapping, MigrationRun, MigrationResult # models.py

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

workday_workers = [
    {
        "worker_id": "WD-2001",
        "first_name": "Maya",
        "last_name": "Chen",
        "old_department": "Sales",
        "new_department": "Engineering",
        "location": "Salt Lake City",
        "manager_id": "WD-M1001"
    },
    {
        "worker_id": "WD-2002",
        "first_name": "Ethan",
        "last_name": "Brooks",
        "old_department": "Engineering",
        "new_department": "Sales",
        "location": "Denver",
        "manager_id": "WD-M1002"
    },
    {
        "worker_id": "WD-2003",
        "first_name": "Sofia",
        "last_name": "Ramirez",
        "old_department": "Sales",
        "new_department": "Marketing",
        "location": "Austin",
        "manager_id": "WD-M1003"
    },
    {
        "worker_id": "WD-2004",
        "first_name": "Noah",
        "last_name": "Williams",
        "old_department": "Marketing",
        "new_department": "Engineering",
        "location": "Seattle",
        "manager_id": "WD-M1004"
    },
        {
        "worker_id": "WD-2005",
        "first_name": "Retry",
        "last_name": "Success",
        "old_department": "Account Executive",
        "new_department": "Team Lead",
        "location": "Seattle",
        "manager_id": "WD-M1004"
    },
        {
        "worker_id": "WD-2006",
        "first_name": "Test",
        "last_name": "Fail 400",
        "old_department": "Engineering",
        "new_department": "Sales Engineering",
        "location": "Seattle",
        "manager_id": "WD-M1004"
    },
        {
        "worker_id": "WD-2007",
        "first_name": "Test",
        "last_name": "Fail 500",
        "old_department": "Implementation",
        "new_department": "Product",
        "location": "Seattle",
        "manager_id": "WD-M1004"
    },
]

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
    "Sales": "SAL",
    "Team Lead": "TL",
    "Sales Engineering": "FAIL",
    "Product": "FAIL",
    "Engineering": "ENG",
    "Marketing": "MKT"
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

        # Temporary failure, succeeds on retry
    if employee_id == "WD-2005" and attempt == 1:
        raise Exception("503 Service Unavailable")

    # Persistent retryable failure
    if employee_id == "WD-2006":
        raise Exception("503 Service Unavailable")

    # Non-retryable bad request
    if employee_id == "WD-2007":
        raise Exception("400 Bad Request")

    return True

learning_attempts = {}

def send_to_learning(employee: LearningUser):

    employee_id = employee.employee_id

    learning_attempts[employee_id] = learning_attempts.get(employee_id, 0) + 1
    attempt = learning_attempts[employee_id]

    # Temporary failure, succeeds on retry
    if employee_id == "WD-2005" and attempt == 1:
        raise Exception("503 Service Unavailable")

    # Persistent retryable failure
    if employee_id == "WD-2006":
        raise Exception("503 Service Unavailable")

    # Non-retryable bad request
    if employee_id == "WD-2007":
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
    "Team Lead": "Leadership Learner",
    "Sales Engineering": "FAIL",
    "Product": "FAIL"
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
# **** WORKSTREAM EMPLOYEE TRANSFER TOOL ****
# ------------------------------------------------------------------


# MOCK WORKSTREAM DATA
# Later this becomes: GET employees from Workstream API
workstream_employees = [
    {
        "employee_id": "WS-2001",
        "first_name": "Sofia",
        "last_name": "Ramirez",
        "email": "sofia.ramirez@example.com",
        "location": "Downtown SLC",
        "position": "Manager",
        "phone": "801-555-2001",
        "hire_date": "2026-07-14",
        "status": "active",
    },
    {
        "employee_id": "WS-2002",
        "first_name": "Ethan",
        "last_name": "Brooks",
        "email": "ethan.brooks@example.com",
        "location": "Airport",
        "position": "Cook",
        "phone": "801-555-2002",
        "hire_date": "2026-08-03",
        "status": "active",
    },
    {
        "employee_id": "WS-2003",
        "first_name": "Maya",
        "last_name": "Chen",
        "email": "maya.chen@example.com",
        "location": "Midvale",
        "position": "Bartender",
        "phone": None,
        "hire_date": "2026-06-21",
        "status": "active",
    },
    {
        "employee_id": "WS-2004",
        "first_name": "Noah",
        "last_name": "Williams",
        "email": "noah.williams@example.com",
        "location": "Sugarhouse",
        "position": "Server",
        "phone": "801-555-2004",
        "hire_date": "2026-05-18",
        "status": "active",
    },
    {
        "employee_id": "WS-2005",
        "first_name": "Isabella",
        "last_name": "Torres",
        "email": "isabella.torres@example.com",
        "location": "Downtown SLC",
        "position": "Server",
        "phone": "801-555-2005",
        "hire_date": "2026-04-09",
        "status": "active",
    },
    {
        "employee_id": "WS-2006",
        "first_name": "Liam",
        "last_name": "Foster",
        "email": None,  # intentionally missing required email
        "location": "Sugarhouse",
        "position": "Cook",
        "phone": "801-555-2006",
        "hire_date": "2026-08-25",
        "status": "active",
    },
    {
        "employee_id": "WS-2007",
        "first_name": "Zoe",
        "last_name": "Anderson",
        "email": "zoe.anderson@example.com",
        "location": "Downtown SLC",
        "position": "Shift Lead",  # intentionally unmapped position
        "phone": "801-555-2007",
        "hire_date": "2026-09-01",
        "status": "active",
    },
    {
        "employee_id": "WS-2008",
        "first_name": "Lucas",
        "last_name": "Bennett",
        "email": "lucas.bennett@example.com",
        "location": "Midvale",
        "position": "Server",
        "phone": None,
        "hire_date": "2025-12-11",
        "status": "inactive",
    },
    {
        "employee_id": "WS-2009",
        "first_name": "Amelia",
        "last_name": "Davis",
        "email": "amelia.davis@example.com",
        "location": "West Valley",
        "position": "Server",
        "phone": "801-555-2009",
        "hire_date": "2026-07-28",
        "status": "active",
    },
]

# MOCK TOAST DATA
# Later this becomes: GET /labor/v1/employees
toast_employees = [
    {
        "externalEmployeeId": "WS-2005",
        "email": "isabella.torres@example.com",
        "firstName": "Isabella",
        "lastName": "Torres",
    }
]


# DATA MAPPINGS
# Workstream values → Toast values
#LOCATION_MAP = {
#    "Downtown SLC": "toast-location-001",
#    "Sugarhouse": "toast-location-002",
#}

#POSITION_MAP = {
#    "Server": "toast-job-server",
#   "Cook": "toast-job-cook",
#}


# This will eventually be persisted in a database.
migration_log = []


# VALIDATION REQUIRED FIELDS
# --------------------------
REQUIRED_FIELDS = [
    "employee_id",
    "first_name",
    "last_name",
    "email",
    "location",
    "position",
]

def validate_employee(employee, db):

    errors = []

    # non-valid employees, either missing required fields AND if location/position present but non in mappings.
    for field in REQUIRED_FIELDS:
        if not employee.get(field):
            errors.append(f"Missing required field: {field}")

    #checking db table for valid location
    if employee.get("location"):

        location_mapping = (
            db.query(LocationMapping)
            .filter(
                LocationMapping.source_location == employee["location"]
            )
            .first()
        )

        if not location_mapping:
            errors.append(
                f"No Toast mapping for location: {employee['location']}"
            )
        #   if employee.get("location") and employee["location"] not in LOCATION_MAP:
        #       errors.append(
        #           f"No Toast mapping for location: {employee['location']}"
        #       )

    #checking db table for valid position
    if employee.get("position"):

        position_mapping = (
            db.query(PositionMapping)
            .filter(
                PositionMapping.source_position == employee["position"]
            )
            .first()
        )

        if not position_mapping:
            errors.append(
                f"No Toast mapping for position: {employee['position']}"
            )

            #    if employee.get("position") and employee["position"] not in POSITION_MAP:
            #        errors.append(
            #            f"No Toast mapping for position: {employee['position']}"
            #        )
    if errors:
        return False, errors

    return True, None


# DUPLICATE CHECK
# --------------------------
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
# ----------------------------
def transform_employee(employee, db):

    location_mapping = (
        db.query(LocationMapping)
        .filter(
            LocationMapping.source_location == employee["location"]
        )
        .first()
    )

    position_mapping = (
        db.query(PositionMapping)
        .filter(
            PositionMapping.source_position == employee["position"]
        )
        .first()
    )

    toast_employee = {
        "entityType": "RestaurantUser",
        "externalEmployeeId": employee["employee_id"],
        "firstName": employee["first_name"],
        "lastName": employee["last_name"],
        "email": employee["email"],
        "location": location_mapping.destination_location,
        "jobReferences": [
            {
                "guid": position_mapping.destination_position,
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
# --------------------------
def send_to_toast(employee):

    toast_employees.append(employee)

    return True


# ------------------------------------------------------------------
# ------------------ *** WORKDAY ENDPOINTS *** ---------------------
# ------------------------------------------------------------------

# PROCESS WORKDAY EMPLOYEE TRANSFER EVENT
# ----------------------
@app.post("/workday/events/worker-transfer")
def process_worker_transfer(event: WorkdayTransferEvent):

    worker = transform_workday_worker(event)

    # for payroll destination
    payroll_employee = transform_worker_to_payroll(worker)
    payroll_result = deliver_with_retry(send_to_payroll, payroll_employee)

    # for learning destination
    learning_user = transform_worker_to_learning(worker)
    learning_result = deliver_with_retry(send_to_learning, learning_user)

    payroll_log_entry = {
        "worker_id": worker.worker_id,
        "destination": "payroll",
        "status": payroll_result["status"],
        "attempts": payroll_result["attempts"],
        "error": payroll_result["error"],
        "latency_ms": payroll_result["latency_ms"],
        "timestamp": datetime.utcnow().isoformat()
    }

    integration_log.append(payroll_log_entry)

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
        "event": event,
        "worker": worker,
        "payroll": payroll_employee,
        "payroll_delivery": payroll_result,
        "learning": learning_user,
        "learning_delivery": learning_result
    }

@app.post("/workday/demo/run")
def run_workday_demo():

    results = []

    for worker in workday_workers:

        event = WorkdayTransferEvent(**worker)

        result = process_worker_transfer(event)

        results.append(result)

    return results

# VIEW WORKDAY INTEGRATION HISTORY
# ----------------------
@app.get("/workday/integrations")
def get_workday_integrations():

    return integration_log

# VIEW WORKDAY INTEGRATION SUMMARY
# ----------------------
@app.get("/workday/integrations/summary")
def get_integration_summary():

    total = len(integration_log)

    successful = sum(
        1 for entry in integration_log
        if entry["status"] == "success"
    )
    failed = sum(
        1 for entry in integration_log
        if entry["status"] == "failed"
    )
    retried = sum(
        1 for entry in integration_log
        if entry["attempts"] > 1
    )
    total_latency = sum(
        entry["latency_ms"] for entry in integration_log
    )
    average_latency = (
        round(total_latency / total, 2)
        if total > 0
        else 0
    )
    success_rate = (
        round((successful / total) * 100, 2)
        if total > 0
        else 0
    )
    failure_rate = (
        round((failed / total) * 100, 2)
        if total > 0
        else 0
    )
    return {
        "total_deliveries": total,
        "successful": successful,
        "failed": failed,
        "retried": retried,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "average_latency_ms": average_latency
    }

# RESET LOGS
# ----------------------
@app.post("/workday/demo/reset")
def clear_logs():
    integration_log.clear()
    payroll_attempts.clear()
    learning_attempts.clear()

    return {
        "status": "success",
        "message": "Workday demo data reset"
    }
# WORKDAY INT END --------------------------------------------------


# ------------------------------------------------------------------
# ------------------ *** WORKSTREAM ENDPOINTS *** ------------------
# ------------------------------------------------------------------

# MIGRATION
# ----------------------
@app.post("/workstream/migrations")
def migrate_employees(db: Session = Depends(get_db)):

    transferred = 0
    skipped = 0
    failed = 0

    run_results = []

    active_employees = [
        employee
        for employee in workstream_employees
        if employee["status"] == "active"
    ]

    # Create the overall migration run
    migration_run = MigrationRun(
        total_employees=len(active_employees)
    )

    db.add(migration_run)
    db.commit()
    db.refresh(migration_run)

    for employee in active_employees:

        employee_name = (
            f"{employee['first_name']} {employee['last_name']}"
        )

        result = {
            "employee_id": employee["employee_id"],
            "name": employee_name,
            "migration_date": datetime.utcnow().isoformat(),
        }

        # Validate employee
        valid, validation_errors = validate_employee(employee, db)

        if not valid:

            failed += 1

            reason = "; ".join(validation_errors)

            # add status and reason as keys to result dict
            result["status"] = "failed"
            result["reason"] = reason

            # migration_log.append(result)
            # run_results.append(result)

            migration_result = MigrationResult(
                migration_run_id=migration_run.id,
                employee_id=employee["employee_id"],
                employee_name=employee_name,
                status="failed",
                reason=result["reason"]
            )

            db.add(migration_result)
            run_results.append(result)

            continue

        # Duplicate check
        if employee_exists_in_toast(employee):

            skipped += 1

            result["status"] = "skipped"
            result["reason"] = "Employee already exists in Toast"

            # migration_log.append(result)
            # run_results.append(result)

            migration_result = MigrationResult(
                migration_run_id=migration_run.id,
                employee_id=employee["employee_id"],
                employee_name=employee_name,
                status="skipped",
                reason=result["reason"]
            )

            db.add(migration_result)
            run_results.append(result)

            continue

        # Transform
        toast_employee = transform_employee(employee, db)

        # Send

        try:

            send_to_toast(toast_employee)

            transferred += 1

            result["status"] = "transferred"
            result["reason"] = (
                f"Location: {employee['location']} → "
                f"{toast_employee['location']} | "
                f"Position: {employee['position']} → "
                f"{toast_employee['jobReferences'][0]['guid']}"
            )

        except Exception as error:

            failed += 1

            result["status"] = "failed"
            result["reason"] = str(error)

        # migration_log.append(result)
        # run_results.append(result)

        migration_result = MigrationResult(
            migration_run_id=migration_run.id,
            employee_id=employee["employee_id"],
            employee_name=employee_name,
            status=result["status"],
            reason=result["reason"]
        )

        db.add(migration_result)
        run_results.append(result)

    # Update the parent migration run
    migration_run.transferred_count = transferred
    migration_run.skipped_count = skipped
    migration_run.failed_count = failed
    migration_run.status = "completed"
    migration_run.completed_at = datetime.utcnow()

    db.commit()

    return {
        "migration_run_id": migration_run.id,
        "summary": {
            "transferred": transferred,
            "skipped": skipped,
            "failed": failed,
        },
        "employees": run_results,
    }
    #return {
    #    "summary": {
    #        "transferred": transferred,
    #        "skipped": skipped,
    #        "failed": failed,
    #    },
    #    "employees": run_results,
    #}


# PRE MIGRATE VALIDATION
# ----------------------
@app.get("/workstream/validation")
def validate_migration(db: Session = Depends(get_db)):
    results = []

    active_employees = [
        employee
        for employee in workstream_employees
        if employee["status"] == "active"
    ]

    for employee in active_employees:
        valid, error = validate_employee(employee, db)

        duplicate = employee_exists_in_toast(employee)

        results.append({
            "employee_id": employee["employee_id"],
            "name": f"{employee['first_name']} {employee['last_name']}",
            "valid": valid,
            "duplicate": duplicate,
            "reason": (
                error
                if not valid
                else "Employee already exists in Toast"
                if duplicate
                else None
            ),
        })

    return results


# CLIENT SEE MAPPINGS
# ----------------------
#@app.get("/workstream/mappings")
#def get_mappings():
#    return {
#       "locations": LOCATION_MAP,
#        "positions": POSITION_MAP,
#    }

# CLIENT SEE MAPPINGS IN DB
# ----------------------
@app.get("/workstream/mappings")
def get_mappings(db: Session = Depends(get_db)):

    location_rows = db.query(LocationMapping).all()
    position_rows = db.query(PositionMapping).all()

    locations = {
        row.source_location: row.destination_location
        for row in location_rows
    }

    positions = {
        row.source_position: row.destination_position
        for row in position_rows
    }

    return {
        "locations": locations,
        "positions": positions
    }
# CLIENT UPDATE LOCATION MAPPINGS
# ----------------------
#@app.post("/workstream/mappings/location")
#def update_location_mapping(workstream_location: str, toast_location: str):

#   LOCATION_MAP[workstream_location] = toast_location

#    return {
#        "message": "Location mapping updated",
#        "mapping": {
#            "workstream": workstream_location,
#            "toast": toast_location,
#        }
#    }

# CLIENT UPDATE LOCATION MAPPINGS IN DB
@app.post("/workstream/mappings/location")
def add_location_mapping(
    source_location: str,
    destination_location: str,
    db: Session = Depends(get_db)
):

    new_mapping = LocationMapping(
        source_location=source_location,
        destination_location=destination_location
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    return new_mapping

# CLIENT UPDATE POSITION MAPPINGS IN DB
# ----------------------
@app.post("/workstream/mappings/position")
def add_position_mapping(
    source_position: str,
    destination_position: str,
    db: Session = Depends(get_db)
):

    new_mapping = PositionMapping(
        source_position=source_position,
        destination_position=destination_position
    )

    db.add(new_mapping)
    db.commit()
    db.refresh(new_mapping)

    return new_mapping
# CLIENT UPDATE POSITION MAPPINGS
# ----------------------
#@app.post("/workstream/mappings/position")
#def update_position_mapping(workstream_position: str, toast_position: str):

#    POSITION_MAP[workstream_position] = toast_position

 #   return {
 #       "message": "Position mapping updated",
 #       "mapping": {
 #           "workstream": workstream_position,
 #           "toast": toast_position,
 #       }
 #   }

# VIEW MIGRATION HISTORY
# ----------------------
@app.get("/workstream/migrations")
def get_migrations(db: Session = Depends(get_db)):

    migration_runs = db.query(MigrationRun).all()

    history = []

    for run in migration_runs:

        run_data = {
            "migration_run_id": run.id,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "status": run.status,
            "total_employees": run.total_employees,
            "transferred": run.transferred_count,
            "skipped": run.skipped_count,
            "failed": run.failed_count,
            "employees": []
        }

        for employee_result in run.results:

            run_data["employees"].append({
                "employee_id": employee_result.employee_id,
                "name": employee_result.employee_name,
                "status": employee_result.status,
                "reason": employee_result.reason
            })

        history.append(run_data)

    return history
    # return migration_log

# DOWNLOAD REPORT
# ----------------------
@app.get("/workstream/migrations/{migration_run_id}/report")
def download_report(
    migration_run_id: int,
    db: Session = Depends(get_db)
):

    results = (
        db.query(MigrationResult)
        .filter(
            MigrationResult.migration_run_id == migration_run_id
        )
        .all()
    )

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

    for result in results:
        writer.writerow({
            "employee_id": result.employee_id,
            "name": result.employee_name,
            "migration_date": result.created_at,
            "status": result.status,
            "reason": result.reason,
        })

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f"attachment; filename=migration_run_{migration_run_id}.csv"
        },
    )
#def download_report():

#    output = io.StringIO()

#    writer = csv.DictWriter(
#        output,
#        fieldnames=[
#            "employee_id",
#            "name",
#            "migration_date",
#            "status",
#            "reason",
#        ],
#    )

#    writer.writeheader()

#    for record in migration_log:
#        writer.writerow(record)

#    output.seek(0)

#    return StreamingResponse(
#        iter([output.getvalue()]),
#        media_type="text/csv",
#        headers={
#            "Content-Disposition":
#                "attachment; filename=employee_migration_report.csv"
#        },
#    )
