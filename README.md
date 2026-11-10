# packlist

Tiny packing-list generator for trips — a CLI that turns a trip's length,
climates and activities into a grouped checklist with estimated weight and
a carry-on limit check.

Tell it how many days you travel, which climates you will meet
(`cold`, `hot`, `rain`, `humid`) and what you plan to do (`hiking`,
`swimming`, `formal`, `photography`), and it prints what to pack, how much
it weighs, and whether it still fits in a carry-on. Handy before a
multi-climate trip like a South America crossing, where one bag has to cover
high-altitude cold and tropical heat.

Standard library only. No dependencies to install. Python 3.9+.

## Install

```sh
git clone https://github.com/moco-oss-lab/packlist.git
cd packlist
python3 packlist.py --help
```

## Usage

```sh
# 10 days, cold + rainy, with hiking
python3 packlist.py --days 10 --climate cold,rain --activity hiking

# Machine-readable output
python3 packlist.py --days 3 --climate hot --json

# From a JSON file (allows custom items too)
python3 packlist.py trip.json
```

`trip.json` format:

```json
{
  "days": 10,
  "climates": ["cold", "rain"],
  "activities": ["hiking"],
  "custom": [
    {"name": "camera", "weight_g": 650, "category": "gear"}
  ]
}
```

Example output:

```
Packing list — 10 day trip
==============================

[clothing]
  [ ] underwear x7 (420 g)
  [ ] warm jacket (800 g)
  ...

Total weight: 6820 g (6.82 kg)
OK: fits the 7000 g carry-on limit.
! Cold + rain: add a waterproof shell over your warm layers.
```

Per-day items (underwear, socks, t-shirts) scale with the trip length and
are capped at a sensible maximum. The `--carry-on` flag changes the weight
limit in grams (default 7000). Climate/activity combinations that need
extra attention print a warning line starting with `!`.

## Tests

```sh
python3 -m unittest test_packlist -v
```

## License

MIT — see [LICENSE](LICENSE).
