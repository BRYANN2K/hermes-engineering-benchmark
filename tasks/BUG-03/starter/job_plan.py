def plan_jobs(jobs):
    return [job['name'] for job in sorted(jobs, key=lambda job: -job.get('priority', 0))]
