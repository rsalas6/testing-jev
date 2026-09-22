"""Test 3 — when Jev says 0.8, is it right 80% of the time?

    task run:test-3-calibration.py
    task run -- test-3-calibration.py --detail   every statement, one by one

This is the claim that matters and the one you can't check by reading the docs.
Every statement below has an answer I wrote by hand (True or False). Easy ones,
plus a few that need a second of thought, so the probabilities spread out.
"""

import sys
from collections import defaultdict

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()

# (scene, [(statement, is it true?), ...])
CASES = [
    (
        "Pikachu uses Thunderbolt on Onix, a rock and ground type.",
        [
            ("The attack is electric", True),
            ("The attack is very effective", False),
            ("Onix is a water type", False),
            ("A Pokemon is attacking another Pokemon", True),
        ],
    ),
    (
        "Goku is a Saiyan raised on Earth. He has died twice and come back both times.",
        [
            ("Goku is human", False),
            ("Goku is currently alive", True),
            ("Goku has been to the afterlife", True),
            ("Goku was born on Earth", False),
        ],
    ),
    (
        "Mario jumps on a Goomba, grabs a fire flower, and falls into a pit.",
        [
            ("Mario defeats an enemy", True),
            ("Mario picks up a power-up", True),
            ("Mario finishes the level", False),
            ("Mario loses a life", True),
            ("The fire flower saves him from the pit", False),
        ],
    ),
    (
        "Batman has no superpowers. He is a billionaire who trained for years and "
        "refuses to kill.",
        [
            ("Batman can fly on his own", False),
            ("Batman is wealthy", True),
            ("Batman kills his enemies", False),
            ("Batman's abilities come from training", True),
        ],
    ),
    (
        "Vegeta trains at 300x gravity for six months and still loses to Goku.",
        [
            ("Vegeta trained hard", True),
            ("Vegeta won the fight", False),
            ("The training lasted more than a year", False),
            ("Goku is stronger in this fight", True),
        ],
    ),
    (
        "A wild Magikarp uses Splash. Nothing happens. It is level 5.",
        [
            ("The attack did damage", False),
            ("The Pokemon is weak", True),
            ("This Magikarp could evolve into Gyarados later", True),
            ("The Pokemon is fully evolved", False),
        ],
    ),
    (
        "Naruto eats ramen for dinner on Monday, Tuesday and Wednesday, then has "
        "barbecue on Thursday.",
        [
            ("Naruto ate ramen three days in a row", True),
            ("Naruto ate ramen every day that week", False),
            ("Naruto ate ramen on Thursday", False),
            ("Naruto likes ramen", True),
        ],
    ),
    (
        "Thanos snaps his fingers with all six Infinity Stones. Half of all life "
        "disappears.",
        [
            ("Thanos succeeded", True),
            ("Everyone died", False),
            ("Thanos was missing a stone", False),
            ("This is bad news for the heroes", True),
        ],
    ),
    (
        "Link opens a chest and finds 20 rupees. He already had 15. His wallet "
        "holds a maximum of 30.",
        [
            ("Link now has 35 rupees", False),
            ("Link's wallet is full", True),
            ("Link found money in the chest", True),
            ("Link lost rupees in this scene", False),
        ],
    ),
    (
        "Ash has lost every Pokemon League he has entered, but he keeps travelling "
        "to new regions with Pikachu.",
        [
            ("Ash has won a Pokemon League", False),
            ("Ash gives up easily", False),
            ("Pikachu stays with Ash", True),
            ("Ash has competed more than once", True),
        ],
    ),
]

client = TypeSafeClient()

detail = "--detail" in sys.argv

# Ask each scene's questions in one call, and keep (what Jev said, the truth).
results = []
for scene, items in CASES:
    questions = {f"q{i}": Noul(instructions=text) for i, (text, _) in enumerate(items)}
    answers = client.system_one(state=scene, questions=questions).answers

    if detail:
        print(f"\n{scene}")
        print(f"  {'jev':>5}  {'truth':<5} {'':<3} statement")

    for i, (text, truth) in enumerate(items):
        said = answers[f"q{i}"].noul
        results.append((said, truth, text))
        if detail:
            # Jev only sees the statement. `truth` is the answer we wrote by hand.
            hit = "ok" if (said > 0.5) == truth else "MISS"
            print(f"  {said:>5.2f}  {str(truth):<5} {hit:<4} {text}")

if detail:
    print()

total = len(results)
correct = sum((p > 0.5) == truth for p, truth, _ in results)
brier = sum((p - truth) ** 2 for p, truth, _ in results) / total

print(f"{total} statements over {len(CASES)} scenes\n")
print(f"accuracy      {correct}/{total} = {correct / total:.0%}")
print(f"brier score   {brier:.3f}   (0 = perfect, 0.25 = always saying 50/50)")

# Calibration: group by what it said, compare with what was true.
buckets = defaultdict(list)
for p, truth, _ in results:
    buckets[min(int(p * 10), 9)].append((p, truth))

print(f"\n{'it said':>12} {'n':>3} {'was true':>9}")
error = 0.0
for bucket in sorted(buckets):
    rows = buckets[bucket]
    said = sum(p for p, _ in rows) / len(rows)
    happened = sum(truth for _, truth in rows) / len(rows)
    error += abs(said - happened) * len(rows)
    print(f"{said:>12.2f} {len(rows):>3} {happened:>9.0%}")

print(f"\ncalibration error {error / total:.3f}   (how far the two columns are apart)")

print("\nbiggest misses")
for p, truth, text in sorted(results, key=lambda r: -abs(r[0] - r[1]))[:3]:
    print(f"  said {p:.2f}, answer is {'yes' if truth else 'no'}:  {text}")
