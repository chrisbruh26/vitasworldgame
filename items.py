from .coordinates import Coordinates

class Item:
    """Item class representing items in the game world."""
    def __init__(self, name, description, coordinates=None, edible=False, nutrition=0, 
                 pickupable=True, value=0, effects=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.edible = edible
        self.nutrition = nutrition
        self.pickupable = pickupable  # Can the player pick this up?
        self.value = value  # Monetary value (for buying/selling)
        self.effects = effects or {}  # Dictionary of effects when used/consumed
    
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
    
    def to_dict(self):
        """Convert item to dictionary for serialization."""
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "edible": self.edible,
            "nutrition": self.nutrition,
            "pickupable": self.pickupable,
            "value": self.value,
            "effects": self.effects
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
            data["effects"]
        )
        return item


class Food(Item):
    """Food item that can be eaten."""
    def __init__(self, name, description, nutrition=10, effects=None):
        super().__init__(name, description, edible=True, nutrition=nutrition, effects=effects)
    
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
    """JetPack class representing the jetpack object."""
    def __init__(self, name="Jetpack", description="A high-tech jetpack that allows you to fly.", 
                 fuel=100, max_fuel=100, fuel_efficiency=1.0):
        super().__init__(name, description)
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.fuel_efficiency = fuel_efficiency  # Lower values mean more efficient
    
    def activate(self, player):
        """Activate the jetpack for the player."""
        if self.fuel > 0:
            player.is_flying = True
            return True
        return False
    
    def refuel(self, amount=100):
        """Refuel the jetpack."""
        self.fuel = min(self.max_fuel, self.fuel + amount)
        print(f"Jetpack refueled to {self.fuel}%")
    
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
            data["fuel_efficiency"]
        )
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


class Vehicle(Item):
    """Base class for vehicles that can be driven."""
    def __init__(self, name, description, speed=1, fuel=100, max_fuel=100):
        super().__init__(name, description, pickupable=False)
        self.speed = speed  # Movement multiplier
        self.fuel = fuel
        self.max_fuel = max_fuel
    
    def drive(self, player, direction, distance=1):
        """Drive the vehicle in a direction."""
        if self.fuel <= 0:
            print(f"The {self.name} is out of fuel!")
            return False
        
        # Consume fuel
        fuel_used = distance / self.speed
        self.fuel -= fuel_used
        if self.fuel < 0:
            self.fuel = 0
        
        print(f"You drive the {self.name} {direction}.")
        # The actual movement logic would be handled by the player or game engine
        return True
    
    def refuel(self, amount=100):
        """Refuel the vehicle."""
        self.fuel = min(self.max_fuel, self.fuel + amount)
        print(f"{self.name} refueled to {self.fuel}%")
    
    def to_dict(self):
        """Convert vehicle to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "speed": self.speed,
            "fuel": self.fuel,
            "max_fuel": self.max_fuel
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create vehicle from dictionary."""
        vehicle = cls(
            data["name"],
            data["description"],
            data["speed"],
            data["fuel"],
            data["max_fuel"]
        )
        return vehicle


# Factory function to create items from templates
def create_item_from_template(template_name, **kwargs):
    """Create an item from a predefined template with optional overrides."""
    templates = {
        "carrot": {
            "class": Food,
            "name": "Carrot",
            "description": "A fresh orange carrot. Bunnies love these!",
            "nutrition": 15,
            "effects": {"energy": 10}
        },
        "jetpack": {
            "class": Jetpack,
            "name": "Jetpack",
            "description": "A high-tech jetpack that allows you to fly.",
            "fuel": 100,
            "max_fuel": 100,
            "fuel_efficiency": 1.0
        },
        "acorn": {
            "class": Food,
            "name": "Acorn",
            "description": "A small acorn, perfect for planting.",
            "nutrition": 5,
            "effects": {"energy": 3}
        },
        "golden_acorn": {
            "class": Food,
            "name": "Golden Acorn",
            "description": "A rare golden acorn! It looks valuable.",
            "nutrition": 20,
            "effects": {"energy": 15, "street_cred": 5},
            "value": 50
        },
        "dollar": {
            "class": Money,
            "amount": 1
        },
        "car": {
            "class": Vehicle,
            "name": "Car",
            "description": "A standard car that can be driven around.",
            "speed": 3,
            "fuel": 100,
            "max_fuel": 100
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown item template: {template_name}")
    
    template = templates[template_name].copy()
    item_class = template.pop("class")
    
    # Override template values with provided kwargs
    template.update(kwargs)
    
    return item_class(**template)