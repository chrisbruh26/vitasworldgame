from .coordinates import Coordinates

class GameObject:
    """Base class for all game objects that can be interacted with."""
    def __init__(self, name, description, coordinates=None, properties=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.properties = properties or {}  # Custom properties
    
    def interact(self, player):
        """Base interaction method."""
        print(f"You interact with the {self.name}.")
    
    def to_dict(self):
        """Convert game object to dictionary for serialization."""
        return {
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
        data["destination"] = self.destination.name if self.destination else None
        data["destination_coords"] = self.destination_coords
        return data


class Elevator(Transport):
    """Elevator class for vertical transportation between floors."""
    def __init__(self, name="Elevator", description="An elevator that can take you to different floors.", coordinates=None):
        super().__init__(name, description, coordinates)
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
    
    def to_dict(self):
        """Convert elevator to dictionary for serialization."""
        data = super().to_dict()
        data["floors"] = {k: (v[0].name, v[1], v[2]) for k, v in self.floors.items()}
        data["current_floor"] = self.current_floor
        return data


class Door(GameObject):
    """Door class for connecting areas."""
    def __init__(self, name="Door", description="A door that leads somewhere.", coordinates=None, locked=False, key_name=None):
        super().__init__(name, description, coordinates)
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
        data["destination"] = self.destination.name if self.destination else None
        data["destination_coords"] = self.destination_coords
        return data


class Vehicle(GameObject):
    """Vehicle class for player-drivable vehicles."""
    def __init__(self, name, description, coordinates=None, speed=1, fuel=100, max_fuel=100):
        super().__init__(name, description, coordinates)
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
        # The actual movement logic would be handled by the player or game engine
        return True
        
    def refuel(self, amount=100):
        """Refuel the vehicle."""
        self.fuel = min(self.max_fuel, self.fuel + amount)
        print(f"{self.name} refueled to {self.fuel}%")
        
    def interact(self, player):
        """Interact with the vehicle."""
        if self.player_inside:
            exit_choice = input(f"You are in the {self.name}. Exit? (yes/no): ").lower()
            if exit_choice == "yes":
                self.exit(player)
        else:
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


class Computer(GameObject):
    """Computer class for interactive terminals."""
    def __init__(self, name="Computer", description="A computer terminal.", coordinates=None, password=None):
        super().__init__(name, description, coordinates)
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


# Factory function to create game objects from templates
def create_object_from_template(template_name, **kwargs):
    """Create a game object from a predefined template with optional overrides."""
    templates = {
        "elevator": {
            "class": Elevator,
            "name": "Elevator",
            "description": "An elevator that can take you to different floors."
        },
        "door": {
            "class": Door,
            "name": "Door",
            "description": "A standard door.",
            "locked": False
        },
        "locked_door": {
            "class": Door,
            "name": "Locked Door",
            "description": "A locked door that requires a key.",
            "locked": True,
            "key_name": "Key"
        },
        "car": {
            "class": Vehicle,
            "name": "Car",
            "description": "A standard car that can be driven around.",
            "speed": 3,
            "fuel": 100,
            "max_fuel": 100
        },
        "helicopter": {
            "class": Vehicle,
            "name": "Helicopter",
            "description": "A helicopter that can fly to distant locations.",
            "speed": 5,
            "fuel": 200,
            "max_fuel": 200
        },
        "computer": {
            "class": Computer,
            "name": "Computer",
            "description": "A computer terminal with various programs."
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown object template: {template_name}")
    
    template = templates[template_name].copy()
    obj_class = template.pop("class")
    
    # Override template values with provided kwargs
    template.update(kwargs)
    
    return obj_class(**template)