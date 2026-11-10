"""packlist — build a packing checklist for a trip.

Give the trip length, the climates you will meet and the activities you
plan, and packlist prints a grouped checklist with estimated weight and a
carry-on limit check.

Usage:
    python3 packlist.py --days 10 --climate cold,rain --activity hiking
    python3 packlist.py trip.json
    python3 packlist.py --days 3 --climate hot --carry-on 7000 --json

trip.json format:
    {"days": 10, "climates": ["cold", "rain"], "activities": ["hiking"],
     "custom": [{"name": "camera", "weight_g": 650, "category": "gear"}]}
"""

import argparse
import json
import sys

# name, weight in grams, category
BASE_ITEMS = [
    ("passport / ID", 50, "documents"),
    ("phone + charger", 250, "gear"),
    ("toothbrush + toiletries", 300, "toiletries"),
    ("medications", 100, "toiletries"),
    ("daypack", 400, "gear"),
]

# items that scale with the number of days (per-day quantity, capped)
PER_DAY_ITEMS = [
    ("underwear", 60, "clothing", 7),
    ("socks", 50, "clothing", 7),
    ("t-shirt", 150, "clothing", 5),
]

CLIMATE_ITEMS = {
    "cold": [
        ("warm jacket", 800, "clothing"),
        ("thermal base layer", 200, "clothing"),
        ("gloves + beanie", 150, "clothing"),
    ],
    "hot": [
        ("sunscreen", 200, "toiletries"),
        ("sun hat", 120, "clothing"),
        ("light shorts", 200, "clothing"),
    ],
    "rain": [
        ("rain jacket", 350, "clothing"),
        ("waterproof bag cover", 100, "gear"),
    ],
    "humid": [
        ("insect repellent", 150, "toiletries"),
        ("quick-dry towel", 200, "gear"),
    ],
}

ACTIVITY_ITEMS = {
    "hiking": [
        ("hiking boots", 1100, "gear"),
        ("trekking poles", 500, "gear"),
        ("water bottle 1L", 1000, "gear"),
    ],
    "swimming": [
        ("swimsuit", 150, "clothing"),
        ("goggles", 80, "gear"),
    ],
    "formal": [
        ("smart shirt", 250, "clothing"),
        ("dress shoes", 900, "gear"),
    ],
    "photography": [
        ("camera", 650, "gear"),
        ("spare memory card", 20, "gear"),
    ],
}

# warnings for combinations that need an extra reminder
COMBO_WARNINGS = [
    ({"cold", "rain"}, "Cold + rain: add a waterproof shell over your warm layers."),
    ({"hot", "humid"}, "Hot + humid: pack extra water and reapply sunscreen often."),
    ({"hiking", "cold"}, "Hiking in the cold: bring altitude / cold-weather medication if needed."),
]

DEFAULT_CARRY_ON_G = 7000


class Item:
    def __init__(self, name, weight_g, category, qty=1):
        self.name = name
        self.weight_g = weight_g
        self.category = category
        self.qty = qty

    @property
    def total_g(self):
        return self.weight_g * self.qty

    def to_dict(self):
        return {"name": self.name, "weight_g": self.weight_g,
                "category": self.category, "qty": self.qty}


def build_list(days, climates, activities, custom=None):
    """Build the packing list. Raises ValueError on bad input."""
    if days < 1:
        raise ValueError("days must be at least 1")
    unknown_climates = sorted(set(climates) - set(CLIMATE_ITEMS))
    if unknown_climates:
        raise ValueError("unknown climate(s): " + ", ".join(unknown_climates))
    unknown_activities = sorted(set(activities) - set(ACTIVITY_ITEMS))
    if unknown_activities:
        raise ValueError("unknown activit(ies): " + ", ".join(unknown_activities))

    items = [Item(name, w, cat) for name, w, cat in BASE_ITEMS]
    for name, w, cat, cap in PER_DAY_ITEMS:
        items.append(Item(name, w, cat, qty=min(days, cap)))
    for climate in sorted(set(climates)):
        items.extend(Item(n, w, c) for n, w, c in CLIMATE_ITEMS[climate])
    for activity in sorted(set(activities)):
        items.extend(Item(n, w, c) for n, w, c in ACTIVITY_ITEMS[activity])
    for entry in custom or []:
        items.append(Item(entry["name"], int(entry["weight_g"]),
                          entry.get("category", "misc"),
                          qty=int(entry.get("qty", 1))))
    return items


def total_weight_g(items):
    return sum(item.total_g for item in items)


def warnings_for(climates, activities):
    present = set(climates) | set(activities)
    return [msg for combo, msg in COMBO_WARNINGS if combo <= present]


def render_text(items, days, carry_on_g):
    lines = [f"Packing list — {days} day trip", "=" * 30, ""]
    by_category = {}
    for item in items:
        by_category.setdefault(item.category, []).append(item)
    for category in sorted(by_category):
        lines.append(f"[{category}]")
        for item in by_category[category]:
            qty = f" x{item.qty}" if item.qty > 1 else ""
            lines.append(f"  [ ] {item.name}{qty} ({item.total_g} g)")
        lines.append("")
    total = total_weight_g(items)
    lines.append(f"Total weight: {total} g ({total / 1000:.2f} kg)")
    if total <= carry_on_g:
        lines.append(f"OK: fits the {carry_on_g} g carry-on limit.")
    else:
        lines.append(
            f"OVER: {total - carry_on_g} g above the {carry_on_g} g "
            "carry-on limit — move items to checked luggage.")
    return "\n".join(lines)


def load_trip_file(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return (int(data.get("days", 1)),
            list(data.get("climates", [])),
            list(data.get("activities", [])),
            list(data.get("custom", [])))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build a packing checklist for a trip.")
    parser.add_argument("trip_file", nargs="?",
                        help="JSON file with days/climates/activities/custom")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--climate", default="",
                        help="comma-separated climates: cold,hot,rain,humid")
    parser.add_argument("--activity", default="",
                        help="comma-separated activities: hiking,swimming,formal,photography")
    parser.add_argument("--carry-on", type=int, default=DEFAULT_CARRY_ON_G,
                        help="carry-on weight limit in grams (default 7000)")
    parser.add_argument("--json", action="store_true",
                        help="print the list as JSON")
    args = parser.parse_args(argv)

    if args.trip_file:
        try:
            days, climates, activities, custom = load_trip_file(args.trip_file)
        except (OSError, ValueError, KeyError) as exc:
            print(f"error: cannot read trip file: {exc}", file=sys.stderr)
            return 2
    else:
        days = args.days
        climates = [c for c in args.climate.split(",") if c]
        activities = [a for a in args.activity.split(",") if a]
        custom = []

    try:
        items = build_list(days, climates, activities, custom)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(
            {"days": days, "items": [i.to_dict() for i in items],
             "total_weight_g": total_weight_g(items),
             "warnings": warnings_for(climates, activities)},
            indent=2, ensure_ascii=False))
    else:
        print(render_text(items, days, args.carry_on))
        for warning in warnings_for(climates, activities):
            print(f"! {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
