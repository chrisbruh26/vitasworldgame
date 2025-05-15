"""
NPC module for the game.
Handles Non-Player Characters.
"""
import random
from .coordinates import Coordinates
from .item import Item

class NPC:
    """NPC class representing non-player characters."""
    def __init__(self, name, description, start_coords=None, area=None):
        self.name = name
        self.description = description
        self.coordinates = start_coords if start_coords else Coordinates(0,0,0) # Global coordinates
        self.location = area # Current Area object
        self.inventory = []
        self.id = f"npc_{name.lower().replace(' ', '_')}_{random.randint(1000,9999)}"
        self.action_cooldown = 0 # Simple cooldown to prevent acting every single turn

    def set_location(self, area, grid_x=None, grid_y=None):
        """Places the NPC in an area and on its grid."""
        if self.location and self.location != area : # If changing areas
            # Get old grid pos to remove from old area's grid
            old_gx, old_gy = self.location.get_relative_coordinates(self.coordinates)[:2]
            self.location.remove_object_from_grid(self, int(old_gx), int(old_gy))

        self.location = area
        if area:
            if grid_x is None: grid_x = area.grid_width // 2
            if grid_y is None: grid_y = area.grid_length // 2
            
            grid_x = max(0, min(grid_x, area.grid_width - 1))
            grid_y = max(0, min(grid_y, area.grid_length - 1))
            
            area.add_object_to_grid(self, grid_x, grid_y) # This also updates self.coordinates
        else: # NPC removed from any area
            self.coordinates = Coordinates(-1,-1,-1) # Off-map

    def get_grid_position(self):
        """Get the NPC's position relative to its current area's grid."""
        if not self.location:
            return None, None
        rel_coords = self.location.get_relative_coordinates(self.coordinates)
        return int(rel_coords[0]), int(rel_coords[1])

    def move_on_grid(self, dx, dy):
        """Move the NPC by dx, dy on its current area's grid."""
        if not self.location: return

        current_gx, current_gy = self.get_grid_position()
        new_gx, new_gy = current_gx + dx, current_gy + dy

        if self.location.is_valid_grid_position(new_gx, new_gy):
            # Remove from old grid cell
            self.location.remove_object_from_grid(self, current_gx, current_gy)
            # Add to new grid cell (this also updates self.coordinates)
            self.location.add_object_to_grid(self, new_gx, new_gy)
            # print(f"{self.name} moved to ({new_gx}, {new_gy}) in {self.location.name}.")
        else:
            # print(f"{self.name} tried to move to ({new_gx}, {new_gy}) but it's out of bounds or invalid.")
            pass

    def teleport_to_grid_cell(self, target_gx, target_gy):
        """Teleport NPC to a specific grid cell within its current area."""
        if not self.location: return
        if self.location.is_valid_grid_position(target_gx, target_gy):
            current_gx, current_gy = self.get_grid_position()
            self.location.remove_object_from_grid(self, current_gx, current_gy)
            self.location.add_object_to_grid(self, target_gx, target_gy)
            print(f"{self.name} teleported to ({target_gx}, {target_gy}) in {self.location.name}.")

    def pick_up_item(self, item, grid_x, grid_y):
        """NPC picks up an item from its location."""
        if not self.location: return
        if item in self.location.get_objects_at_grid_cell(grid_x, grid_y):
            self.location.remove_object_from_grid(item, grid_x, grid_y)
            self.inventory.append(item)
            item.coordinates = None # Item is now in inventory
            print(f"{self.name} picked up {item.name}.")
            # Future: Subtract money if it's a "purchase"

    def drop_item(self, item_name):
        """NPC drops an item into its current location."""
        # Similar to player's drop
        pass

    def look_around_and_act(self):
        """NPC scans for items and decides to move or pick up."""
        if not self.location: return
        if self.action_cooldown > 0:
            self.action_cooldown -=1
            return

        my_gx, my_gy = self.get_grid_position()

        # 1. Check items at current location
        objects_here = self.location.get_objects_at_grid_cell(my_gx, my_gy)
        for obj in objects_here:
            if isinstance(obj, Item) and obj.pickupable:
                if random.random() < 0.7: # 70% chance to pick up if on same spot
                    self.pick_up_item(obj, my_gx, my_gy)
                    self.action_cooldown = 2 # Cooldown after picking up
                    return

        # 2. Scan for nearby items (within 2 cells for simplicity)
        target_item = None
        min_dist = float('inf')
        item_target_pos = None

        for item_obj in self.location.items: # Iterate all items in area
            if not item_obj.pickupable or item_obj in self.inventory: continue

            item_gx, item_gy = self.location.get_relative_coordinates(item_obj.coordinates)[:2]
            dist = abs(my_gx - item_gx) + abs(my_gy - item_gy) # Manhattan distance

            if dist <= 2 and dist > 0: # Nearby, but not on current spot
                if random.random() < 0.5: # 50% chance to consider it
                    if dist < min_dist:
                        min_dist = dist
                        target_item = item_obj
                        item_target_pos = (int(item_gx), int(item_gy))
            elif dist > 2 and dist < 5 : # A bit further, less chance to go for it
                 if random.random() < 0.2: # 20% chance to consider it
                    if dist < min_dist: # Prioritize closer items even if far
                        min_dist = dist
                        target_item = item_obj
                        item_target_pos = (int(item_gx), int(item_gy))

        if target_item and item_target_pos:
            # Move towards item or teleport if far
            if min_dist == 1: # Adjacent
                self.move_on_grid(item_target_pos[0] - my_gx, item_target_pos[1] - my_gy)
            elif min_dist > 1 and min_dist <=2 : # Needs a couple of steps
                 # Move one step towards
                dx = 1 if item_target_pos[0] > my_gx else -1 if item_target_pos[0] < my_gx else 0
                dy = 1 if item_target_pos[1] > my_gy else -1 if item_target_pos[1] < my_gy else 0
                self.move_on_grid(dx,dy)
            elif min_dist > 2: # "Teleport" for items further away
                self.teleport_to_grid_cell(item_target_pos[0], item_target_pos[1])
            self.action_cooldown = 1
            return

        # 3. If no item interaction, random wander
        if random.random() < 0.3: # 30% chance to wander
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (0,0)]) # (0,0) for idle
            if dx !=0 or dy !=0:
                self.move_on_grid(dx, dy)
            self.action_cooldown = 3 # Cooldown after wandering

    def update(self):
        """Called each game turn to allow NPC to perform actions."""
        self.look_around_and_act()

class NPCManager:
    def __init__(self):
        self.npcs = {} # npc_id -> NPC_object

    def add_npc(self, npc):
        self.npcs[npc.id] = npc

    def get_npc(self, npc_id_or_name):
        if npc_id_or_name in self.npcs:
            return self.npcs[npc_id_or_name]
        for npc in self.npcs.values():
            if npc.name.lower() == npc_id_or_name.lower():
                return npc
        return None

    def update_all_npcs(self):
        for npc in self.npcs.values():
            npc.update()