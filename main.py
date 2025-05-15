"""
Vita Game - A text-based adventure game where you play as Vita, a mischievous bunny.
"""

import os
import sys
import json

# Import modules directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the game manager
from modules.game_manager import GameManager

def create_default_templates():
    """Create default templates if they don't exist."""
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Area templates
    area_templates = {
        "park": {
            "type": "Area",
            "name": "Park",
            "description": "A peaceful park with trees and benches.",
            "grid_width": 10,
            "grid_length": 10,
            "weather": "sunny"
        },
        "street": {
            "type": "Area",
            "name": "Street",
            "description": "A busy city street with shops and traffic.",
            "grid_width": 15,
            "grid_length": 5
        },
        "suburbs": {
            "type": "Area",
            "name": "Suburbs",
            "description": "A quiet suburban neighborhood with houses.",
            "grid_width": 20,
            "grid_length": 10
        },
        "house": {
            "type": "Area",
            "name": "House",
            "description": "A cozy house with basic furnishings.",
            "grid_width": 5,
            "grid_length": 5
        },
        "office_building": {
            "type": "Building",
            "name": "Office Building",
            "description": "A tall office building with multiple floors.",
            "grid_width": 8,
            "grid_length": 8,
            "num_floors": 5
        },
        "office_floor": {
            "type": "Area",
            "name": "Office Floor",
            "description": "A floor in an office building with cubicles and offices.",
            "grid_width": 8,
            "grid_length": 8
        }
    }
    
    # Item templates
    item_templates = {
        "carrot": {
            "type": "Food",
            "name": "Carrot",
            "description": "A fresh orange carrot. Good for bunnies!",
            "nutrition": 15,
            "effects": {"energy": 10},
            "value": 5
        },
        "apple": {
            "type": "Food",
            "name": "Apple",
            "description": "A juicy red apple.",
            "nutrition": 20,
            "effects": {"energy": 15},
            "value": 8
        },
        "jetpack": {
            "type": "Jetpack",
            "name": "Jetpack",
            "description": "A high-tech jetpack that allows you to fly.",
            "fuel": 100,
            "max_fuel": 100,
            "fuel_efficiency": 1.0,
            "value": 500
        },
        "metal_scrap": {
            "type": "CraftingIngredient",
            "name": "Metal Scrap",
            "description": "A piece of scrap metal. Useful for crafting.",
            "ingredient_type": "metal",
            "value": 10
        },
        "fabric": {
            "type": "CraftingIngredient",
            "name": "Fabric",
            "description": "A piece of fabric. Useful for crafting.",
            "ingredient_type": "fabric",
            "value": 5
        }
    }
    
    # Object templates
    object_templates = {
        "elevator": {
            "type": "Elevator",
            "name": "Elevator",
            "description": "An elevator that can take you to different floors."
        },
        "car": {
            "type": "Vehicle",
            "name": "Car",
            "description": "A standard car that can be driven around.",
            "speed": 3,
            "fuel": 100,
            "max_fuel": 100
        },
        "door": {
            "type": "Door",
            "name": "Door",
            "description": "A standard door that connects areas."
        },
        "vending_machine": {
            "type": "VendingMachine",
            "name": "Vending Machine",
            "description": "A vending machine selling various items."
        }
    }
    
    # NPC templates
    npc_templates = {
        "squirrel": {
            "name": "Squirrel",
            "description": "A bushy-tailed squirrel looking for acorns.",
            "dialogue": {
                "default": "Squeak! (He seems to be looking for acorns.)",
                "friendly": "Squeak squeak! (He seems happy to see you.)"
            },
            "personality": {
                "nervousness": 70,
                "friendliness": 50
            },
            "money": 10
        },
        "shopkeeper": {
            "name": "Shopkeeper",
            "description": "A friendly shopkeeper selling various goods.",
            "dialogue": {
                "default": "Welcome to my shop! Feel free to browse around.",
                "friendly": "Ah, my favorite customer! What can I get for you today?"
            },
            "personality": {
                "friendliness": 60,
                "greed": 40
            },
            "money": 500
        },
        "police_officer": {
            "name": "Police Officer",
            "description": "A stern-looking police officer keeping the peace.",
            "dialogue": {
                "default": "Move along, citizen. Nothing to see here.",
                "hostile": "You're causing trouble. I'm keeping my eye on you!"
            },
            "personality": {
                "strictness": 80,
                "suspicion": 60
            },
            "money": 100
        },
        "civilian": {
            "name": "Civilian",
            "description": "An ordinary citizen going about their day.",
            "dialogue": {
                "default": "Hello there!",
                "friendly": "Nice to see you again!"
            },
            "personality": {
                "friendliness": 50,
                "curiosity": 40
            },
            "money": 50
        }
    }
    
    # Save templates to files
    with open(os.path.join(data_dir, "area_templates.json"), 'w') as f:
        json.dump(area_templates, f, indent=4)
    
    with open(os.path.join(data_dir, "item_templates.json"), 'w') as f:
        json.dump(item_templates, f, indent=4)
    
    with open(os.path.join(data_dir, "object_templates.json"), 'w') as f:
        json.dump(object_templates, f, indent=4)
    
    with open(os.path.join(data_dir, "npc_templates.json"), 'w') as f:
        json.dump(npc_templates, f, indent=4)

def main():
    """Main function to run the game."""
    # Create default templates if they don't exist
    create_default_templates()
    
    # Create and initialize the game manager
    game_manager = GameManager()
    game_manager.initialize_game()
    
    # Run the game
    game_manager.run()

if __name__ == "__main__":
    main()