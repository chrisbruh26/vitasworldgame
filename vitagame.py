# version 1 of the vita game, which will eventually be turned into a web-based game
# This is a text-based open-world game inspired by Goat Simulator but with a bunny protagonist

class Coordinates:
    """Represents a position in the 3D game world."""
    def __init__(self, x=0, y=0, z=0):
        self.x = x  # East-West position
        self.y = y  # North-South position
        self.z = z  # Height/Elevation
    
    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"
    
    def distance_to(self, other_coords):
        """Calculate horizontal distance to another coordinate."""
        return ((self.x - other_coords.x) ** 2 + (self.y - other_coords.y) ** 2) ** 0.5
    
    def height_difference(self, other_coords):
        """Calculate vertical distance to another coordinate."""
        return abs(self.z - other_coords.z)


class Item:
    """Item class representing items in the game world."""
    def __init__(self, name, description, coordinates=None, edible=False, nutrition=0):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.edible = edible
        self.nutrition = nutrition

    def __str__(self):
        return self.name
    
    def use(self, player):
        """Use the item."""
        print(f"You use the {self.name}.")


class Food(Item):
    """Food item that can be eaten."""
    def __init__(self, name, description, nutrition=10, effect=None):
        super().__init__(name, description, edible=True, nutrition=nutrition)
        self.effect_function = effect
    
    def effect(self, player):
        """Apply special effect when eaten."""
        if self.effect_function:
            self.effect_function(player)


class Jetpack(Item):
    """JetPack class representing the jetpack object."""
    def __init__(self):
        super().__init__("Jetpack", "A high-tech jetpack that allows you to fly.")
        self.fuel = 100
        self.max_fuel = 100
    
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


