from workday.schemas import WorkdayTransferEvent, WorkerContract, PayrollEmployee, LearningUser
import time

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