"""Background job management.

Provides a simple local job system using asyncio.
Designed to be replaceable with Celery/RQ later.
"""

import asyncio
import logging
import time
import traceback
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field

from app.config import Settings

logger = logging.getLogger(__name__)


class JobState(str, Enum):
    """Job execution states."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Represents a processing job."""
    job_id: str
    project_id: str
    state: JobState = JobState.QUEUED
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None


class JobManager:
    """Manages background processing jobs.
    
    Uses asyncio tasks for non-blocking pipeline execution.
    Can be replaced with Celery/RQ by implementing the same interface.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.jobs: dict[str, Job] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._counter = 0

    def _next_job_id(self) -> str:
        self._counter += 1
        return f"job-{self._counter:04d}"

    async def submit_processing_job(self, project_id: str, project_manager) -> str:
        """Submit a processing job."""
        existing = [j for j in self.jobs.values() if j.project_id == project_id and j.state in (JobState.QUEUED, JobState.PROCESSING)]
        if existing:
            raise ValueError(f'Project already has active job {existing[-1].job_id}')
        from app.pipeline.processor import PipelineProcessor

        job_id = self._next_job_id()
        job = Job(job_id=job_id, project_id=project_id)
        self.jobs[job_id] = job

        # Create and run the pipeline in a background task
        processor = PipelineProcessor(self.settings)

        async def _run():
            job.state = JobState.PROCESSING
            job.started_at = time.time()
            try:
                await asyncio.to_thread(processor.run, project_id, project_manager, job)
                job.state = JobState.COMPLETED
                job.completed_at = time.time()
                logger.info(f"Job {job_id} completed in {job.completed_at - job.started_at:.1f}s")
            except Exception as e:
                job.state = JobState.FAILED
                job.error = str(e)
                job.completed_at = time.time()
                logger.error(f"Job {job_id} failed: {e}")
                logger.debug(traceback.format_exc())

        task = asyncio.create_task(_run())
        self._tasks[job_id] = task

        logger.info(f"Submitted job {job_id} for project {project_id}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job status."""
        return self.jobs.get(job_id)

    def get_project_job(self, project_id: str) -> Optional[Job]:
        """Return the newest job for a project."""
        matches = [j for j in self.jobs.values() if j.project_id == project_id]
        return max(matches, key=lambda j: j.started_at or 0.0) if matches else None
