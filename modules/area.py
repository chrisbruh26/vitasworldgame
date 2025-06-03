"""
Area module for the game.
Handles game world areas and their connections.
"""

from .coordinates import Coordinates

class Area:
    """Area class representing different locations in the game world."""
    def __init__(self, name, description, area_origin_coords=None, grid_width=10, grid_length=10):
        self.name = name
        self.description = description
        # The global coordinates of the (0,0) point of this area's grid
        self.area_origin_coords = area_origin_coords if area_origin_coords else Coordinates(0, 0, 0)
        self.grid_width = grid_width
        self.grid_length = grid_length
        self.connections = {}  # direction_str -> connected_Area_object
        
        # For objects within the area's grid
        # Key: (grid_x, grid_y), Value: list of objects (Item or NPC instances)
        self.grid_objects = {} 
        self.items = [] # List of Item instances physically in this area
        self.npcs = []  # List of NPC instances physically in this area
        self.id = f"area_{name.lower().replace(' ', '_')}"
        # For shops: item_name.lower() -> {'prototype': Item_instance, 'price': float, 'stock': int}
        # The 'prototype' is used to create new items when sold.
        self.associated_stock_symbol = None # For linking area to a stock market symbol
        self.is_shelter = False # Flag to indicate if this area is a good place to hide
        self.shop_stock = {}


    def add_connection(self, direction, connected_area):
        """Add a connection to another area and a reverse connection."""
        self.connections[direction.lower()] = connected_area
        reverse_directions = {
            "north": "south", "south": "north",
            "east": "west", "west": "east",
            "up": "down", "down": "up" # For potential future use
        }
        if direction.lower() in reverse_directions:
            reverse_dir = reverse_directions[direction.lower()]
            if reverse_dir not in connected_area.connections: # Avoid infinite recursion
                connected_area.add_connection(reverse_dir, self)

    def is_valid_grid_position(self, grid_x, grid_y):
        """Check if the given grid coordinates are within the area's bounds."""
        return 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_length

    def get_global_coordinates(self, grid_x, grid_y, grid_z=0):
        """Convert local grid coordinates to global world coordinates."""
        return Coordinates(
            self.area_origin_coords.x + grid_x,
            self.area_origin_coords.y + grid_y,
            self.area_origin_coords.z + grid_z # Assuming items/NPCs are at base Z of area for now
        )

    def get_relative_coordinates(self, global_coords):
        """Convert global world coordinates to local grid coordinates."""
        return (
            global_coords.x - self.area_origin_coords.x,
            global_coords.y - self.area_origin_coords.y,
            global_coords.z - self.area_origin_coords.z
        )

    def add_object_to_grid(self, obj, grid_x, grid_y):
        """Adds an object (Item or NPC) to a specific grid cell and updates its global coords."""
        if not self.is_valid_grid_position(grid_x, grid_y):
            print(f"Warning: Cannot place {obj.name} at ({grid_x},{grid_y}) in {self.name}. Out of bounds.")
            return

        obj.coordinates = self.get_global_coordinates(grid_x, grid_y)
        
        grid_pos = (grid_x, grid_y)
        if grid_pos not in self.grid_objects:
            self.grid_objects[grid_pos] = []
        
        if obj not in self.grid_objects[grid_pos]:
            self.grid_objects[grid_pos].append(obj)

        # Add to specific lists if not already present
        from .item import Item # Avoid circular import at module level
        from .npc import NPC
        if isinstance(obj, Item) and obj not in self.items:
            self.items.append(obj)
        elif isinstance(obj, NPC) and obj not in self.npcs:
            self.npcs.append(obj)
            obj.location = self

    def remove_object_from_grid(self, obj, grid_x, grid_y):
        """Removes an object from a specific grid cell."""
        grid_pos = (grid_x, grid_y)
        if grid_pos in self.grid_objects and obj in self.grid_objects[grid_pos]:
            self.grid_objects[grid_pos].remove(obj)
            if not self.grid_objects[grid_pos]: # If list is empty, delete key
                del self.grid_objects[grid_pos]

        # Also remove from specific lists
        from .item import Item
        from .npc import NPC
        if isinstance(obj, Item) and obj in self.items:
            self.items.remove(obj)
        elif isinstance(obj, NPC) and obj in self.npcs:
            self.npcs.remove(obj)
            # obj.location = None # Handled by NPC.set_location or when NPC moves areas

    def get_objects_at_grid_cell(self, grid_x, grid_y):
        """Get all objects at a specific grid cell."""
        return self.grid_objects.get((grid_x, grid_y), [])

    def __str__(self):
        return f"{self.name} (Origin: {self.area_origin_coords}, Size: {self.grid_width}x{self.grid_length})"

    # --- Shop-specific methods ---
    def add_item_to_shop(self, item_prototype, price, quantity):
        """
        Adds an item type to the shop's for-sale stock.
        :param item_prototype: An instance of the Item to be used as a template.
        :param price: The selling price of the item.
        :param quantity: How many units are in stock (can be float('inf')).
        """
        self.shop_stock[item_prototype.name.lower()] = {
            'prototype': item_prototype,
            'price': price,
            'stock': quantity
        }
        print(f"Added {item_prototype.name} to {self.name}'s shop stock. Price: ${price}, Stock: {quantity}")

    def get_shop_listing(self):
        """Returns a list of strings describing items for sale."""
        if not self.shop_stock:
            return []
        listing = []
        for name, details in self.shop_stock.items():
            stock_info = "Unlimited" if details['stock'] == float('inf') else str(details['stock'])
            listing.append(f"- {details['prototype'].name}: ${details['price']:.2f} (Stock: {stock_info})")
        return listing

    def process_purchase(self, item_name_query, buyer_money):
        """
        Processes a purchase if possible.
        Returns the item instance and its price if successful, else (None, 0).
        """
        item_details = self.shop_stock.get(item_name_query.lower())
        if not item_details:
            return None, 0 # Item not found
        if item_details['stock'] <= 0:
            return None, 0 # Out of stock
        if buyer_money < item_details['price']:
            return None, 0 # Cannot afford

        item_details['stock'] -= 1
        return item_details['prototype'].clone(), item_details['price']

class AreaManager:
    """Manages all areas in the game world."""
    def __init__(self):
        self.areas = {}  # area_id -> Area_object

    def add_area(self, area):
        """Add an area to the manager."""
        if area.id in self.areas:
            print(f"Warning: Area with ID '{area.id}' already exists. Overwriting.")
        self.areas[area.id] = area

    def get_area(self, area_id_or_name):
        """Get an area by its ID or case-insensitive name."""
        if area_id_or_name in self.areas:
            return self.areas[area_id_or_name]
        for area in self.areas.values():
            if area.name.lower() == area_id_or_name.lower():
                return area
        return None
    
    def get_area_by_id(self, area_id):
        """Get an area by its exact ID."""
        return self.areas.get(area_id)

    def connect_areas(self, area1_id, direction, area2_id):
        """Connect two areas in the specified direction."""
        area1 = self.get_area(area1_id)
        area2 = self.get_area(area2_id)
        if area1 and area2:
            area1.add_connection(direction, area2)
            return True
        print(f"Error connecting areas: One or both not found ('{area1_id}', '{area2_id}')")
        return False