"""Test 5 — does a long state make it worse?

    task run:test-5-long-state.py
    task run -- test-5-long-state.py --hard   filler that looks like the needle

Their docs admit accuracy drops when the state fills up with detail that has
nothing to do with the question. So: hide one made up fact in a pile of cartoon
filler and ask about it as the pile grows.

The fact has to be invented, not something the model already knows, otherwise
it can answer from memory instead of reading.
"""

import sys

from dotenv import load_dotenv
from typesafe_sdk import Noul, TypeSafeClient
from typesafe_sdk._core.errors import TypeSafeBadRequestError

load_dotenv()

NEEDLE = (
    "On Tuesday, Wile E. Coyote bought a rocket at Acme Discount Store number 47 "
    "and paid with a coupon for 12 dollars."
)

# Sentences with the same shape as the needle: a character, a day, a store
# number and a coupon. Now the model has to keep them apart.
CONFUSABLE = [
    "On Friday, Daffy Duck bought a jetpack at Acme Discount Store number 12 and paid with a coupon for 8 dollars.",
    "On Monday, Tom bought a mousetrap at Acme Discount Store number 31 and paid with a coupon for 5 dollars.",
    "On Sunday, Bugs Bunny bought a carrot slicer at Acme Discount Store number 9 and paid with a coupon for 20 dollars.",
    "On Thursday, Sylvester bought a ladder at Acme Discount Store number 47 and paid with a coupon for 3 dollars.",
    "On Wednesday, Yosemite Sam bought dynamite at Acme Discount Store number 22 and paid with a coupon for 15 dollars.",
]

FILLER = [
    "The Road Runner ran past a cactus and said beep beep.",
    "Tom set a trap for Jerry and caught his own tail instead.",
    "Scooby and Shaggy ate a sandwich the size of a small car.",
    "Bugs Bunny took a wrong turn at Albuquerque again.",
    "Homer fell asleep at the console of the nuclear plant.",
    "SpongeBob flipped a patty and smiled at nobody in particular.",
    "Daffy Duck argued about whether it was duck season or rabbit season.",
    "Fred Flintstone parked his car with his own two feet.",
]

QUESTIONS = {
    # True, and only findable by reading the needle.
    "tuesday": "The rocket was bought on a Tuesday",
    # False, same shape, to see if noise pushes it up.
    "friday": "The rocket was bought on a Friday",
    # True, but vague: which coupon? The filler is full of other coupons.
    "vague": "The coupon was worth 12 dollars",
    # Same fact, asked precisely.
    "precise": "The coupon used to buy the rocket was worth 12 dollars",
}


HARD = "--hard" in sys.argv
LINES = CONFUSABLE if HARD else FILLER


def build_state(filler_lines: int) -> str:
    """The needle sits in the middle of the haystack."""
    half = [LINES[i % len(LINES)] for i in range(filler_lines // 2)]
    return " ".join([*half, NEEDLE, *half])


client = TypeSafeClient()

print(f"needle: {NEEDLE}")
print(f"filler: {'lines that look just like it' if HARD else 'unrelated cartoon lines'}\n")
print(f"{'filler lines':>12} {'words':>7} {'tokens':>7} {'tuesday':>9} {'friday':>8} {'vague':>8} {'precise':>9}")

for filler_lines in (0, 20, 100, 400, 800, 1200):
    state = build_state(filler_lines)
    try:
        response = client.system_one(
            state=state,
            questions={key: Noul(instructions=text) for key, text in QUESTIONS.items()},
        )
    except TypeSafeBadRequestError as error:
        # The state budget is 32k tokens, so this is where the wall is.
        print(f"{filler_lines:>12} {len(state.split()):>7}   rejected: {error.body['detail']['error_type']}")
        continue
    answers = response.answers
    print(
        f"{filler_lines:>12} {len(state.split()):>7} {response.usage.input_tokens:>7}"
        f" {answers['tuesday'].noul:>9.2f} {answers['friday'].noul:>8.2f}"
        f" {answers['vague'].noul:>8.2f} {answers['precise'].noul:>9.2f}"
    )

print("\ntuesday and precise should stay near 1.00, friday near 0.00.")