class Player:
    """Player class for the Vita game."""
    def __init__(self):
        self.name = "Vita"
        self.street_cred = 0
        self.inventory = []
        self.current_area = None
        self.coordinates = Coordinates(0, 0, 0)
        self.jetpack = None
        self.is_flying = False
        self.energy = 100
        self.max_energy = 100
        self.hunger = 0
        
    def set_current_area(self, area, grid_x=0, grid_y=0):
        """Set the current area for the player."""
        self.current_area = area
        # Update player coordinates to match area entrance coordinates plus grid position
        self.coordinates = Coordinates(
            area.coordinates.x + grid_x,
            area.coordinates.y + grid_y,
            area.coordinates.z
        )
        print(f"You are now in {area.name}. {area.description}")
        self.look_around()
    
    def look_around(self):
        """Look around the current area."""
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        print(f"You are at position ({grid_x}, {grid_y}) in {self.current_area.name}.")
        
        # Display available directions for movement within the grid
        print("You can move:")
        if grid_y < self.current_area.grid_length - 1:
            print("- north/forward")
        if grid_y > 0:
            print("- south/backward")
        if grid_x < self.current_area.grid_width - 1:
            print("- east/right")
        if grid_x > 0:
            print("- west/left")
        
        # Display area connections (exits to other areas)
        if self.current_area.connections:
            print("Area exits:")
            for direction, area in self.current_area.connections.items():
                print(f"- {direction} to {area.name}")
        
        # Display objects at the current position
        objects_here = self.current_area.get_objects_at(grid_x, grid_y, grid_z)
        if objects_here:
            print("At your position:")
            for obj in objects_here:
                print(f"- {obj.name}: {obj.description}")
        
        # Display items in the area
        if self.current_area.items:
            print("Items in this area:")
            for item in self.current_area.items:
                # Get the relative position of the item
                item_rel_x = item.coordinates.x - self.current_area.coordinates.x
                item_rel_y = item.coordinates.y - self.current_area.coordinates.y
                # Only show items that are visible (in the same area)
                if 0 <= item_rel_x < self.current_area.grid_width and 0 <= item_rel_y < self.current_area.grid_length:
                    direction = self.get_relative_direction(grid_x, grid_y, item_rel_x, item_rel_y)
                    print(f"- {item.name}: {item.description} ({direction})")
        
        # Display NPCs in the area
        if self.current_area.npcs:
            print("People in this area:")
            for npc in self.current_area.npcs:
                # Get the relative position of the NPC
                npc_rel_x = npc.coordinates.x - self.current_area.coordinates.x
                npc_rel_y = npc.coordinates.y - self.current_area.coordinates.y
                # Only show NPCs that are visible (in the same area)
                if 0 <= npc_rel_x < self.current_area.grid_width and 0 <= npc_rel_y < self.current_area.grid_length:
                    direction = self.get_relative_direction(grid_x, grid_y, npc_rel_x, npc_rel_y)
                    print(f"- {npc.name}: {npc.description} ({direction})")
        
        # Display objects in the area
        if self.current_area.objects:
            print("Objects in this area:")
            for obj in self.current_area.objects:
                # Get the relative position of the object
                obj_rel_x = obj.coordinates.x - self.current_area.coordinates.x
                obj_rel_y = obj.coordinates.y - self.current_area.coordinates.y
                # Only show objects that are visible (in the same area)
                if 0 <= obj_rel_x < self.current_area.grid_width and 0 <= obj_rel_y < self.current_area.grid_length:
                    # Skip objects at the current position (already displayed above)
                    if obj_rel_x == grid_x and obj_rel_y == grid_y:
                        continue
                    direction = self.get_relative_direction(grid_x, grid_y, obj_rel_x, obj_rel_y)
                    print(f"- {obj.name}: {obj.description} ({direction})")
    
    def get_relative_direction(self, from_x, from_y, to_x, to_y):
        """Get the relative direction from one position to another."""
        if from_x == to_x and from_y == to_y:
            return "here"
            
        directions = []
        if to_y > from_y:
            directions.append("north")
        elif to_y < from_y:
            directions.append("south")
            
        if to_x > from_x:
            directions.append("east")
        elif to_x < from_x:
            directions.append("west")
            
        distance = int(((to_x - from_x) ** 2 + (to_y - from_y) ** 2) ** 0.5)
        if distance == 1:
            proximity = "adjacent"
        elif distance <= 3:
            proximity = "nearby"
        else:
            proximity = "in the distance"
            
        return f"{' '.join(directions)} {proximity}"

    def add_item(self, item):
        """Add an item to the player's inventory."""
        self.inventory.append(item)
        print(f"You have picked up {item.name}.")
        
        # Special handling for jetpack
        if item.name.lower() == "jetpack":
            self.jetpack = item
            print("You can now fly by activating your jetpack!")

    def remove_item(self, item_name):
        """Remove an item from the player's inventory."""
        item = next((i for i in self.inventory if i.name.lower() == item_name.lower()), None)
        if item:
            self.inventory.remove(item)
            print(f"You have dropped {item.name}.")
            
            # Special handling for jetpack
            if item.name.lower() == "jetpack" and self.jetpack == item:
                self.jetpack = None
                self.is_flying = False
                print("You can no longer fly without your jetpack!")
            
            # Add the item to the current area
            if self.current_area:
                self.current_area.add_item(item)
        else:
            print(f"You don't have {item_name} in your inventory.")
    
    def activate_jetpack(self):
        """Activate the jetpack to fly."""
        if not self.jetpack:
            print("You don't have a jetpack!")
            return False
        
        if self.jetpack.fuel <= 0:
            print("Your jetpack is out of fuel!")
            return False
        
        self.is_flying = True
        print("Whoosh! Your jetpack activates and you start flying!")
        return True
    
    def deactivate_jetpack(self):
        """Deactivate the jetpack."""
        if self.is_flying:
            self.is_flying = False
            print("You deactivate your jetpack and land gently.")
            # Make sure player is at ground level of current area
            self.coordinates.z = self.current_area.coordinates.z
    
    def fly(self, direction, distance=1):
        """Fly in a direction using the jetpack."""
        if not self.is_flying:
            print("You need to activate your jetpack first!")
            return False
        
        if self.jetpack.fuel <= 0:
            print("Your jetpack runs out of fuel!")
            self.is_flying = False
            return False
        
        # Consume fuel
        self.jetpack.fuel -= distance
        if self.jetpack.fuel < 0:
            self.jetpack.fuel = 0
        
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        new_x, new_y, new_z = grid_x, grid_y, grid_z
        
        # Move in the specified direction
        if direction.lower() == "up":
            new_z += distance
            print(f"You fly upward to elevation {self.current_area.coordinates.z + new_z}.")
        elif direction.lower() == "down":
            if grid_z - distance < 0:
                # Don't go below ground level
                new_z = 0
                print("You descend to ground level.")
            else:
                new_z -= distance
                print(f"You fly downward to elevation {self.current_area.coordinates.z + new_z}.")
        elif direction.lower() == "north" or direction.lower() == "forward":
            new_y += distance
            print(f"You fly north.")
        elif direction.lower() == "south" or direction.lower() == "backward":
            new_y -= distance
            print(f"You fly south.")
        elif direction.lower() == "east" or direction.lower() == "right":
            new_x += distance
            print(f"You fly east.")
        elif direction.lower() == "west" or direction.lower() == "left":
            new_x -= distance
            print(f"You fly west.")
        else:
            print(f"Unknown direction: {direction}")
            return False
        
        # Check if new position is within area bounds
        if 0 <= new_x < self.current_area.grid_width and 0 <= new_y < self.current_area.grid_length:
            # Update player coordinates
            self.coordinates.x = self.current_area.coordinates.x + new_x
            self.coordinates.y = self.current_area.coordinates.y + new_y
            self.coordinates.z = self.current_area.coordinates.z + new_z
            
            # Check for objects at the new position
            objects_here = self.current_area.get_objects_at(new_x, new_y, new_z)
            if objects_here:
                print("You see:")
                for obj in objects_here:
                    print(f"- {obj.name}: {obj.description}")
                    
            return True
        else:
            # Check if there's a connection in this direction
            if direction.lower() in self.current_area.connections:
                connected_area = self.current_area.connections[direction.lower()]
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
                self.set_current_area(connected_area, entry_x, entry_y)
                # Maintain flying elevation
                self.coordinates.z = connected_area.coordinates.z + grid_z
                return True
            else:
                print(f"You can't fly {direction} from here. You've reached the edge of {self.current_area.name}.")
                return False
    
    def eat(self, item_name):
        """Eat an item from inventory."""
        item = next((i for i in self.inventory if i.name.lower() == item_name.lower()), None)
        if not item:
            print(f"You don't have {item_name} to eat.")
            return
        
        if hasattr(item, 'edible') and item.edible:
            self.hunger = max(0, self.hunger - item.nutrition)
            self.inventory.remove(item)
            print(f"You eat the {item.name}. Yum!")
            if hasattr(item, 'effect'):
                item.effect(self)
        else:
            print(f"You can't eat the {item.name}!")
            
    def get_grid_position(self):
        """Get the player's position relative to the current area's grid."""
        if not self.current_area:
            return None
        
        rel_x = self.coordinates.x - self.current_area.coordinates.x
        rel_y = self.coordinates.y - self.current_area.coordinates.y
        rel_z = self.coordinates.z - self.current_area.coordinates.z
        
        return (rel_x, rel_y, rel_z)
    
    def move(self, direction, distance=1):
        """Move the player in a direction within the current area's grid."""
        if not self.current_area:
            print("You're not in any area.")
            return False
            
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        new_x, new_y = grid_x, grid_y
        
        # Calculate new position based on direction
        if direction.lower() == "north" or direction.lower() == "forward":
            new_y += distance
        elif direction.lower() == "south" or direction.lower() == "backward":
            new_y -= distance
        elif direction.lower() == "east" or direction.lower() == "right":
            new_x += distance
        elif direction.lower() == "west" or direction.lower() == "left":
            new_x -= distance
        else:
            print(f"Unknown direction: {direction}")
            return False
            
        # Check if new position is within area bounds
        if 0 <= new_x < self.current_area.grid_width and 0 <= new_y < self.current_area.grid_length:
            # Update player coordinates
            self.coordinates.x = self.current_area.coordinates.x + new_x
            self.coordinates.y = self.current_area.coordinates.y + new_y
            
            # Describe the movement
            print(f"You move {direction}.")
            
            # Check for objects at the new position
            objects_here = self.current_area.get_objects_at(new_x, new_y, grid_z)
            if objects_here:
                print("You see:")
                for obj in objects_here:
                    print(f"- {obj.name}: {obj.description}")
                    
            return True
        else:
            # Check if there's a connection in this direction
            if direction.lower() in self.current_area.connections:
                connected_area = self.current_area.connections[direction.lower()]
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
                self.set_current_area(connected_area, entry_x, entry_y)
                return True
            else:
                print(f"You can't go {direction} from here. You've reached the edge of {self.current_area.name}.")
                return False
                
    def examine_surroundings(self):
        """Examine the immediate surroundings in the current grid position."""
        if not self.current_area:
            print("You're not in any area.")
            return
            
        grid_x, grid_y, grid_z = self.get_grid_position()
        print(f"You are at position ({grid_x}, {grid_y}) in {self.current_area.name}.")
        
        # Check for objects at the current position
        objects_here = self.current_area.get_objects_at(grid_x, grid_y, grid_z)
        if objects_here:
            print("You see:")
            for obj in objects_here:
                print(f"- {obj.name}: {obj.description}")
        else:
            print("There's nothing of interest at your current position.")


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

    def remove_item(self, item_name):
        """Remove an item from the area."""
        item = next((i for i in self.items if i.name.lower() == item_name.lower()), None)
        if item:
            self.items.remove(item)
            return item
        return None
    
    def add_npc(self, npc):
        """Add an NPC to the area."""
        self.npcs.append(npc)
        npc.location = self
    
    def remove_npc(self, npc):
        """Remove an NPC from the area."""
        if npc in self.npcs:
            self.npcs.remove(npc)
            npc.location = None
    
    def add_object(self, obj):
        """Add an object to the area."""
        self.objects.append(obj)
    
    def remove_object(self, obj_name):
        """Remove an object from the area."""
        obj = next((o for o in self.objects if o.name.lower() == obj_name.lower()), None)
        if obj:
            self.objects.remove(obj)
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
            if isinstance(obj, Item) and obj not in self.items:
                self.items.append(obj)
            elif isinstance(obj, NPC) and obj not in self.npcs:
                self.npcs.append(obj)
                obj.location = self
            elif isinstance(obj, GameObject) and obj not in self.objects:
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


