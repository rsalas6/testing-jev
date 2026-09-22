"""Test 2 — parallelism: does asking more questions cost more time?

    task run:test-2-parallel.py
    task run -- test-2-parallel.py --save      writes test-2-parallel-output.txt
    task run -- test-2-parallel.py --runs 5    more repetitions per step
    task run -- test-2-parallel.py --answers   show what the 32 questions answered

The claim: the state is ingested once and every question is evaluated against it
in parallel, so latency should stay flat as questions pile up. If that holds,
"speculative fan-out" (ask everything up front, let code pick) is the right
design instead of one call per decision.
"""

import argparse
import contextlib
import io
import pathlib
import statistics
import sys
import time

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient

load_dotenv()  # the SDK reads TYPESAFE_API_KEY from the environment

USD_PER_INPUT_TOKEN = 0.042 / 1_000_000  # output tokens are free

parser = argparse.ArgumentParser()
parser.add_argument("--save", action="store_true", help="also write the output to a .txt")
parser.add_argument("--runs", type=int, default=3, help="calls per step (median is reported)")
parser.add_argument("--answers", action="store_true", help="print the answers to all questions")
args = parser.parse_args()

STATE = """
Subject: Refund for order #A-2291

I ordered the annual plan on Friday and was charged twice. I've emailed support
twice with no answer. My team of 12 can't log in either, we get a 500 error on
the SSO page. I need this fixed today or we're moving to another vendor.
"""

QUESTIONS = [
    "The customer was charged more than once",
    "The customer mentions a login or authentication problem",
    "The customer threatens to churn",
    "The customer is a paying customer",
    "The message mentions a specific order number",
    "The customer has contacted support before about this",
    "The message mentions a team or multiple users",
    "The customer asks for a refund",
    "The message reports a server error",
    "The message has a deadline",
    "The customer sounds angry",
    "This should be escalated to engineering",
    "This should be escalated to billing",
    "The message contains a security concern",
    "The customer is on an annual plan",
    "The message mentions single sign-on",
    "The customer is a new customer",
    "The message includes an attachment",
    "The customer offers a workaround",
    "The message was written by a bot",
    "The customer is asking for a discount",
    "The message mentions a competitor by name",
    "The customer wants to cancel immediately",
    "The message contains profanity",
    "The message mentions an invoice",
    "The customer mentions a phone call",
    "The message is a duplicate of a previous ticket",
    "The customer is an administrator of the account",
    "The message mentions a browser",
    "The message mentions a mobile device",
    "The request is covered by a standard refund policy",
    "The customer provided steps to reproduce",
]

client = TypeSafeClient()

STEPS = (1, 2, 5, 10, 20, 32)


def measure(n: int) -> tuple[float, int, int]:
    questions = {f"q{i}": Noul(instructions=q) for i, q in enumerate(QUESTIONS[:n])}
    times, usage = [], None
    for _ in range(args.runs):
        start = time.perf_counter()
        response = client.system_one(state=STATE, questions=questions)
        times.append((time.perf_counter() - start) * 1000)
        usage = response.usage
    return statistics.median(times), usage.input_tokens, usage.output_tokens


def answers() -> None:
    """The work itself: 32 yes/no questions about one ticket, in one call."""
    questions = {f"q{i}": Noul(instructions=q) for i, q in enumerate(QUESTIONS)}
    start = time.perf_counter()
    response = client.system_one(state=STATE, questions=questions)
    elapsed = (time.perf_counter() - start) * 1000

    print(STATE.strip())
    print(f"\n{len(QUESTIONS)} Noul questions, one call, {elapsed:.0f} ms\n")

    scored = [
        (response.answers[f"q{i}"].noul, text) for i, text in enumerate(QUESTIONS)
    ]
    for probability, text in sorted(scored, reverse=True):
        mark = "yes " if probability > 0.5 else "no  "
        print(f"  {probability:>5.2f}  {mark}{text}")

    usd = response.usage.input_tokens * USD_PER_INPUT_TOKEN
    print(f"\n${usd:.8f} total · ${usd / len(QUESTIONS):.8f} per answer")


def run() -> None:
    print(f"state: {len(STATE.split())} words · {args.runs} calls per step, median reported\n")
    header = f"{'questions':>9} {'ms':>6} {'ms/question':>12} {'in tok':>7} {'$/call':>12} {'$/decision':>12}"
    print(header)
    print("-" * len(header))

    first_ms = None
    for n in STEPS:
        ms, tokens_in, _ = measure(n)
        first_ms = first_ms or ms
        usd = tokens_in * USD_PER_INPUT_TOKEN
        print(
            f"{n:>9} {ms:>6.0f} {ms / n:>12.0f} {tokens_in:>7}"
            f" {usd:>12.8f} {usd / n:>12.8f}"
        )

    print(
        "\nIf the last row's ms is close to the first row's, the questions really"
        "\nare evaluated in parallel: 32 decisions for the price of one round trip."
    )


buffer = io.StringIO()
with contextlib.redirect_stdout(buffer) if args.save else contextlib.nullcontext():
    answers() if args.answers else run()

if args.save:
    text = buffer.getvalue()
    sys.stdout.write(text)
    name = f"{pathlib.Path(__file__).stem}{'-answers' if args.answers else ''}-output.txt"
    pathlib.Path(name).write_text(text)
    print(f"\nsaved to {name}")
