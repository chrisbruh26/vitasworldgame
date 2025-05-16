"""
Item module for the game.
Handles all items that can be picked up, used, or interacted with.
"""

from .coordinates import Coordinates

class Item:
    """Base class for all items in the game."""
    def __init__(self, name, description, coordinates=None, pickupable=True, value=0):
        self.name = name
        self.description = description
        # Global coordinates of the item if it's in an area, None if in inventory
        self.coordinates = coordinates 
        self.pickupable = pickupable
        self.value = value # For potential future use with money system
        self.id = f"item_{name.lower().replace(' ', '_')}"

    def __str__(self):
        return self.name

    def clone(self):
        """Creates a new instance of this item (a copy)."""
        return Item(
            name=self.name,
            description=self.description,
            coordinates=None, # Cloned item is not in the world initially
            pickupable=self.pickupable,
            value=self.value
        )

    def to_dict(self):
        """Convert item to dictionary for serialization (future use)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "pickupable": self.pickupable,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data):
        """Create item from dictionary (future use)."""
        coords = Coordinates.from_dict(data["coordinates"]) if data["coordinates"] else None
        return cls(
            data["name"],
            data["description"],
            coordinates=coords,
            pickupable=data.get("pickupable", True),
            value=data.get("value", 0)
        )

class ItemManager:
    """Manages all items in the game (simplified for now)."""
    def __init__(self):
        self.items_master_list = {} # Stores all created items by ID for reference
        # For now, we'll create items directly. Templates can be added later.