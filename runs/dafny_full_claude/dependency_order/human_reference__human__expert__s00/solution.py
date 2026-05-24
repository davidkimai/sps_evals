from __future__ import annotations


def plan_batches(dependencies: dict[str, list[str]]) -> list[list[str]]:
    tasks = set(dependencies)
    for blockers in dependencies.values():
        tasks.update(blockers)

    remaining = {task: set(dependencies.get(task, [])) for task in tasks}
    batches: list[list[str]] = []
    while remaining:
        ready = sorted(task for task, blockers in remaining.items() if not blockers)
        if not ready:
            raise ValueError("dependency graph contains a cycle")

        batches.append(ready)
        completed = set(ready)
        remaining = {
            task: blockers - completed
            for task, blockers in remaining.items()
            if task not in completed
        }
    return batches
