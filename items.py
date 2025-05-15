"""
Items module for Vita Game.
Handles all items that can be picked up, used, or interacted with.
"""

import json
from .coordinates import Coordinates

class Item:
    """Base class for all items in the game."""
    def __init__(self, name, description, coordinates=None, edible=False, nutrition=0, 
                 pickupable=True, value=0, effects=None, properties=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.edible = edible
        self.nutrition = nutrition
        self.pickupable = pickupable  # Can the player pick this up?
        self.value = value  # Monetary value (for buying/selling)
        self.effects = effects or {}  # Dictionary of effects when used/consumed
        self.properties = properties or {}  # Custom properties
        self.id = f"item_{name.lower().replace(' ', '_')}"
        
        # Ensure all items are pickupable by default unless explicitly set to False
        if not hasattr(self, 'pickupable'):
            self.pickupable = True
    
    def __str__(self):
        return self.name
    
    def use(self, player):
        """Use the item."""
        print(f"You use the {self.name}.")
        
        # Apply any effects
        for effect_type, effect_value in self.effects.items():
            if effect_type == "energy":
                player.energy = min(player.max_energy, player.energy + effect_value)
                print(f"Your energy increased by {effect_value}.")
            elif effect_type == "street_cred":
                player.street_cred += effect_value
                print(f"Your street cred {'increased' if effect_value > 0 else 'decreased'} by {abs(effect_value)}.")
    
    def set_property(self, key, value):
        """Set a custom property for this item."""
        self.properties[key] = value
    
    def get_property(self, key, default=None):
        """Get a custom property for this item."""
        return self.properties.get(key, default)
    
    def to_dict(self):
        """Convert item to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "edible": self.edible,
            "nutrition": self.nutrition,
            "pickupable": self.pickupable,
            "value": self.value,
            "effects": self.effects,
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create item from dictionary."""
        item = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data["edible"],
            data["nutrition"],
            data["pickupable"],
            data["value"],
            data["effects"],
            data["properties"]
        )
        item.id = data.get("id", item.id)
        return item


class Food(Item):
    """Food item that can be eaten."""
    def __init__(self, name, description, nutrition=10, effects=None, value=5, properties=None):
        super().__init__(
            name, 
            description, 
            edible=True, 
            nutrition=nutrition, 
            value=value,
            effects=effects,
            properties=properties
        )
    
    def effect(self, player):
        """Apply special effect when eaten."""
        for effect_type, effect_value in self.effects.items():
            if effect_type == "energy":
                player.energy = min(player.max_energy, player.energy + effect_value)
                print(f"Your energy increased by {effect_value}.")
            elif effect_type == "street_cred":
                player.street_cred += effect_value
                print(f"Your street cred {'increased' if effect_value > 0 else 'decreased'} by {abs(effect_value)}.")


class Jetpack(Item):
    """Jetpack class representing the jetpack object."""
    def __init__(self, name="Jetpack", description="A high-tech jetpack that allows you to fly.", 
                 fuel=100, max_fuel=100, fuel_efficiency=1.0, value=500, properties=None):
        super().__init__(
            name, 
            description, 
            pickupable=True,  # Jetpacks are always pickupable
            value=value,
            properties=properties
        )
        # Ensure pickupable is always True for jetpacks
        self.pickupable = True
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.fuel_efficiency = fuel_efficiency  # Lower values mean more efficient
    
    def activate(self, player):
        """Activate the jetpack for the player."""
        if self.fuel > 0:
            player.is_flying = True
            print(f"You activate the {self.name} and start flying!")
            return True
        print(f"The {self.name} is out of fuel!")
        return False
    
    def deactivate(self, player):
        """Deactivate the jetpack."""
        if player.is_flying:
            player.is_flying = False
            print(f"You deactivate the {self.name} and land gently.")
    
    def refuel(self, amount=100):
        """Refuel the jetpack."""
        self.fuel = min(self.max_fuel, self.fuel + amount)
        print(f"{self.name} refueled to {self.fuel}%")
    
    def __str__(self):
        return f"{self.name} (Fuel: {self.fuel}%)"
    
    def to_dict(self):
        """Convert jetpack to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "fuel": self.fuel,
            "max_fuel": self.max_fuel,
            "fuel_efficiency": self.fuel_efficiency
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create jetpack from dictionary."""
        jetpack = cls(
            data["name"],
            data["description"],
            data["fuel"],
            data["max_fuel"],
            data["fuel_efficiency"],
            data.get("value", 500),
            data.get("properties", {})
        )
        jetpack.id = data.get("id", jetpack.id)
        return jetpack