class GameObject:
    """Base class for all game objects that can be interacted with."""
    def __init__(self, name, description, coordinates=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
    
    def interact(self, player):
        """Base interaction method."""
        print(f"You interact with the {self.name}.")

class Transport(GameObject):
    """Base class for objects that provide transportation for the player."""
    # This class can include cars, which will be controllable by the player
    def __init__(self, name, description, coordinates=None):
        super().__init__(name, description, coordinates)
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
            
        # In a real game, you would handle floor selection here
        # For now, we'll just print the options


class NPC:
    """NPC class representing non-player characters in the game world."""
    def __init__(self, name, description, coordinates=None, dialogue=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.location = None
        self.dialogue = dialogue if dialogue else {"default": "Hello there!"}
        self.quest = None

    def set_location(self, area):
        """Set the location of the NPC."""
        if self.location:
            self.location.remove_npc(self)
        self.location = area
        area.add_npc(self)
        # Update NPC coordinates to match area
        self.coordinates = Coordinates(area.coordinates.x, area.coordinates.y, area.coordinates.z)

    def remove_location(self):
        """Remove the NPC from its current location."""
        if self.location:
            self.location.remove_npc(self)
            self.location = None
    
    def talk(self, player):
        """Talk to the NPC."""
        if self.quest and self.quest.is_completed:
            if self.name == "Jeff":
                print(f"{self.name} waves silently while quietly nibbling on an acorn.")
            else:
                print(f"{self.name}: {self.dialogue.get('quest_complete', 'Thank you for your help!')}")
        elif self.quest and self.quest.is_active:
            print(f"{self.name}: {self.quest.get_status()}")
        else:
            print(f"{self.name}: {self.dialogue.get('default')}")
    
    def assign_quest(self, quest):
        """Assign a quest to this NPC."""
        self.quest = quest
        quest.giver = self


class Quest:
    """Quest class for side missions."""
    def __init__(self, name, description, objective, reward=None):
        self.name = name
        self.description = description
        self.objective = objective  # Function that checks if quest is completed
        self.reward = reward
        self.is_active = False
        self.is_completed = False
        self.giver = None
    
    def start(self, player):
        """Start the quest."""
        self.is_active = True
        print(f"Quest started: {self.name}")
        print(self.description)
    
    def check_completion(self, player):
        """Check if the quest is completed."""
        if self.objective(player):
            self.complete(player)
            return True
        return False
    
    def complete(self, player):
        """Complete the quest and give rewards."""
        self.is_completed = True
        print(f"Quest completed: {self.name}")
        if self.reward:
            self.reward(player)
    
    def get_status(self):
        """Get the current status of the quest."""
        if self.is_completed:
            return f"You've already completed my quest. Thank you!"
        elif self.is_active:
            return f"Have you completed my quest yet? {self.description}"
        else:
            return f"I have a quest for you: {self.description} Will you accept it?"


# set up items and add them to areas
def create_areas(): 
    """Create areas and set up their connections."""
    # Create areas with coordinates
    park = Area("Park", "A beautiful park with trees, some low hills, and a fountain.", Coordinates(0, 0, 0))
    house = Area("House", "A cozy little house with a small garden.", Coordinates(0, 10, 0), height=2)
    street = Area("Street", "A busy street with shops and cafes.", Coordinates(10, 0, 0))
    alley = Area("Alley", "A dark alley with a shady vibe.", Coordinates(15, 5, 0))
    rooftop = Area("Rooftop", "A high rooftop with a great view of the city.", Coordinates(0, 10, 2))
    
    # Tall building
    skyscraper_lobby = Area("Skyscraper Lobby", "The grand entrance to a massive skyscraper.", Coordinates(20, 20, 0), height=50)
    skyscraper_mid = Area("Skyscraper Mid-Level", "The middle floor of the skyscraper with offices.", Coordinates(20, 20, 25))
    skyscraper_top = Area("Skyscraper Top", "The top floor with an observation deck.", Coordinates(20, 20, 50))

    # Set up connections
    park.add_connection("north", house)
    park.add_connection("east", street)
    street.add_connection("north", alley)
    house.add_connection("up", rooftop)  # Can go up to the rooftop from the house
    
    # Skyscraper connections
    street.add_connection("northeast", skyscraper_lobby)
    skyscraper_lobby.add_connection("southwest", street)
    skyscraper_lobby.add_connection("up", skyscraper_mid)
    skyscraper_mid.add_connection("up", skyscraper_top)

    # Add items to areas
    park.add_item(Item("Bench", "A wooden bench to sit on."))
    acorn = Item("Acorn", "A small acorn, perfect for planting.", edible=True, nutrition=5)
    
    for i in range(3):
        street.add_item(acorn)
        skyscraper_top.add_item(acorn)
        
    park.add_item(Jetpack())
    
    house.add_item(Item("Key", "A small key that might open something."))
    
    # Add food items
    park.add_item(Food("Carrot", "A fresh orange carrot. Bunnies love these!", 15))
    street.add_item(Food("Ice Cream", "A delicious ice cream cone. Might give you a sugar rush!", 10, 
                         lambda player: setattr(player, 'energy', min(player.max_energy, player.energy + 20))))
    
    # Add jetpack to the game
    rooftop.add_item(Jetpack())
    
    # Add some acorns for the side quest
    alley.add_item(Item("Acorn", "A small acorn, perfect for planting.", edible=True, nutrition=5))
    rooftop.add_item(Item("Acorn", "A small acorn, perfect for planting.", edible=True, nutrition=5))
    skyscraper_top.add_item(Item("Golden Acorn", "A rare golden acorn! It looks valuable.", edible=True, nutrition=20))

    return park, house, street, alley, rooftop, skyscraper_lobby, skyscraper_mid, skyscraper_top


def main():
    # Create the game world
    areas = create_areas()
    park, house, street, alley, rooftop, skyscraper_lobby, skyscraper_mid, skyscraper_top = areas
    
    # Create player
    player = Player()
    
    # Create NPCs
    squirrel = NPC("Jeff", "A bushy-tailed squirrel with a worried expression.", 
                  dialogue={"default": "I've lost my acorns! Can you help me find 10 acorns?",
                           "quest_active": "Have you found my acorns yet?",
                           "quest_complete": "Thank you for finding my acorns! Now I can survive the winter."})
    
    # need templates for NPCs using json so that I can create several similar NPCs, like multiple squirrels

    park.add_npc(squirrel)
    
    # Create the acorn collection quest
    def acorn_quest_objective(player):
        """Check if player has 10 acorns."""
        acorn_count = sum(1 for item in player.inventory if item.name.lower() == "acorn")
        golden_acorn_count = sum(1 for item in player.inventory if item.name.lower() == "golden acorn")
        return acorn_count + (golden_acorn_count * 2) >= 10
    
    def acorn_quest_reward(player):
        """Reward for completing the acorn quest."""
        # Remove acorns from inventory
        acorns_to_remove = []
        count = 0
        for item in player.inventory:
            if item.name.lower() == "acorn" and count < 10:
                acorns_to_remove.append(item)
                count += 1
            elif item.name.lower() == "golden acorn" and count < 10:
                acorns_to_remove.append(item)
                count += 2  # Golden acorns count as 2
        
        for acorn in acorns_to_remove:
            player.inventory.remove(acorn)
        
        # Give reward
        player.street_cred += 20
        print("Your street cred increased by 20 points!")
        print("Jeff (the squirrel) is very grateful and spreads the word about your helpfulness.")
        
        # Add a special item as reward
        jetpack_upgrade = Item("Jetpack Fuel Upgrade", "A special upgrade that increases jetpack efficiency.")
        player.add_item(jetpack_upgrade)
        if player.jetpack:
            player.jetpack.max_fuel = 150
            player.jetpack.fuel = 150
            print("Your jetpack has been upgraded with a larger fuel tank!")
    
    acorn_quest = Quest("Acorn Collector", 
                       "Find 10 acorns for the squirrels. Golden acorns count as 2!", 
                       acorn_quest_objective, 
                       acorn_quest_reward)
    squirrel.assign_quest(acorn_quest)
    
    # Set player's starting area
    player.set_current_area(park)
    
    print("Welcome to the Vita Game!")
    print("You are Vita, a mischievous bunny with a jetpack and a taste for adventure.")
    print("Explore the world, cause some chaos, and have fun!")
    print("\nCommands:")
    print("- 'go [direction]' to move (north, south, east, west, up, down)")
    print("- 'look' to look around")
    print("- 'pick up [item]' to pick up an item")
    print("- 'drop [item]' to drop an item")
    print("- 'inventory' or 'inv' to check your inventory")
    print("- 'eat [item]' to eat food")
    print("- 'activate jetpack' to start flying")
    print("- 'deactivate jetpack' to stop flying")
    print("- 'fly [direction]' to fly in a direction")
    print("- 'talk to [npc]' to talk to an NPC")
    print("- 'quit' to exit the game")
    
    # Main game loop
    while True:
        action = input("\n> ").lower()
        
        if action == "quit":
            print("Thanks for playing!")
            break
            
        elif action == "look":
            player.look_around()
            
        elif action.startswith("pick up "):
            item_name = action[8:]  # Remove "pick up " from the beginning
            item = next((i for i in player.current_area.items if i.name.lower() == item_name.lower()), None)
            if item:
                player.add_item(item)
                player.current_area.remove_item(item_name)
            else:
                print(f"There is no {item_name} here.")
                
        elif action.startswith("drop "):
            item_name = action[5:]  # Remove "drop " from the beginning
            player.remove_item(item_name)
            
        elif action.startswith("go "):
            direction = action[3:]  # Remove "go " from the beginning
            if direction in player.current_area.connections:
                # Check if player needs to fly to reach this area
                target_area = player.current_area.connections[direction]
                height_diff = target_area.coordinates.z - player.current_area.coordinates.z
                
                if height_diff > 0 and not player.is_flying:
                    print(f"You need to fly to reach {target_area.name}. Try activating your jetpack first!")
                else:
                    new_area = player.current_area.connections[direction]
                    player.set_current_area(new_area)
            else:
                print(f"You can't go {direction} from here.")
                
        elif action in ["inventory", "inv"]:
            if player.inventory:
                print("Your inventory:")
                for item in player.inventory:
                    print(f"- {item}")
            else:
                print("Your inventory is empty.")
                
        elif action.startswith("eat "):
            item_name = action[4:]  # Remove "eat " from the beginning
            player.eat(item_name)
            
        elif action == "activate jetpack":
            player.activate_jetpack()
            
        elif action == "deactivate jetpack":
            player.deactivate_jetpack()
            
        elif action.startswith("fly "):
            direction = action[4:]  # Remove "fly " from the beginning
            player.fly(direction)
            
        elif action.startswith("talk to "):
            npc_name = action[8:]  # Remove "talk to " from the beginning
            npc = next((n for n in player.current_area.npcs if n.name.lower() == npc_name.lower()), None)
            if npc:
                npc.talk(player)
                if npc.quest and not npc.quest.is_active and not npc.quest.is_completed:
                    accept = input("Accept quest? (yes/no): ").lower()
                    if accept == "yes":
                        npc.quest.start(player)
                elif npc.quest and npc.quest.is_active and not npc.quest.is_completed:
                    if npc.quest.check_completion(player):
                        npc.talk(player)  # Talk again to get completion dialogue
            else:
                print(f"There is no {npc_name} here to talk to.")
                
        elif action == "status":
            print(f"Name: {player.name}")
            print(f"Street Cred: {player.street_cred}")
            print(f"Position: {player.coordinates}")
            print(f"Energy: {player.energy}/{player.max_energy}")
            print(f"Hunger: {player.hunger}")
            if player.is_flying:
                print("Status: Flying with jetpack")
            else:
                print("Status: On the ground")
                
        else:
            print("Command not recognized. Try again.")


# The game will be very open-world but one side mission that the player can do is find 10 acorns and bring them to a tree in the park

def create_example_world():
    """Create an example world to demonstrate the grid system."""
    # Create areas
    park = Area("Central Park", "A beautiful park with trees and a pond.", 
                Coordinates(0, 0, 0), grid_width=10, grid_length=10)
    
    skyscraper_lobby = Area("Skyscraper Lobby", "The grand entrance to a tall skyscraper.", 
                           Coordinates(20, 0, 0), grid_width=5, grid_length=5)
    
    skyscraper_floor2 = Area("Skyscraper Floor 2", "The second floor of the skyscraper.", 
                            Coordinates(20, 0, 10), grid_width=5, grid_length=5)
    
    skyscraper_floor3 = Area("Skyscraper Floor 3", "The third floor of the skyscraper.", 
                            Coordinates(20, 0, 20), grid_width=5, grid_length=5)
    
    # Connect areas
    park.add_connection("east", skyscraper_lobby)
    
    # Create objects and place them in the grid
    # Park objects
    tree = GameObject("Tree", "A tall oak tree with branches perfect for climbing.")
    park.place_object_at(tree, 3, 7)
    
    bench = GameObject("Bench", "A wooden bench to sit and relax.")
    park.place_object_at(bench, 5, 5)
    
    pond = GameObject("Pond", "A small pond with ducks swimming in it.")
    park.place_object_at(pond, 8, 2)
    
    # Skyscraper objects
    reception_desk = GameObject("Reception Desk", "A sleek modern reception desk.")
    skyscraper_lobby.place_object_at(reception_desk, 2, 1)
    
    # Create an elevator in the lobby
    elevator = Elevator("Skyscraper Elevator", "A high-speed elevator serving all floors of the skyscraper.")
    skyscraper_lobby.place_object_at(elevator, 4, 2)
    
    # Add floors to the elevator
    elevator.add_floor(1, skyscraper_lobby, 4, 2)
    elevator.add_floor(2, skyscraper_floor2, 4, 2)
    elevator.add_floor(3, skyscraper_floor3, 4, 2)
    
    # Create items
    carrot = Food("Carrot", "A fresh orange carrot.", nutrition=15)
    park.place_object_at(carrot, 2, 3)
    
    jetpack = Jetpack()
    park.place_object_at(jetpack, 7, 7)
    
    # Create NPCs
    squirrel = NPC("Jeff", "A bushy-tailed squirrel looking for acorns.", 
                  dialogue={"default": "Squeak! (He seems to be looking for acorns.)"})
    park.place_object_at(squirrel, 3, 6)
    
    receptionist = NPC("Sarah", "A friendly receptionist at the front desk.",
                      dialogue={"default": "Welcome to the skyscraper! How can I help you today?"})
    skyscraper_lobby.place_object_at(receptionist, 2, 1)
    
    return park, skyscraper_lobby, skyscraper_floor2, skyscraper_floor3

def example_game():
    """Run a simple example game to demonstrate the grid system."""
    print("Welcome to Vita Game!")
    print("This is a simple example to demonstrate the grid-based movement system.")
    print("Commands: move [direction], look, examine, inventory, quit")
    print("Directions: north/forward, south/backward, east/right, west/left")
    
    # Create the world
    park, skyscraper_lobby, floor2, floor3 = create_example_world()
    
    # Create player
    player = Player()
    player.set_current_area(park, 5, 5)  # Start in the middle of the park
    
    # Game loop
    running = True
    while running:
        command = input("\nWhat would you like to do? ").strip().lower()
        
        if command == "quit":
            running = False
            print("Thanks for playing!")
        
        elif command == "look":
            player.look_around()
        
        elif command == "examine":
            player.examine_surroundings()
        
        elif command == "inventory":
            if player.inventory:
                print("You are carrying:")
                for item in player.inventory:
                    print(f"- {item}")
            else:
                print("Your inventory is empty.")
        
        elif command.startswith("move "):
            direction = command[5:].strip()
            player.move(direction)
        
        elif command.startswith("pick up ") or command.startswith("take "):
            item_name = command[8:] if command.startswith("pick up") else command[5:]
            grid_x, grid_y, grid_z = player.get_grid_position()
            objects_here = player.current_area.get_objects_at(grid_x, grid_y, grid_z)
            
            item = next((obj for obj in objects_here if isinstance(obj, Item) and obj.name.lower() == item_name.lower()), None)
            if item:
                player.current_area.remove_object_from_grid(item, grid_x, grid_y, grid_z)
                player.add_item(item)
            else:
                print(f"There's no {item_name} here to pick up.")
        
        elif command.startswith("use "):
            obj_name = command[4:].strip()
            
            # Check if it's in inventory
            obj = next((item for item in player.inventory if item.name.lower() == obj_name.lower()), None)
            
            if obj:
                if obj_name.lower() == "jetpack":
                    player.activate_jetpack()
                else:
                    obj.use(player)
            else:
                # Check if it's in the current location
                grid_x, grid_y, grid_z = player.get_grid_position()
                objects_here = player.current_area.get_objects_at(grid_x, grid_y, grid_z)
                obj = next((o for o in objects_here if o.name.lower() == obj_name.lower()), None)
                
                if obj:
                    if isinstance(obj, Elevator):
                        print("Available floors:")
                        for floor in sorted(obj.floors.keys()):
                            area, _, _ = obj.floors[floor]
                            print(f"- Floor {floor}: {area.name}")
                        floor_num = input("Which floor? ")
                        try:
                            floor_num = int(floor_num)
                            obj.go_to_floor(floor_num, player)
                        except ValueError:
                            print("Please enter a valid floor number.")
                    else:
                        obj.interact(player)
                else:
                    print(f"You don't see {obj_name} here.")
        
        elif command.startswith("fly "):
            direction = command[4:].strip()
            if player.jetpack and player.is_flying:
                player.fly(direction)
            else:
                print("You need to activate your jetpack first!")
        
        elif command == "activate jetpack":
            if player.jetpack:
                player.activate_jetpack()
            else:
                print("You don't have a jetpack!")
        
        elif command == "deactivate jetpack":
            if player.is_flying:
                player.deactivate_jetpack()
            else:
                print("Your jetpack is not active.")
        
        else:
            print("I don't understand that command.")

if __name__ == "__main__":
    example_game()
