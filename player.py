from .coordinates import Coordinates

class Player:
    """Player class for the Vita game."""
    def __init__(self, name="Vita"):
        self.name = name
        self.street_cred = 0
        self.inventory = []
        self.current_area = None
        self.coordinates = Coordinates(0, 0, 0)
        self.jetpack = None
        self.is_flying = False
        self.energy = 100
        self.max_energy = 100
        self.hunger = 0
        self.max_hunger = 100
        self.money = 0
        self.skills = {}  # Dictionary of skills and their levels
        self.quests = []  # Active and completed quests
        self.relationships = {}  # Relationships with NPCs
        self.properties = {}  # Custom properties
        
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
        
        # Consume fuel based on efficiency
        fuel_used = distance * self.jetpack.fuel_efficiency
        self.jetpack.fuel -= fuel_used
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
    
    def add_quest(self, quest):
        """Add a quest to the player's quest log."""
        self.quests.append(quest)
        quest.start(self)
    
    def check_quests(self):
        """Check the status of all active quests."""
        active_quests = [q for q in self.quests if q.active]
        if not active_quests:
            print("You don't have any active quests.")
            return
        
        print("Active quests:")
        for quest in active_quests:
            print(f"- {quest.name}: {quest.check_progress(self)}")
    
    def complete_quest(self, quest_name):
        """Mark a quest as completed."""
        quest = next((q for q in self.quests if q.name.lower() == quest_name.lower() and q.active), None)
        if quest:
            quest.complete(self)
        else:
            print(f"You don't have an active quest named '{quest_name}'.")
    
    def set_relationship(self, npc, value):
        """Set relationship value with an NPC."""
        self.relationships[npc.name] = value
        
    def adjust_relationship(self, npc, amount):
        """Adjust relationship value with an NPC."""
        current = self.get_relationship(npc)
        self.relationships[npc.name] = max(-100, min(100, current + amount))
        
    def get_relationship(self, npc):
        """Get relationship value with an NPC."""
        return self.relationships.get(npc.name, 0)
    
    def set_skill(self, skill_name, level):
        """Set a skill level."""
        self.skills[skill_name] = level
        
    def improve_skill(self, skill_name, amount=1):
        """Improve a skill by a certain amount."""
        current = self.get_skill(skill_name)
        self.skills[skill_name] = current + amount
        print(f"Your {skill_name} skill improved to {self.skills[skill_name]}!")
        
    def get_skill(self, skill_name):
        """Get a skill level."""
        return self.skills.get(skill_name, 0)
    
    def add_money(self, amount):
        """Add money to the player."""
        self.money += amount
        print(f"You gained ${amount}. You now have ${self.money}.")
        
    def remove_money(self, amount):
        """Remove money from the player."""
        if self.money >= amount:
            self.money -= amount
            print(f"You spent ${amount}. You now have ${self.money}.")
            return True
        else:
            print(f"You don't have enough money. You need ${amount} but only have ${self.money}.")
            return False
    
    def set_property(self, key, value):
        """Set a custom property for the player."""
        self.properties[key] = value
        
    def get_property(self, key, default=None):
        """Get a custom property for the player."""
        return self.properties.get(key, default)
    
    def to_dict(self):
        """Convert player to dictionary for serialization."""
        return {
            "name": self.name,
            "street_cred": self.street_cred,
            "coordinates": self.coordinates.to_dict(),
            "energy": self.energy,
            "max_energy": self.max_energy,
            "hunger": self.hunger,
            "max_hunger": self.max_hunger,
            "money": self.money,
            "skills": self.skills,
            "relationships": self.relationships,
            "properties": self.properties,
            "is_flying": self.is_flying
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create player from dictionary."""
        player = cls(data["name"])
        player.street_cred = data["street_cred"]
        player.coordinates = Coordinates.from_dict(data["coordinates"])
        player.energy = data["energy"]
        player.max_energy = data["max_energy"]
        player.hunger = data["hunger"]
        player.max_hunger = data["max_hunger"]
        player.money = data["money"]
        player.skills = data["skills"]
        player.relationships = data["relationships"]
        player.properties = data["properties"]
        player.is_flying = data["is_flying"]
        
        return player