class Money(Item):
    """Money item that can be used for transactions."""
    def __init__(self, amount=1):
        super().__init__(
            f"${amount}" if amount == 1 else f"${amount}",
            f"{'A dollar bill' if amount == 1 else f'${amount} in cash'}.",
            value=amount
        )
        self.amount = amount
    
    def to_dict(self):
        """Convert money to dictionary for serialization."""
        data = super().to_dict()
        data["amount"] = self.amount
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create money from dictionary."""
        return cls(data["amount"])


class CraftingIngredient(Item):
    """An item that can be used in crafting recipes."""
    def __init__(self, name, description, ingredient_type, value=5, properties=None):
        super().__init__(
            name, 
            description, 
            pickupable=True,
            value=value,
            properties=properties
        )
        self.ingredient_type = ingredient_type  # e.g., "metal", "wood", "fabric"
    
    def to_dict(self):
        """Convert crafting ingredient to dictionary for serialization."""
        data = super().to_dict()
        data["ingredient_type"] = self.ingredient_type
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create crafting ingredient from dictionary."""
        ingredient = cls(
            data["name"],
            data["description"],
            data["ingredient_type"],
            data.get("value", 5),
            data.get("properties", {})
        )
        ingredient.id = data.get("id", ingredient.id)
        return ingredient


class ItemManager:
    """Manages all items in the game."""
    def __init__(self):
        self.items = {}  # Dictionary mapping item IDs to Item objects
        self.templates = {}  # Dictionary of item templates
    
    def add_item(self, item):
        """Add an item to the manager."""
        self.items[item.id] = item
    
    def get_item(self, item_id):
        """Get an item by ID."""
        return self.items.get(item_id)
    
    def add_template(self, template_id, template_data):
        """Add an item template."""
        self.templates[template_id] = template_data
    
    def create_from_template(self, template_id, **kwargs):
        """Create an item from a template."""
        # Try exact match first
        if template_id in self.templates:
            template_key = template_id
        else:
            # Try case-insensitive match
            template_key = next((k for k in self.templates.keys() 
                               if k.lower() == template_id.lower()), None)
            
            if template_key is None:
                raise ValueError(f"Unknown item template: {template_id}")
        
        template = self.templates[template_key].copy()
        item_type = template.pop("type")
        
        # Override template values with provided kwargs
        template.update(kwargs)
        
        # Create the item based on its type
        if item_type == "Item":
            item = Item(**template)
        elif item_type == "Food":
            item = Food(**template)
        elif item_type == "Jetpack":
            item = Jetpack(**template)
        elif item_type == "Money":
            item = Money(template.get("amount", 1))
        elif item_type == "CraftingIngredient":
            item = CraftingIngredient(**template)
        elif item_type == "Clothing":
            # For clothing items, use the base Item class
            # You could create a Clothing class in the future for more specific functionality
            item = Item(
                template.get("name", "Clothing Item"),
                template.get("description", "A piece of clothing."),
                value=template.get("value", 10)
            )
        else:
            raise ValueError(f"Unknown item type: {item_type}")
        
        # Generate a unique ID if needed
        if "id" in kwargs:
            item.id = kwargs["id"]
        
        return item
    
    def save_to_json(self, filename):
        """Save all items to a JSON file."""
        data = {
            "items": {item_id: item.to_dict() for item_id, item in self.items.items()},
            "templates": self.templates
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_json(self, filename):
        """Load items from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Load templates
        self.templates = data.get("templates", {})
        
        # Load items
        for item_id, item_data in data.get("items", {}).items():
            item_type = item_data.get("type", "Item")
            
            if item_type == "Item":
                item = Item.from_dict(item_data)
            elif item_type == "Food":
                item = Food.from_dict(item_data)
            elif item_type == "Jetpack":
                item = Jetpack.from_dict(item_data)
            elif item_type == "Money":
                item = Money.from_dict(item_data)
            elif item_type == "CraftingIngredient":
                item = CraftingIngredient.from_dict(item_data)
            else:
                print(f"Warning: Unknown item type {item_type}, creating as generic Item")
                item = Item.from_dict(item_data)
            
            self.add_item(item)