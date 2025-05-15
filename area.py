"""
Area module for Vita Game.
Handles game world areas and their connections.
"""

import json
import inspect
from .coordinates import Coordinates

class Area:
    """Area class representing different locations in the game world."""
    def __init__(self, name, description, coordinates=None, height=1, grid_width=10, grid_length=10, 
                 weather="clear", time_of_day="day", properties=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.height = height  # How tall this area is (for buildings)
        self.grid_width = grid_width  # Width of the area grid (x-axis)
        self.grid_length = grid_length  # Length of the area grid (y-axis)
        self.connections = {}  # Direction -> Area connections
        self.items = []  # Items in the area
        self.npcs = []  # NPCs in the area
        self.objects = []  # Game objects in the area
        # Dictionary to store objects by their coordinates within the area
        # Format: {(x, y, z): [list of objects at this position]}
        self.grid_objects = {}
        # Area-specific properties
        self.properties = properties or {}
        # Weather and time of day
        self.weather = weather
        self.time_of_day = time_of_day
        # Area ID for reference in connections
        self.id = f"{name.lower().replace(' ', '_')}"

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
            # Check if object is an Item by looking at its class hierarchy
            if hasattr(obj, 'pickupable') and obj not in self.items:
                # If it has a 'pickupable' attribute, it's an item
                self.items.append(obj)
            elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'NPC' and obj not in self.npcs:
                self.npcs.append(obj)
                obj.location = self
            elif hasattr(obj, '__class__') and obj.__class__.__name__ in ['GameObject', 'Transport', 'Elevator', 'Vehicle', 'Door'] and obj not in self.objects:
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
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "height": self.height,
            "grid_width": self.grid_width,
            "grid_length": self.grid_length,
            "connections": {k: v.id for k, v in self.connections.items()},  # Store area IDs
            "properties": self.properties,
            "weather": self.weather,
            "time_of_day": self.time_of_day
        }
    
    @classmethod
    def from_dict(cls, data, area_resolver=None):
        """Create area from dictionary."""
        area = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data["height"],
            data["grid_width"],
            data["grid_length"],
            data["weather"],
            data["time_of_day"],
            data["properties"]
        )
        area.id = data.get("id", area.id)
        
        # Connections need to be resolved after all areas are created
        # This would be handled by a game loader
        if area_resolver and "connections" in data:
            for direction, area_id in data["connections"].items():
                connected_area = area_resolver(area_id)
                if connected_area:
                    area.connections[direction] = connected_area
        
        return area


class Building(Area):
    """A special type of area that represents a building with multiple floors."""
    def __init__(self, name, description, coordinates=None, num_floors=1, height=1, grid_width=10, grid_length=10, 
                 weather="clear", time_of_day="day", properties=None):
        super().__init__(name, description, coordinates, height, grid_width, grid_length, 
                         weather, time_of_day, properties)
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
        data["floors"] = {k: v.id for k, v in self.floors.items()}  # Store area IDs
        return data
    
    @classmethod
    def from_dict(cls, data, area_resolver=None):
        """Create building from dictionary."""
        building = super().from_dict(data, area_resolver)
        building.num_floors = data.get("num_floors", 1)
        
        # Floors need to be resolved after all areas are created
        if area_resolver and "floors" in data:
            for floor_num, area_id in data["floors"].items():
                floor_area = area_resolver(area_id)
                if floor_area:
                    building.floors[int(floor_num)] = floor_area
        
        return building


class AreaManager:
    """Manages all areas in the game world."""
    def __init__(self):
        self.areas = {}  # Dictionary mapping area IDs to Area objects
        self.templates = {}  # Dictionary mapping template IDs to template data
        
    def add_area(self, area):
        """Add an area to the manager."""
        self.areas[area.id] = area
        
    def get_area(self, area_id):
        """Get an area by ID."""
        return self.areas.get(area_id)
    
    def connect_areas(self, area1_id, direction, area2_id):
        """Connect two areas in the specified direction."""
        area1 = self.get_area(area1_id)
        area2 = self.get_area(area2_id)
        if area1 and area2:
            area1.add_connection(direction, area2)
            return True
        return False
    
    def create_area_from_template(self, template_id, coordinates=None, custom_name=None, custom_description=None, properties=None):
        """Create an area from a template."""
        if template_id not in self.templates:
            print(f"Template '{template_id}' not found.")
            return None
            
        template = self.templates[template_id]
        area_type = template.get("type", "Area")
        
        # Set coordinates if provided, otherwise use default (0,0,0)
        coords = coordinates if coordinates else Coordinates(0, 0, 0)
        
        # Use custom name/description if provided, otherwise use template values
        name = custom_name if custom_name else template.get("name", "Unnamed Area")
        description = custom_description if custom_description else template.get("description", "No description.")
        
        # Merge template properties with custom properties
        merged_properties = template.get("properties", {}).copy()
        if properties:
            merged_properties.update(properties)
            
        if area_type == "Building":
            area = Building(
                name,
                description,
                coords,
                template.get("num_floors", 1),
                template.get("height", 1),
                template.get("grid_width", 10),
                template.get("grid_length", 10),
                template.get("weather", "clear"),
                template.get("time_of_day", "day"),
                merged_properties
            )
        else:
            area = Area(
                name,
                description,
                coords,
                template.get("height", 1),
                template.get("grid_width", 10),
                template.get("grid_length", 10),
                template.get("weather", "clear"),
                template.get("time_of_day", "day"),
                merged_properties
            )
            
        # Add the area to the manager
        self.add_area(area)
        return area
        
    def save_to_json(self, filename):
        """Save all areas to a JSON file."""
        data = {area_id: area.to_dict() for area_id, area in self.areas.items()}
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_json(self, filename):
        """Load areas from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # First pass: Create all areas
        for area_id, area_data in data.items():
            if area_data.get("num_floors", 0) > 0:
                area = Building.from_dict(area_data)
            else:
                area = Area.from_dict(area_data)
            self.add_area(area)
        
        # Second pass: Resolve connections
        for area_id, area_data in data.items():
            area = self.get_area(area_id)
            if "connections" in area_data:
                for direction, connected_area_id in area_data["connections"].items():
                    connected_area = self.get_area(connected_area_id)
                    if connected_area:
                        area.connections[direction] = connected_area
            
            # Resolve building floors
            if isinstance(area, Building) and "floors" in area_data:
                for floor_num, floor_area_id in area_data["floors"].items():
                    floor_area = self.get_area(floor_area_id)
                    if floor_area:
                        area.floors[int(floor_num)] = floor_area