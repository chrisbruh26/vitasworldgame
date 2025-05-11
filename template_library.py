"""
Template Library for Vita Game.
This module contains predefined templates for game entities.
"""

from .templates import (
    ItemTemplate, NPCTemplate, GameObjectTemplate, 
    AreaTemplate, ItemRequestQuestTemplate
)
from .vitagame import (
    Area, Item, Food, Jetpack, NPC, GameObject, 
    Transport, Elevator, Coordinates
)
from .quests import ItemRequestQuest

# ===== AREA TEMPLATES =====

PARK_TEMPLATE = AreaTemplate(
    Area,
    "Park",
    "A peaceful park with trees and benches.",
    grid_width=10,
    grid_length=10
)

SKYSCRAPER_FLOOR_TEMPLATE = AreaTemplate(
    Area,
    "Skyscraper Floor",
    "A floor in a tall skyscraper with offices and meeting rooms.",
    grid_width=5,
    grid_length=5
)

APARTMENT_TEMPLATE = AreaTemplate(
    Area,
    "Apartment",
    "A cozy apartment with basic furnishings.",
    grid_width=4,
    grid_length=4
)

STREET_TEMPLATE = AreaTemplate(
    Area,
    "Street",
    "A busy city street with traffic and pedestrians.",
    grid_width=15,
    grid_length=3
)

SHOP_TEMPLATE = AreaTemplate(
    Area,
    "Shop",
    "A small shop selling various goods.",
    grid_width=5,
    grid_length=5
)

# ===== ITEM TEMPLATES =====

CARROT_TEMPLATE = ItemTemplate(
    Food,
    "Carrot",
    "A fresh orange carrot.",
    nutrition=15
)

APPLE_TEMPLATE = ItemTemplate(
    Food,
    "Apple",
    "A juicy red apple.",
    nutrition=20
)

JETPACK_TEMPLATE = ItemTemplate(
    Jetpack,
    "Jetpack",
    "A high-tech jetpack that allows you to fly."
)

ACORN_TEMPLATE = ItemTemplate(
    Item,
    "Acorn",
    "A small acorn that squirrels love to eat."
)

KEY_TEMPLATE = ItemTemplate(
    Item,
    "Key",
    "A metal key that can unlock something."
)

# ===== NPC TEMPLATES =====

SQUIRREL_TEMPLATE = NPCTemplate(
    NPC,
    "Squirrel",
    "A bushy-tailed squirrel looking for acorns.",
    dialogue={
        "default": "Squeak! (He seems to be looking for acorns.)",
        "quest_active": "Squeak squeak! (He's still waiting for those acorns.)",
        "quest_complete": "Squeak! Squeak! (He's very happy with the acorns you gave him!)"
    }
)

SHOPKEEPER_TEMPLATE = NPCTemplate(
    NPC,
    "Shopkeeper",
    "A friendly shopkeeper selling various goods.",
    dialogue={
        "default": "Welcome to my shop! Feel free to browse around.",
        "greeting": "Hello there! Looking for anything specific today?"
    }
)

OFFICE_WORKER_TEMPLATE = NPCTemplate(
    NPC,
    "Office Worker",
    "A busy office worker in formal attire.",
    dialogue={
        "default": "Sorry, I'm really busy right now.",
        "greeting": "Hello! I'd love to chat, but I have a deadline to meet."
    }
)

# ===== GAME OBJECT TEMPLATES =====

TREE_TEMPLATE = GameObjectTemplate(
    GameObject,
    "Tree",
    "A tall oak tree with branches perfect for climbing."
)

BENCH_TEMPLATE = GameObjectTemplate(
    GameObject,
    "Bench",
    "A wooden bench to sit and relax."
)

ELEVATOR_TEMPLATE = GameObjectTemplate(
    Elevator,
    "Elevator",
    "An elevator that can take you to different floors."
)

DESK_TEMPLATE = GameObjectTemplate(
    GameObject,
    "Desk",
    "A wooden desk with drawers."
)

COMPUTER_TEMPLATE = GameObjectTemplate(
    GameObject,
    "Computer",
    "A desktop computer with a large monitor."
)

# ===== QUEST TEMPLATES =====

ACORN_QUEST_TEMPLATE = ItemRequestQuestTemplate(
    "Acorn Collector",
    "Collect 10 acorns for the hungry squirrel.",
    required_item="Acorn",
    quantity=10,
    reward={"street_cred": 5}
)

DELIVERY_QUEST_TEMPLATE = ItemRequestQuestTemplate(
    "Package Delivery",
    "Deliver this package to the recipient.",
    required_item="Package",
    quantity=1,
    reward={"street_cred": 3}
)

# Function to create a customized name for NPCs from templates
def create_named_npc(template, name, **kwargs):
    """Create an NPC with a custom name from a template."""
    npc = template.create(**kwargs)
    npc.name = name
    return npc