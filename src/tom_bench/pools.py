"""Curated content pools for procedural scenario generation.

Deliberately avoids "Sally", "Anne", "basket", and "marble" (the classic
false-belief vignette's fixed names/objects) so generated scenarios don't
surface-match the textbook paradigm. Everything here is generic household
vocabulary — no real people, brands, or copyrighted text.
"""

ROOMS: list[str] = [
    "kitchen",
    "garage",
    "bedroom",
    "home office",
    "attic",
    "laundry room",
    "pantry",
    "hallway closet",
    "basement",
    "sunroom",
    "workshop",
    "mudroom",
]

CONTAINERS: list[str] = [
    "cardboard box",
    "top drawer",
    "wicker basket",
    "storage bin",
    "wooden chest",
    "filing cabinet",
    "toolbox",
    "backpack",
    "shoe rack",
    "linen cupboard",
    "plastic tote",
    "bookshelf cubby",
]

OBJECTS: list[str] = [
    "flashlight",
    "stapler",
    "umbrella",
    "ball of yarn",
    "board game",
    "camera",
    "watering can",
    "toolkit",
    "sketchbook",
    "coffee mug",
    "spare charger",
    "deck of cards",
    "wrench set",
    "picture frame",
    "yoga mat",
    "tackle box",
    "sewing kit",
    "paint roller",
    "chess set",
    "thermos",
    "binoculars",
    "extension cord",
    "first aid kit",
    "tape measure",
    "guitar tuner",
    "recipe box",
    "gardening gloves",
    "candle",
    "notebook",
    "headlamp",
    "pocketknife",
    "keychain",
    "jar of buttons",
    "roll of stickers",
    "set of dice",
    "compass",
    "hand mirror",
    "spool of wire",
    "bicycle pump",
    "travel mug",
    "puzzle box",
    "harmonica",
    "magnifying glass",
    "clipboard",
    "stopwatch",
    "rain jacket",
    "portable speaker",
    "letter opener",
    "ball of twine",
    "spare batteries",
    "packet of seeds",
]

# NPC name pool: intentionally diverse, deliberately not "Sally"/"Anne".
NAMES: list[str] = [
    "Priya",
    "Marcus",
    "Elena",
    "Kofi",
    "Wren",
    "Diego",
    "Amara",
    "Soren",
    "Nadia",
    "Ibrahim",
    "Yuki",
    "Talia",
    "Rafael",
    "Ines",
    "Oskar",
    "Zara",
    "Lior",
    "Camille",
    "Dmitri",
    "Aisha",
]

# Paraphrase templates for each narrative beat. `{}` slots are filled by the
# generator. Multiple variants per beat so no two scenarios read identically.

PLACE_TEMPLATES: list[str] = [
    "{seeker} puts the {obj} in the {container} in the {room}.",
    "{seeker} sets the {obj} down inside the {container}, in the {room}.",
    "While standing in the {room}, {seeker} places the {obj} into the {container}.",
    "{seeker} tucks the {obj} away in the {container} in the {room}.",
]

SEEKER_LEAVES_TEMPLATES: list[str] = [
    "{seeker} then heads to the {room}.",
    "{seeker} walks off toward the {room}.",
    "A moment later, {seeker} leaves for the {room}.",
    "{seeker} steps out and goes to the {room}.",
]

MOVE_TEMPLATES: list[str] = [
    "While {seeker} is away, someone moves the {obj} from the {container} in the {from_room} to the {container2} in the {to_room}.",
    "With {seeker} out of the room, the {obj} gets moved from the {from_room} to the {to_room}, into the {container2}.",
    "Meanwhile, the {obj} is taken out of the {container} in the {from_room} and placed in the {container2} in the {to_room}.",
    "In {seeker}'s absence, the {obj} is relocated from the {from_room}'s {container} to the {to_room}'s {container2}.",
]

TOLD_TEMPLATES: list[str] = [
    "Someone finds {seeker} in the {room} and mentions that the {obj} is now in the {container2} in the {to_room}.",
    "{seeker} is told, while still in the {room}, that the {obj} has been moved to the {container2} in the {to_room}.",
    "A message reaches {seeker} in the {room}: the {obj} is now in the {to_room}, inside the {container2}.",
    "Before returning, {seeker} learns that the {obj} was moved to the {container2} in the {to_room}.",
]

FILLER_TEMPLATES: list[str] = [
    "{seeker} remains in the {room}, unaware anything has changed.",
    "Nobody tells {seeker}, who stays in the {room} the whole time.",
    "{seeker} is still in the {room} and hears nothing about it.",
    "No word reaches {seeker}, who is occupied in the {room}.",
]

DISTRACTOR_TEMPLATES: list[str] = [
    "Separately, someone tidies the {container3} in the {distractor_room}, moving the {obj2} into the {container4}.",
    "At the same time, the {obj2} is shifted from the {container3} to the {container4} in the {distractor_room}, unrelated to the {obj}'s whereabouts.",
]
