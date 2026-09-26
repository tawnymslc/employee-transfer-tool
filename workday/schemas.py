from pydantic import BaseModel
from typing import Optional

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