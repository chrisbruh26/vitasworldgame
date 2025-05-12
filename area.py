from .coordinates import Coordinates
from .items import Item

class Area:
    """Area class representing different locations in the game world."""
    def __init__(self, name, description, coordinates=None, height=1, grid_width=10, grid_length=10):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.height = height  # How tall this area is (for buildings)
        self.grid_width = grid_width  # Width of the area grid (x-axis)
        self.grid_length = grid_length  # Length of the area grid (y-axis)
        self.connections = {}
        self.items = []
        self.npcs = []
        self.objects = []
        # Dictionary to store objects by their coordinates within the area
        # Format: {(x, y, z): [list of objects at this position]}
        self.grid_objects = {}
        # Area-specific properties
        self.properties = {}
        # Weather and time of day
        self.weather = "clear"
        self.time_of_day = "day"

    def add_connection(self, direction, area):
        """Add a connection to another area."""
        self.connections[direction] = area
        # Add reverse connection if it doesn't exist
        reverse_directions = {
            "north": "south", "south": "north", 
            "east": "west", "west": "east",
            "up": "down", "down": "up"
        }
        if direction in reverse_directions and reverse_directions[direction] not in area.connections:
            area.connections[reverse_directions[direction]] = self

    def add_item(self, item):
        """Add an item to the area."""
        self.items.append(item)
        
        # If the item has coordinates, also add it to the grid
        if hasattr(item, 'coordinates'):
            # Get relative coordinates within this area
            rel_x, rel_y, rel_z = self.get_relative_coordinates(item.coordinates)
            if 0 <= rel_x < self.grid_width and 0 <= rel_y < self.grid_length:
                self.place_object_at(item, rel_x, rel_y, rel_z)

    def remove_item(self, item_name):
        """Remove an item from the area."""
        item = next((i for i in self.items if i.name.lower() == item_name.lower()), None)
        if item:
            self.items.remove(item)
            
            # Also remove from grid if present
            rel_x, rel_y, rel_z = self.get_relative_coordinates(item.coordinates)
            self.remove_object_from_grid(item, rel_x, rel_y, rel_z)
            
            return item
        return None
    
    def add_npc(self, npc):
        """Add an NPC to the area."""
        self.npcs.append(npc)
        npc.location = self
        
        # If the NPC has coordinates, also add it to the grid
        if hasattr(npc, 'coordinates'):
            # Get relative coordinates within this area
            rel_x, rel_y, rel_z = self.get_relative_coordinates(npc.coordinates)
            if 0 <= rel_x < self.grid_width and 0 <= rel_y < self.grid_length:
                self.place_object_at(npc, rel_x, rel_y, rel_z)
    
    def remove_npc(self, npc):
        """Remove an NPC from the area."""
        if npc in self.npcs:
            self.npcs.remove(npc)
            
            # Also remove from grid if present
            rel_x, rel_y, rel_z = self.get_relative_coordinates(npc.coordinates)
            self.remove_object_from_grid(npc, rel_x, rel_y, rel_z)
            
            npc.location = None
    
    def add_object(self, obj):
        """Add an object to the area."""
        self.objects.append(obj)
        
        # If the object has coordinates, also add it to the grid
        if hasattr(obj, 'coordinates'):
            # Get relative coordinates within this area
            rel_x, rel_y, rel_z = self.get_relative_coordinates(obj.coordinates)
            if 0 <= rel_x < self.grid_width and 0 <= rel_y < self.grid_length:
                self.place_object_at(obj, rel_x, rel_y, rel_z)
    
    def remove_object(self, obj_name):
        """Remove an object from the area."""
        obj = next((o for o in self.objects if o.name.lower() == obj_name.lower()), None)
        if obj:
            self.objects.remove(obj)
            
            # Also remove from grid if present
            rel_x, rel_y, rel_z = self.get_relative_coordinates(obj.coordinates)
            self.remove_object_from_grid(obj, rel_x, rel_y, rel_z)
            
            return obj
        return None
    
    def __str__(self):
        return f"{self.name} at {self.coordinates}"
        
    def place_object_at(self, obj, x, y, z=0):
        """Place an object at specific coordinates within the area grid."""
        # Ensure coordinates are within grid bounds
        if 0 <= x < self.grid_width and 0 <= y < self.grid_length:
            # Update object's coordinates
            obj.coordinates = Coordinates(
                self.coordinates.x + x,  # Global x coordinate
                self.coordinates.y + y,  # Global y coordinate
                self.coordinates.z + z   # Global z coordinate
            )
            
            # Store object in grid_objects dictionary
            grid_key = (x, y, z)
            if grid_key not in self.grid_objects:
                self.grid_objects[grid_key] = []
            self.grid_objects[grid_key].append(obj)
            
            # Add to appropriate list based on object type
            if hasattr(obj, '__class__') and obj.__class__.__name__ == 'Item' and obj not in self.items:
                self.items.append(obj)
            elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'NPC' and obj not in self.npcs:
                self.npcs.append(obj)
                obj.location = self
            elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'GameObject' and obj not in self.objects:
                self.objects.append(obj)
                
            return True
        else:
            print(f"Cannot place {obj.name} at ({x}, {y}, {z}): coordinates out of bounds.")
            return False
            
    def get_objects_at(self, x, y, z=0):
        """Get all objects at specific coordinates within the area grid."""
        return self.grid_objects.get((x, y, z), [])
        
    def remove_object_from_grid(self, obj, x, y, z=0):
        """Remove an object from specific coordinates within the area grid."""
        grid_key = (x, y, z)
        if grid_key in self.grid_objects and obj in self.grid_objects[grid_key]:
            self.grid_objects[grid_key].remove(obj)
            if not self.grid_objects[grid_key]:  # If list is empty
                del self.grid_objects[grid_key]
            return True
        return False
        
    def get_relative_coordinates(self, global_coords):
        """Convert global coordinates to grid-relative coordinates."""
        return (
            global_coords.x - self.coordinates.x,
            global_coords.y - self.coordinates.y,
            global_coords.z - self.coordinates.z
        )
    
    def set_property(self, key, value):
        """Set a property for this area."""
        self.properties[key] = value
    
    def get_property(self, key, default=None):
        """Get a property for this area."""
        return self.properties.get(key, default)
    
    def set_weather(self, weather):
        """Set the weather for this area."""
        self.weather = weather
        print(f"The weather in {self.name} changes to {weather}.")
    
    def set_time_of_day(self, time_of_day):
        """Set the time of day for this area."""
        self.time_of_day = time_of_day
        print(f"The time in {self.name} changes to {time_of_day}.")
    
    def to_dict(self):
        """Convert area to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "height": self.height,
            "grid_width": self.grid_width,
            "grid_length": self.grid_length,
            "connections": {k: v.name for k, v in self.connections.items()},  # Just store names, resolve later
            "properties": self.properties,
            "weather": self.weather,
            "time_of_day": self.time_of_day
        }
    
    @classmethod
    def from_dict(cls, data, item_resolver=None, npc_resolver=None):
        """Create area from dictionary."""
        area = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data["height"],
            data["grid_width"],
            data["grid_length"]
        )
        area.properties = data["properties"]
        area.weather = data["weather"]
        area.time_of_day = data["time_of_day"]
        
        # Connections need to be resolved after all areas are created
        # This would be handled by a game loader
        
        return area


class Building(Area):
    """A special type of area that represents a building with multiple floors."""
    def __init__(self, name, description, coordinates=None, num_floors=1, **kwargs):
        super().__init__(name, description, coordinates, **kwargs)
        self.num_floors = num_floors
        self.floors = {}  # Dictionary mapping floor numbers to areas
        
    def add_floor(self, floor_number, area):
        """Add a floor to the building."""
        self.floors[floor_number] = area
        # Set the floor's coordinates based on the building's coordinates and floor number
        area.coordinates = Coordinates(
            self.coordinates.x,
            self.coordinates.y,
            self.coordinates.z + (floor_number - 1) * area.height
        )
        
    def get_floor(self, floor_number):
        """Get a floor area by floor number."""
        return self.floors.get(floor_number)
    
    def to_dict(self):
        """Convert building to dictionary for serialization."""
        data = super().to_dict()
        data["num_floors"] = self.num_floors
        data["floors"] = {k: v.name for k, v in self.floors.items()}  # Just store names, resolve later
        return data


# Factory function to create areas from templates
def create_area_from_template(template_name, **kwargs):
    """Create an area from a predefined template with optional overrides."""
    templates = {
        "park": {
            "class": Area,
            "name": "Park",
            "description": "A beautiful park with trees, some low hills, and a fountain.",
            "coordinates": Coordinates(0, 0, 0),
            "grid_width": 15,
            "grid_length": 15,
            "weather": "sunny",
            "time_of_day": "day"
        },
        "house": {
            "class": Area,
            "name": "House",
            "description": "A cozy little house with a small garden.",
            "coordinates": Coordinates(0, 10, 0),
            "height": 2,
            "grid_width": 8,
            "grid_length": 8
        },
        "street": {
            "class": Area,
            "name": "Street",
            "description": "A busy street with shops and cafes.",
            "coordinates": Coordinates(10, 0, 0),
            "grid_width": 20,
            "grid_length": 5
        },
        "skyscraper": {
            "class": Building,
            "name": "Skyscraper",
            "description": "A tall skyscraper with many floors.",
            "coordinates": Coordinates(20, 20, 0),
            "num_floors": 50,
            "height": 50,
            "grid_width": 10,
            "grid_length": 10
        },
        "mall": {
            "class": Building,
            "name": "Shopping Mall",
            "description": "A large shopping mall with multiple stores.",
            "coordinates": Coordinates(30, 30, 0),
            "num_floors": 3,
            "height": 10,
            "grid_width": 30,
            "grid_length": 30
        },
        "airport": {
            "class": Area,
            "name": "Airport",
            "description": "A busy airport with planes and helicopters.",
            "coordinates": Coordinates(50, 50, 0),
            "grid_width": 50,
            "grid_length": 50
        },
        "farm": {
            "class": Area,
            "name": "Farm",
            "description": "A peaceful farm with crops and animals.",
            "coordinates": Coordinates(-20, -20, 0),
            "grid_width": 30,
            "grid_length": 30,
            "weather": "clear"
        },
        "casino": {
            "class": Area,
            "name": "Casino",
            "description": "A flashy casino full of games and opportunities to win or lose money.",
            "coordinates": Coordinates(40, 10, 0),
            "grid_width": 20,
            "grid_length": 20,
            "time_of_day": "night"
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown area template: {template_name}")
    
    template = templates[template_name].copy()
    area_class = template.pop("class")
    
    # Handle coordinates specially
    if "coordinates" in template and isinstance(template["coordinates"], Coordinates):
        coords = template.pop("coordinates")
        if "coordinates" in kwargs:
            # Use provided coordinates
            coords = kwargs.pop("coordinates")
        template["coordinates"] = coords
    
    # Override template values with provided kwargs
    template.update(kwargs)
    
    return area_class(**template)