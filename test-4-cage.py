"""Test 4 — Jev can only answer from the list you give it.

    task run:test-4-cage.py

Ask "which superhero is this?" about a ham sandwich. There is no right answer,
but a Choice has to pick something. Then add an "other" option and ask again.
"""

from dotenv import load_dotenv
from typesafe_sdk import Choice, TypeSafeClient

load_dotenv()

SANDWICH = "Two slices of bread with ham and cheese in the middle."

THREE_OPTIONS = {
    "batman": "A rich guy in a bat costume",
    "superman": "An alien who can fly",
    "spiderman": "A teenager who shoots webs",
}

FOUR_OPTIONS = THREE_OPTIONS | {"other": "Not a superhero at all"}

client = TypeSafeClient()


def ask(options):
    answer = client.system_one(
        state=SANDWICH,
        questions={"hero": Choice(instructions="Which superhero is this", criteria=options)},
    ).answers["hero"]
    return answer.choice, answer.confidence


print(f'state:    "{SANDWICH}"')
print("question: which superhero is this?\n")

choice, confidence = ask(THREE_OPTIONS)
print(f"3 options  -> {choice}   confidence {confidence:.2f}   <- wrong, but it had to pick one")

choice, confidence = ask(FOUR_OPTIONS)
print(f"+ 'other'  -> {choice}   confidence {confidence:.2f}   <- now it can say no")

print("\nLesson: always give it an escape hatch, and check the confidence.")
