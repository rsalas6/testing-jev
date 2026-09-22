"""Test 1 — the three question types in one call.

    task run:test-1-types.py                   friendly summary
    task run -- test-1-types.py --raw          the full response, pretty printed
    task run -- test-1-types.py --save         also writes test-1-types-output.txt
    task run -- test-1-types.py --raw --save   writes test-1-types-raw-output.txt
    task run -- test-1-types.py --state "..."  evaluate your own text

Choice: pick one option. Score: place it on a described scale. Noul: yes/no.
All three are asked in a single request and answered in parallel.
"""

import argparse
import contextlib
import io
import json
import pathlib
import sys
import time

from dotenv import load_dotenv
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

load_dotenv()  # the SDK reads TYPESAFE_API_KEY from the environment

# https://docs.typesafe.ai/models — charged per input token; output is free.
USD_PER_INPUT_TOKEN = 0.042 / 1_000_000

parser = argparse.ArgumentParser()
parser.add_argument("--raw", action="store_true", help="print the full API response")
parser.add_argument("--save", action="store_true", help="also write the output to a .txt")
parser.add_argument("--state", default=None, help="text to evaluate")
args = parser.parse_args()

STATE = args.state or (
    "Hi, I've been trying to connect my Stripe account for 3 days and the "
    "integration keeps failing. I'm losing sales. Please help ASAP."
)

QUESTIONS = {
    # Choice: one option out of a set (up to 255). Descriptions matter.
    "department": Choice(
        instructions="Which team should handle this",
        criteria={
            "billing": "Payment or subscription issues",
            "technical": "Bugs or integration problems",
            "sales": "Pricing or account questions",
            "other": "Fits none of the above",
        },
    ),
    # Score: a position on an ordered scale you describe in words (2-10 levels).
    "frustration": Score(
        instructions="How frustrated the customer appears",
        criteria=[
            "Calm, just stating facts",
            "Frustrated but civil",
            "Very angry, strong language or threatening to leave",
        ],
    ),
    # Noul: a statement, answered with P(true).
    "is_urgent": Noul(instructions="The message conveys urgency or time-sensitivity"),
}


def as_dict(obj):
    """The SDK returns pydantic-style objects; fall back to __dict__."""
    for attr in ("model_dump", "dict", "to_dict"):
        if hasattr(obj, attr):
            return getattr(obj, attr)()
    return vars(obj)


def bar(value: float, width: int = 20) -> str:
    filled = round(value * width)
    return "█" * filled + "·" * (width - filled)


def distribution(probabilities: dict, legend: dict | None = None) -> None:
    for key, probability in sorted(probabilities.items(), key=lambda kv: -kv[1]):
        label = legend.get(key, legend.get(str(key), key)) if legend else key
        print(f"    {bar(probability)} {probability:>5.2f}  {label}")


def summary(response, elapsed_ms: float) -> None:
    department = response.answers["department"]
    frustration = response.answers["frustration"]
    is_urgent = response.answers["is_urgent"]

    print(f"state: {STATE}\n")

    print(f"[choice] department = {department.choice}   confidence {department.confidence:.2f}")
    distribution(department.probabilities)

    print(f"\n[score]  frustration = {frustration.score}   confidence {frustration.confidence:.2f}")
    distribution(frustration.probabilities, getattr(frustration, "legend", None))

    print(f"\n[noul]   is_urgent = {is_urgent.noul:.2f}   (no confidence field: the number is both)")
    print(f"    {bar(is_urgent.noul)}")

    print(f"\n{elapsed_ms:.0f} ms for all three · {response.model}")


def cost(response) -> None:
    usage = response.usage
    spent = usage.input_tokens * USD_PER_INPUT_TOKEN
    print(
        f"cost: {usage.input_tokens} in / {usage.output_tokens} out tokens"
        f" = ${spent:.8f}   (output tokens are free)"
    )
    print(f"      ${spent * 1_000:.4f} per 1k calls · {int(1 / spent):,} calls per dollar")


client = TypeSafeClient()

start = time.perf_counter()
response = client.system_one(state=STATE, questions=QUESTIONS)
elapsed = (time.perf_counter() - start) * 1000

buffer = io.StringIO()
with contextlib.redirect_stdout(buffer) if args.save else contextlib.nullcontext():
    if args.raw:
        print(json.dumps(as_dict(response), indent=2, default=str, sort_keys=False))
    else:
        summary(response, elapsed)
    print()
    cost(response)

if args.save:
    text = buffer.getvalue()
    sys.stdout.write(text)
    name = f"{pathlib.Path(__file__).stem}{'-raw' if args.raw else ''}-output.txt"
    pathlib.Path(name).write_text(text)
    print(f"\nsaved to {name}")
