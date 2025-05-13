"""
Game Objects module for Vita Game.
Handles all interactive objects in the game world.
"""

import json
from .coordinates import Coordinates

class GameObject:
    """Base class for all game objects that can be interacted with."""
    def __init__(self, name, description, coordinates=None, properties=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.properties = properties or {}  # Custom properties
        self.id = f"obj_{name.lower().replace(' ', '_')}"
    
    def interact(self, player):
        """Base interaction method."""
        print(f"You interact with the {self.name}.")
    
    def set_property(self, key, value):
        """Set a custom property for this object."""
        self.properties[key] = value
    
    def get_property(self, key, default=None):
        """Get a custom property for this object."""
        return self.properties.get(key, default)
    
    def to_dict(self):
        """Convert game object to dictionary for serialization."""
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "properties": self.properties
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create game object from dictionary."""
        obj = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data["properties"]
        )
        obj.id = data.get("id", obj.id)
        return obj


class Transport(GameObject):
    """Base class for objects that provide transportation for the player."""
    def __init__(self, name, description, coordinates=None, properties=None):
        super().__init__(name, description, coordinates, properties)
        self.destination = None  # Where this transport leads to
        self.destination_coords = (0, 0, 0)  # Grid coordinates in the destination area
        
    def set_destination(self, area, grid_x=0, grid_y=0, grid_z=0):
        """Set the destination for this transport."""
        self.destination = area
        self.destination_coords = (grid_x, grid_y, grid_z)
        print(f"{self.name} will take you to {area.name} at position ({grid_x}, {grid_y}, {grid_z}).")
        
    def use(self, player):
        """Use the transport to travel to its destination."""
        if self.destination:
            grid_x, grid_y, grid_z = self.destination_coords
            player.set_current_area(self.destination, grid_x, grid_y)
            # Update z-coordinate if needed
            if grid_z != 0:
                player.coordinates.z = self.destination.coordinates.z + grid_z
            print(f"You travel to {self.destination.name}.")
        else:
            print(f"{self.name} has no destination set.")
    
    def to_dict(self):
        """Convert transport to dictionary for serialization."""
        data = super().to_dict()
        data["destination"] = self.destination.id if self.destination else None
        data["destination_coords"] = self.destination_coords
        return data
    
    @classmethod
    def from_dict(cls, data, area_resolver=None):
        """Create transport from dictionary."""
        transport = super().from_dict(data)
        
        # Resolve destination if area_resolver is provided
        if area_resolver and data.get("destination"):
            transport.destination = area_resolver(data["destination"])
            transport.destination_coords = data.get("destination_coords", (0, 0, 0))
        
        return transport


class Elevator(Transport):
    """Elevator class for vertical transportation between floors."""
    def __init__(self, name="Elevator", description="An elevator that can take you to different floors.", coordinates=None, properties=None):
        super().__init__(name, description, coordinates, properties)
        self.floors = {}  # Dictionary mapping floor numbers to (area, grid_x, grid_y) tuples
        self.current_floor = 1
        
    def add_floor(self, floor_number, area, grid_x=0, grid_y=0):
        """Add a floor to the elevator's destinations."""
        self.floors[floor_number] = (area, grid_x, grid_y)
        print(f"Floor {floor_number} added: {area.name}")
        
    def go_to_floor(self, floor_number, player):
        """Take the player to a specific floor."""
        if floor_number in self.floors:
            area, grid_x, grid_y = self.floors[floor_number]
            self.current_floor = floor_number
            print(f"The elevator moves to floor {floor_number}.")
            player.set_current_area(area, grid_x, grid_y)
            return True
        else:
            print(f"There is no floor {floor_number} button in this elevator.")
            return False
            
    def interact(self, player):
        """Interact with the elevator."""
        if not self.floors:
            print("This elevator doesn't seem to go anywhere.")
            return
            
        print(f"You're in the elevator. Current floor: {self.current_floor}")
        print("Available floors:")
        for floor in sorted(self.floors.keys()):
            area, _, _ = self.floors[floor]
            print(f"- Floor {floor}: {area.name}")
        
        floor_choice = input("Enter floor number (or 'cancel'): ")
        if floor_choice.lower() == 'cancel':
            print("You decide not to use the elevator.")
            return
        
        try:
            floor_number = int(floor_choice)
            self.go_to_floor(floor_number, player)
        except ValueError:
            print("That's not a valid floor number.")
    
    def to_dict(self):
        """Convert elevator to dictionary for serialization."""
        data = super().to_dict()
        data["floors"] = {k: (v[0].id, v[1], v[2]) for k, v in self.floors.items()}
        data["current_floor"] = self.current_floor
        return data
    
    @classmethod
    def from_dict(cls, data, area_resolver=None):
        """Create elevator from dictionary."""
        elevator = super().from_dict(data, area_resolver)
        elevator.current_floor = data.get("current_floor", 1)
        
        # Resolve floors if area_resolver is provided
        if area_resolver and "floors" in data:
            for floor_num, floor_data in data["floors"].items():
                area_id, grid_x, grid_y = floor_data
                area = area_resolver(area_id)
                if area:
                    elevator.floors[int(floor_num)] = (area, grid_x, grid_y)
        
        return elevator


class Door(GameObject):
    """Door class for connecting areas."""
    def __init__(self, name="Door", description="A door that leads somewhere.", coordinates=None, locked=False, key_name=None, properties=None):
        super().__init__(name, description, coordinates, properties)
        self.locked = locked
        self.key_name = key_name  # Name of the item needed to unlock
        self.destination = None
        self.destination_coords = (0, 0, 0)
        
    def set_destination(self, area, grid_x=0, grid_y=0):
        """Set the destination for this door."""
        self.destination = area
        self.destination_coords = (grid_x, grid_y, 0)
        
    def unlock(self, player):
        """Try to unlock the door."""
        if not self.locked:
            print("The door is already unlocked.")
            return True
            
        if not self.key_name:
            print("This door doesn't seem to have a lock.")
            self.locked = False
            return True
            
        key = next((i for i in player.inventory if i.name.lower() == self.key_name.lower()), None)
        if key:
            print(f"You use the {key.name} to unlock the door.")
            self.locked = False
            return True
        else:
            print(f"You need a {self.key_name} to unlock this door.")
            return False
            
    def interact(self, player):
        """Interact with the door."""
        if self.locked:
            print(f"The {self.name} is locked.")
            unlock_attempt = input("Try to unlock? (yes/no): ").lower()
            if unlock_attempt == "yes":
                if self.unlock(player) and self.destination:
                    self.use(player)
        elif self.destination:
            self.use(player)
        else:
            print(f"The {self.name} doesn't seem to lead anywhere.")
            
    def use(self, player):
        """Use the door to travel to its destination."""
        if self.locked:
            print(f"The {self.name} is locked.")
            return
            
        if self.destination:
            grid_x, grid_y, _ = self.destination_coords
            player.set_current_area(self.destination, grid_x, grid_y)
            print(f"You go through the {self.name} to {self.destination.name}.")
        else:
            print(f"The {self.name} doesn't seem to lead anywhere.")
    
    def to_dict(self):
        """Convert door to dictionary for serialization."""
        data = super().to_dict()
        data["locked"] = self.locked
        data["key_name"] = self.key_name
        data["destination"] = self.destination.id if self.destination else None
        data["destination_coords"] = self.destination_coords
        return data
    
    @classmethod
    def from_dict(cls, data, area_resolver=None):
        """Create door from dictionary."""
        door = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data.get("locked", False),
            data.get("key_name"),
            data.get("properties", {})
        )
        door.id = data.get("id", door.id)
        
        # Resolve destination if area_resolver is provided
        if area_resolver and data.get("destination"):
            door.destination = area_resolver(data["destination"])
            door.destination_coords = data.get("destination_coords", (0, 0, 0))
        
        return door


