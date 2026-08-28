from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from datetime import datetime
import csv
import io

app = FastAPI(title="Workstream → Toast Employee Transfer")


# ------------------------------------------------------------------
# MOCK WORKSTREAM DATA
# Later this becomes: GET employees from Workstream API
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# MOCK TOAST DATA
# Later this becomes: GET /labor/v1/employees
# ------------------------------------------------------------------

toast_employees = [
    {
        "externalEmployeeId": "WS-1002",
        "email": "james@example.com",
        "firstName": "James",
        "lastName": "Smith",
    }
]


# ------------------------------------------------------------------
# DATA MAPPINGS
# Workstream values → Toast values
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# DUPLICATE CHECK
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# TRANSFORM WORKSTREAM → TOAST
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# MOCK SEND TO TOAST
# Eventually becomes POST /labor/v1/employees
# ------------------------------------------------------------------

def send_to_toast(employee):

    toast_employees.append(employee)

    return True


# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# VIEW MIGRATION HISTORY
# ------------------------------------------------------------------

@app.get("/migrations")
def get_migrations():

    return migration_log


# ------------------------------------------------------------------
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