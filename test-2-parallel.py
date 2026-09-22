"""Test 2 — is asking 20 questions slower than asking 1?

    task run:test-2-parallel.py
    task run -- test-2-parallel.py --answers     see what it decided

Jev reads the state once and answers every question in parallel, so the wall
clock should barely move as questions pile up.
"""

import sys
import time

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()

PRICE_PER_INPUT_TOKEN = 0.042 / 1_000_000  # output tokens are free

STATE = """
Ash throws a Poke Ball at a wild Pikachu. It bounces off, the Pikachu
Thunderbolts him, and Team Rocket shows up in a hot air balloon.
"""

QUESTIONS = [
    "A Pokemon is being caught",
    "Someone gets electrocuted",
    "Team Rocket appears",
    "The scene happens indoors",
    "A Poke Ball is used",
    "The Pikachu is wild",
    "Ash is the trainer in the scene",
    "The balloon is shaped like a Meowth",
    "Someone is injured badly enough to need a hospital",
    "This is a battle between two trainers",
    "A legendary Pokemon appears",
    "The Pokemon obeys Ash",
    "The scene is from Dragon Ball",
    "Pikachu is an electric type",
    "Someone says the word 'twerp'",
    "The scene takes place in space",
    "Ash succeeds on his first try",
    "There is a flying vehicle in the scene",
    "The Pikachu attacks the trainer",
    "The scene is animated",
]

client = TypeSafeClient()


def ask(how_many: int):
    """One call with `how_many` yes/no questions. Returns ms and the response."""
    questions = {f"q{i}": Noul(instructions=q) for i, q in enumerate(QUESTIONS[:how_many])}
    start = time.perf_counter()
    response = client.system_one(state=STATE, questions=questions)
    return (time.perf_counter() - start) * 1000, response


print(STATE.strip(), "\n")

if "--answers" in sys.argv:
    ms, response = ask(len(QUESTIONS))
    print(f"{len(QUESTIONS)} questions, one call, {ms:.0f} ms\n")
    for i, question in enumerate(QUESTIONS):
        probability = response.answers[f"q{i}"].noul
        print(f"  {probability:>5.2f}  {'yes' if probability > 0.5 else 'no '}  {question}")
    sys.exit()

print(f"{'questions':>9} {'ms':>6} {'ms each':>8} {'tokens':>7} {'$ each':>12}")
for how_many in (1, 5, 10, 20):
    ms, response = ask(how_many)
    tokens = response.usage.input_tokens
    usd = tokens * PRICE_PER_INPUT_TOKEN / how_many
    print(f"{how_many:>9} {ms:>6.0f} {ms / how_many:>8.0f} {tokens:>7} {usd:>12.8f}")

print("\nSame wall clock, 20x the decisions. Ask everything in one call.")