class Vehicle(GameObject):
    """Vehicle class for player-drivable vehicles."""
    def __init__(self, name, description, coordinates=None, speed=1, fuel=100, max_fuel=100, properties=None):
        super().__init__(name, description, coordinates, properties)
        self.speed = speed  # Movement multiplier
        self.fuel = fuel
        self.max_fuel = max_fuel
        self.player_inside = False
        
    def enter(self, player):
        """Enter the vehicle."""
        self.player_inside = True
        print(f"You enter the {self.name}.")
        
    def exit(self, player):
        """Exit the vehicle."""
        self.player_inside = False
        print(f"You exit the {self.name}.")
        
    def drive(self, player, direction, distance=1):
        """Drive the vehicle in a direction."""
        if not self.player_inside:
            print(f"You need to enter the {self.name} first.")
            return False
            
        if self.fuel <= 0:
            print(f"The {self.name} is out of fuel!")
            return False
        
        # Consume fuel
        fuel_used = distance / self.speed
        self.fuel -= fuel_used
        if self.fuel < 0:
            self.fuel = 0
        
        print(f"You drive the {self.name} {direction}.")
        
        # Get current grid position
        grid_x, grid_y, grid_z = player.get_grid_position()
        new_x, new_y = grid_x, grid_y
        
        # Calculate new position based on direction
        if direction.lower() in ["north", "forward"]:
            new_y += distance
        elif direction.lower() in ["south", "backward"]:
            new_y -= distance
        elif direction.lower() in ["east", "right"]:
            new_x += distance
        elif direction.lower() in ["west", "left"]:
            new_x -= distance
        else:
            print(f"Unknown direction: {direction}")
            return False
        
        # Check if new position is within area bounds
        if 0 <= new_x < player.current_area.grid_width and 0 <= new_y < player.current_area.grid_length:
            # Update player and vehicle coordinates
            player.coordinates.x = player.current_area.coordinates.x + new_x
            player.coordinates.y = player.current_area.coordinates.y + new_y
            self.coordinates.x = player.coordinates.x
            self.coordinates.y = player.coordinates.y
            
            # Check for objects at the new position
            objects_here = player.current_area.get_objects_at(new_x, new_y, grid_z)
            if objects_here:
                print("You see:")
                for obj in objects_here:
                    if obj != self:  # Don't list the vehicle itself
                        print(f"- {obj.name}: {obj.description}")
                        
            return True
        else:
            # Check if there's a connection in this direction
            if direction.lower() in player.current_area.connections:
                connected_area = player.current_area.connections[direction.lower()]
                # Determine entry point on the other side
                entry_x, entry_y = 0, 0
                if direction.lower() == "north":
                    entry_y = 0  # Enter from the south side
                    entry_x = grid_x  # Keep the same x-coordinate
                elif direction.lower() == "south":
                    entry_y = connected_area.grid_length - 1  # Enter from the north side
                    entry_x = grid_x  # Keep the same x-coordinate
                elif direction.lower() == "east":
                    entry_x = 0  # Enter from the west side
                    entry_y = grid_y  # Keep the same y-coordinate
                elif direction.lower() == "west":
                    entry_x = connected_area.grid_width - 1  # Enter from the east side
                    entry_y = grid_y  # Keep the same y-coordinate
                
                # Move to the connected area
                player.set_current_area(connected_area, entry_x, entry_y)
                # Update vehicle coordinates
                self.coordinates.x = player.coordinates.x
                self.coordinates.y = player.coordinates.y
                self.coordinates.z = player.coordinates.z
                # Add vehicle to new area
                connected_area.add_object(self)
                return True
            else:
                print(f"You can't drive {direction} from here. You've reached the edge of {player.current_area.name}.")
                return False
        
    def refuel(self, amount=100):
        """Refuel the vehicle."""
        self.fuel = min(self.max_fuel, self.fuel + amount)
        print(f"{self.name} refueled to {self.fuel}%")
        
    def interact(self, player):
        """Interact with the vehicle."""
        if self.player_inside:
            print(f"You are in the {self.name}.")
            print(f"Fuel: {self.fuel}/{self.max_fuel}")
            print("Options:")
            print("1. Drive")
            print("2. Exit vehicle")
            
            choice = input("What would you like to do? ")
            if choice == "1":
                direction = input("Which direction? (north/south/east/west): ").lower()
                self.drive(player, direction)
            elif choice == "2":
                self.exit(player)
            else:
                print("Invalid choice.")
        else:
            print(f"You see a {self.name}.")
            enter_choice = input(f"Enter the {self.name}? (yes/no): ").lower()
            if enter_choice == "yes":
                self.enter(player)
    
    def to_dict(self):
        """Convert vehicle to dictionary for serialization."""
        data = super().to_dict()
        data["speed"] = self.speed
        data["fuel"] = self.fuel
        data["max_fuel"] = self.max_fuel
        data["player_inside"] = self.player_inside
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create vehicle from dictionary."""
        vehicle = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data.get("speed", 1),
            data.get("fuel", 100),
            data.get("max_fuel", 100),
            data.get("properties", {})
        )
        vehicle.id = data.get("id", vehicle.id)
        vehicle.player_inside = data.get("player_inside", False)
        return vehicle


class Computer(GameObject):
    """Computer class for interactive terminals."""
    def __init__(self, name="Computer", description="A computer terminal.", coordinates=None, password=None, properties=None):
        super().__init__(name, description, coordinates, properties)
        self.password = password
        self.logged_in = False
        self.programs = {}  # Dictionary of available programs
        
    def login(self, password_attempt):
        """Try to log in to the computer."""
        if not self.password or password_attempt == self.password:
            self.logged_in = True
            print("Login successful.")
            return True
        else:
            print("Incorrect password.")
            return False
            
    def logout(self):
        """Log out of the computer."""
        self.logged_in = False
        print("Logged out.")
        
    def add_program(self, name, function):
        """Add a program to the computer."""
        self.programs[name] = function
        
    def run_program(self, name, player):
        """Run a program on the computer."""
        if not self.logged_in:
            print("You need to log in first.")
            return
            
        if name in self.programs:
            self.programs[name](player)
        else:
            print(f"Program '{name}' not found.")
            
    def interact(self, player):
        """Interact with the computer."""
        print(f"You sit down at the {self.name}.")
        
        if not self.logged_in and self.password:
            password_attempt = input("Enter password (or leave blank to cancel): ")
            if not password_attempt:
                print("Login cancelled.")
                return
            if not self.login(password_attempt):
                return
        elif not self.logged_in:
            self.logged_in = True
            print("Computer unlocked.")
            
        while self.logged_in:
            print("\nAvailable programs:")
            for program in self.programs:
                print(f"- {program}")
            print("- logout")
            
            choice = input("\nEnter program name (or 'logout' to exit): ").lower()
            if choice == "logout":
                self.logout()
                break
            elif choice in self.programs:
                self.run_program(choice, player)
            else:
                print(f"Program '{choice}' not found.")
    
    def to_dict(self):
        """Convert computer to dictionary for serialization."""
        data = super().to_dict()
        data["password"] = self.password
        data["logged_in"] = self.logged_in
        # We can't serialize functions, so we'll just store program names
        data["programs"] = list(self.programs.keys())
        return data


class VendingMachine(GameObject):
    """Vending machine that sells items."""
    def __init__(self, name="Vending Machine", description="A vending machine selling various items.", coordinates=None, properties=None):
        super().__init__(name, description, coordinates, properties)
        self.items = {}  # Dictionary mapping item IDs to (item, price) tuples
        
    def add_item(self, item, price=None):
        """Add an item to the vending machine."""
        if price is None:
            price = item.value * 1.5  # Default markup
        self.items[item.id] = (item, price)
        
    def buy_item(self, item_id, player):
        """Player buys an item from the vending machine."""
        if item_id not in self.items:
            print("That item is not available.")
            return False
            
        item, price = self.items[item_id]
        if player.money < price:
            print(f"You don't have enough money. The {item.name} costs ${price}.")
            return False
            
        # Create a new instance of the item for the player
        new_item = type(item)(item.name, item.description)
        if hasattr(item, 'nutrition'):
            new_item.nutrition = item.nutrition
        if hasattr(item, 'effects'):
            new_item.effects = item.effects.copy()
            
        player.money -= price
        player.add_item(new_item)
        print(f"You bought {item.name} for ${price}.")
        return True
        
    def interact(self, player):
        """Interact with the vending machine."""
        print(f"You approach the {self.name}.")
        print(f"Your money: ${player.money}")
        print("\nAvailable items:")
        
        if not self.items:
            print("The vending machine is empty.")
            return
            
        for i, (item_id, (item, price)) in enumerate(self.items.items(), 1):
            print(f"{i}. {item.name}: ${price}")
            
        choice = input("\nEnter item number to buy (or 'cancel'): ")
        if choice.lower() == 'cancel':
            print("You decide not to buy anything.")
            return
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(self.items):
                item_id = list(self.items.keys())[index]
                self.buy_item(item_id, player)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")
    
    def to_dict(self):
        """Convert vending machine to dictionary for serialization."""
        data = super().to_dict()
        data["items"] = {item_id: (item.id, price) for item_id, (item, price) in self.items.items()}
        return data
    
    @classmethod
    def from_dict(cls, data, item_resolver=None):
        """Create vending machine from dictionary."""
        vending_machine = super().from_dict(data)
        
        # Resolve items if item_resolver is provided
        if item_resolver and "items" in data:
            for item_id, (item_ref_id, price) in data["items"].items():
                item = item_resolver(item_ref_id)
                if item:
                    vending_machine.items[item_id] = (item, price)
        
        return vending_machine


class GameObjectManager:
    """Manages all game objects in the game."""
    def __init__(self):
        self.objects = {}  # Dictionary mapping object IDs to GameObject objects
        self.templates = {}  # Dictionary of object templates
    
    def add_object(self, obj):
        """Add an object to the manager."""
        self.objects[obj.id] = obj
    
    def get_object(self, obj_id):
        """Get an object by ID."""
        return self.objects.get(obj_id)
    
    def add_template(self, template_id, template_data):
        """Add an object template."""
        self.templates[template_id] = template_data
    
    def create_from_template(self, template_id, **kwargs):
        """Create an object from a template."""
        if template_id not in self.templates:
            raise ValueError(f"Unknown object template: {template_id}")
        
        template = self.templates[template_id].copy()
        obj_type = template.pop("type")
        
        # Override template values with provided kwargs
        template.update(kwargs)
        
        # Create the object based on its type
        if obj_type == "GameObject":
            obj = GameObject(**template)
        elif obj_type == "Transport":
            obj = Transport(**template)
        elif obj_type == "Elevator":
            obj = Elevator(**template)
        elif obj_type == "Door":
            obj = Door(**template)
        elif obj_type == "Vehicle":
            obj = Vehicle(**template)
        elif obj_type == "Computer":
            obj = Computer(**template)
        elif obj_type == "VendingMachine":
            obj = VendingMachine(**template)
        else:
            raise ValueError(f"Unknown object type: {obj_type}")
        
        # Generate a unique ID if needed
        if "id" in kwargs:
            obj.id = kwargs["id"]
        
        return obj
    
    def save_to_json(self, filename):
        """Save all objects to a JSON file."""
        data = {
            "objects": {obj_id: obj.to_dict() for obj_id, obj in self.objects.items()},
            "templates": self.templates
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_json(self, filename, area_resolver=None, item_resolver=None):
        """Load objects from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Load templates
        self.templates = data.get("templates", {})
        
        # Load objects
        for obj_id, obj_data in data.get("objects", {}).items():
            obj_type = obj_data.get("type", "GameObject")
            
            if obj_type == "GameObject":
                obj = GameObject.from_dict(obj_data)
            elif obj_type == "Transport":
                obj = Transport.from_dict(obj_data, area_resolver)
            elif obj_type == "Elevator":
                obj = Elevator.from_dict(obj_data, area_resolver)
            elif obj_type == "Door":
                obj = Door.from_dict(obj_data, area_resolver)
            elif obj_type == "Vehicle":
                obj = Vehicle.from_dict(obj_data)
            elif obj_type == "Computer":
                obj = Computer.from_dict(obj_data)
            elif obj_type == "VendingMachine":
                obj = VendingMachine.from_dict(obj_data, item_resolver)
            else:
                print(f"Warning: Unknown object type {obj_type}, creating as generic GameObject")
                obj = GameObject.from_dict(obj_data)
            
            self.add_object(obj)