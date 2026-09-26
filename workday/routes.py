from fastapi import APIRouter
from datetime import datetime

from workday.schemas import WorkdayTransferEvent
from workday.data import workday_workers
from workday.services import (
    transform_workday_worker,
    transform_worker_to_payroll,
    transform_worker_to_learning,
    send_to_payroll,
    send_to_learning,
    deliver_with_retry,
    integration_log,
    payroll_attempts,
    learning_attempts,
)


router = APIRouter(
    prefix="/workday",
    tags=["Workday Integration"]
)


# PROCESS ONE WORKDAY EMPLOYEE TRANSFER EVENT
# ------------------------------------------------------------------
@router.post("/events/worker-transfer")
def process_worker_transfer(event: WorkdayTransferEvent):

    # Workday event → canonical worker
    worker = transform_workday_worker(event)

    # Canonical worker → Payroll
    payroll_employee = transform_worker_to_payroll(worker)

    payroll_result = deliver_with_retry(
        send_to_payroll,
        payroll_employee
    )

    # Canonical worker → Learning
    learning_user = transform_worker_to_learning(worker)

    learning_result = deliver_with_retry(
        send_to_learning,
        learning_user
    )

    # Log Payroll delivery
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

    # Log Learning delivery
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


# RUN ALL DEMO EVENTS / RUNNING POST FOR WORKER TRANSFER
# ------------------------------------------------------------------
@router.post("/demo/run")
def run_workday_demo():

    results = []

    for worker_data in workday_workers:
        event = WorkdayTransferEvent(**worker_data)
        result = process_worker_transfer(event)
        results.append(result)

    return results


# VIEW WORKDAY INTEGRATION HISTORY
# ------------------------------------------------------------------
@router.get("/integrations")
def get_workday_integrations():

    return integration_log


# VIEW WORKDAY INTEGRATION SUMMARY
# ------------------------------------------------------------------
@router.get("/integrations/summary")
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
        entry["latency_ms"]
        for entry in integration_log
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


# RESET WORKDAY DEMO
# ------------------------------------------------------------------
@router.post("/demo/reset")
def clear_logs():

    integration_log.clear()
    payroll_attempts.clear()
    learning_attempts.clear()

    return {
        "status": "success",
        "message": "Workday demo data reset"
    }