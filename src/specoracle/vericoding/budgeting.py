from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetPolicy:
    candidate_bank_usd: float = 140.0
    selector_usd: float = 80.0
    e2e_usd: float = 120.0
    secure_usd: float = 40.0
    adjudication_usd: float = 20.0
    hard_ceiling_usd: float = 400.0

    def to_dict(self) -> dict[str, float]:
        return self.__dict__.copy()


def assert_within_budget(total_usd: float, policy: BudgetPolicy = BudgetPolicy()) -> None:
    if total_usd > policy.hard_ceiling_usd:
        raise RuntimeError(
            f"vericoding budget overrun risk: ${total_usd:.2f} > ${policy.hard_ceiling_usd:.2f}"
        )
