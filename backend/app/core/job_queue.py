"""Simple Redis-based job queue for async request processing."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Job expiry time in seconds (1 hour)
JOB_EXPIRY = 3600

# Job queue key prefix
JOB_PREFIX = "job:"


class JobStatus(str, Enum):
    """Job processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResult(BaseModel):
    """Job result model."""
    job_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


async def create_job(job_data: Dict[str, Any]) -> str:
    """
    Create a new job in the queue.

    Args:
        job_data: Data to store with the job

    Returns:
        Job ID
    """
    try:
        redis = await get_redis()
        if redis is None:
            raise RuntimeError("Redis not available")

        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        job = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "created_at": now,
            "updated_at": now,
            "data": job_data,
            "result": None,
            "error": None,
        }

        await redis.setex(
            f"{JOB_PREFIX}{job_id}",
            JOB_EXPIRY,
            json.dumps(job),
        )

        logger.info(f"Created job {job_id}")
        return job_id

    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise


async def get_job(job_id: str) -> Optional[JobResult]:
    """
    Get job status and result.

    Args:
        job_id: Job ID to look up

    Returns:
        JobResult or None if not found
    """
    try:
        redis = await get_redis()
        if redis is None:
            return None

        data = await redis.get(f"{JOB_PREFIX}{job_id}")
        if not data:
            return None

        job = json.loads(data)
        return JobResult(
            job_id=job["job_id"],
            status=JobStatus(job["status"]),
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            result=job.get("result"),
            error=job.get("error"),
        )

    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        return None


async def update_job_status(
    job_id: str,
    status: JobStatus,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> bool:
    """
    Update job status and optionally set result or error.

    Args:
        job_id: Job ID to update
        status: New status
        result: Optional result data
        error: Optional error message

    Returns:
        True if updated successfully
    """
    try:
        redis = await get_redis()
        if redis is None:
            return False

        key = f"{JOB_PREFIX}{job_id}"
        data = await redis.get(key)
        if not data:
            return False

        job = json.loads(data)
        job["status"] = status.value
        job["updated_at"] = datetime.utcnow().isoformat()

        if result is not None:
            job["result"] = result
        if error is not None:
            job["error"] = error

        # Refresh TTL
        await redis.setex(key, JOB_EXPIRY, json.dumps(job))
        logger.info(f"Updated job {job_id} to status {status.value}")
        return True

    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {e}")
        return False


async def get_job_data(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the original job data.

    Args:
        job_id: Job ID

    Returns:
        Job data or None
    """
    try:
        redis = await get_redis()
        if redis is None:
            return None

        data = await redis.get(f"{JOB_PREFIX}{job_id}")
        if not data:
            return None

        job = json.loads(data)
        return job.get("data")

    except Exception as e:
        logger.error(f"Failed to get job data {job_id}: {e}")
        return None


async def process_job_async(
    job_id: str,
    processor_fn,
) -> None:
    """
    Process a job asynchronously.

    Args:
        job_id: Job ID to process
        processor_fn: Async function that takes job_data and returns result dict
    """
    try:
        # Mark as processing
        await update_job_status(job_id, JobStatus.PROCESSING)

        # Get job data
        job_data = await get_job_data(job_id)
        if job_data is None:
            await update_job_status(job_id, JobStatus.FAILED, error="Job data not found")
            return

        # Process
        result = await processor_fn(job_data)

        # Mark completed
        await update_job_status(job_id, JobStatus.COMPLETED, result=result)

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        await update_job_status(job_id, JobStatus.FAILED, error=str(e))
