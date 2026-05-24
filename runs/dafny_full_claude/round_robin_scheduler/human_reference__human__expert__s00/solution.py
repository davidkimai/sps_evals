def assign_round_robin(workers: list[dict], jobs: list[str]) -> list[dict]:
    enabled = [worker["name"] for worker in workers if worker.get("enabled", True)]
    if not enabled:
        raise ValueError("at least one worker must be enabled")
    assignments = []
    for index, job in enumerate(jobs):
        assignments.append({"job": job, "worker": enabled[index % len(enabled)]})
    return assignments
