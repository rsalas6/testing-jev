"""Test 1 — the three question types.

    task run:test-1-types.py
    task run -- test-1-types.py --raw            see the whole response
    task run -- test-1-types.py > test-1.txt     save it yourself
"""

import json
import sys

from dotenv import load_dotenv
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

load_dotenv()  # the SDK reads TYPESAFE_API_KEY from the environment

STATE = """
Goku powers up to Super Saiyan 3 and screams for twenty minutes.
Frieza waits patiently, filing his nails.
"""

QUESTIONS = {
    # Choice: pick one option out of a set.
    "genre": Choice(
        instructions="What kind of scene is this",
        criteria={
            "fight": "Characters are fighting",
            "comedy": "The scene is played for laughs",
            "romance": "Characters are falling in love",
            "other": "None of the above",
        },
    ),
    # Score: a position on a scale you describe in words.
    "power_level": Score(
        instructions="How dangerous is this situation",
        criteria=["Nothing is happening", "A normal fight", "The planet might explode"],
    ),
    # Noul: a statement, answered with the probability that it is true.
    "is_anime": Noul(instructions="This scene is from an anime"),
}

client = TypeSafeClient()
response = client.system_one(state=STATE, questions=QUESTIONS)

if "--raw" in sys.argv:
    print(json.dumps(response.model_dump(), indent=2, default=str))
    sys.exit()

genre = response.answers["genre"]
power = response.answers["power_level"]
anime = response.answers["is_anime"]

print(STATE.strip(), "\n")
print(f"[choice] genre       = {genre.choice}  (confidence {genre.confidence:.2f})")
print(f"         {genre.probabilities}")
print(f"[score]  power_level = {power.score}  (confidence {power.confidence:.2f})")
print(f"         {power.probabilities}")
print(f"[noul]   is_anime    = {anime.noul}")

# The point: your code branches on numbers, not on text.
if power.score >= 1.5:
    print("\n-> evacuate the planet")
else:
    print("\n-> keep watching")
