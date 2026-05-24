def route_tickets(tickets: list[dict], rules: dict[str, dict]) -> list[dict]:
    severity_boost_table = {"critical": 10, "high": 5}
    routed_rows = []
    for ticket in tickets:
        if not _valid_ticket(ticket):
            continue
        service_rule_table = rules.get(ticket["service"], rules.get("default", {}))
        priority = int(service_rule_table.get("priority", 0))
        priority += severity_boost_table.get(ticket["severity"], 0)
        routed_rows.append(
            {
                "id": ticket["id"],
                "queue": service_rule_table.get("queue", "triage"),
                "priority": priority,
                "status_code": "routed",
            }
        )
    return routed_rows


def _valid_ticket(ticket: dict) -> bool:
    return all(ticket.get(field) for field in ("id", "severity", "service"))
