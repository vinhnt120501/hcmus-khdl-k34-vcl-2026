"""Nhãn thực thể và từ vựng quan hệ dùng chung."""

ENTITY_LABELS = ["PER", "LOC", "TIT", "EVT", "DYNA"]

PREDICATES = {
    "descendant_of", "father_of", "mother_of", "spouse_of", "sibling_of",
    "appointed_to", "bestowed_title", "holds_title", "ascended_throne",
    "succeeded_by", "ruled", "moved_capital_to", "conquered", "quelled_rebellion",
    "led_uprising", "issued_edict", "dispatched_to", "part_of", "located_at",
    "borders_with", "occurred_on", "reign_era", "alias_of", "other_relation",
}

SIDES = ("zh", "vi")
