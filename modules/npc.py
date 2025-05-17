"""
NPC module for the game.
Handles Non-Player Characters.
"""
import random
from .coordinates import Coordinates
from .item import Item

class NPC:
    """NPC class representing non-player characters."""
    def __init__(self, name, description, start_coords=None, area=None, money=20):
        self.name = name
        self.description = description
        self.coordinates = start_coords if start_coords else Coordinates(0,0,0) # Global coordinates
        self.location = area # Current Area object
        self.inventory = []
        self.money = money
        self.id = f"npc_{name.lower().replace(' ', '_')}_{random.randint(1000,9999)}"
        self.action_cooldown = 0 # Simple cooldown to prevent acting every single turn
        
        # Shopping related attributes
        self.desire_to_shop_chance = random.uniform(0.50, 0.75) # Chance per turn to consider shopping
        self.is_currently_shopping = False # Flag to indicate multi-turn shopping intent
        self.desire_to_change_area_chance = random.uniform(0.2, 0.10) # Small chance to wander to a new area
        self.shopping_target_item_name = None # Specific item NPC might want

        # Fleeing related attributes
        self.is_fleeing = False
        self.flee_timer = 0

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
        if not self.location: return False

        current_gx, current_gy = self.get_grid_position()
        new_gx, new_gy = current_gx + dx, current_gy + dy

        if self.location.is_valid_grid_position(new_gx, new_gy):
            # Remove from old grid cell
            self.location.remove_object_from_grid(self, current_gx, current_gy)
            # Add to new grid cell (this also updates self.coordinates)
            self.location.add_object_to_grid(self, new_gx, new_gy)
            return True # Moved successfully
        else:
            return False # Did not move

    def teleport_to_grid_cell(self, target_gx, target_gy):
        """Teleport NPC to a specific grid cell within its current area."""
        if not self.location: return None
        if self.location.is_valid_grid_position(target_gx, target_gy):
            current_gx, current_gy = self.get_grid_position()
            self.location.remove_object_from_grid(self, current_gx, current_gy)
            self.location.add_object_to_grid(self, target_gx, target_gy)
            return f"{self.name} spotted something and ran to ({target_gx}, {target_gy})."
        return None

    def pick_up_item(self, item, grid_x, grid_y):
        """NPC picks up an item from its location."""
        if not self.location: return None
        message = None
        if item in self.location.get_objects_at_grid_cell(grid_x, grid_y):
            if item.value > 0:
                if self.money >= item.value:
                    self.money -= item.value
                    message = f"{self.name} bought {item.name} for ${item.value}. (Money left: ${self.money})"
                else:
                    self.action_cooldown = 3 # Think about it for a bit
                    return f"{self.name} wants {item.name} (costs ${item.value}), but cannot afford it. (Has ${self.money})"
            else:
                message = f"{self.name} picked up {item.name} (free)."

            if message and "cannot afford" not in message: # Ensure pickup only if affordable or free
                self.location.remove_object_from_grid(item, grid_x, grid_y)
                self.inventory.append(item)
                item.coordinates = None # Item is now in inventory
            return message
        return None
    
    def add_item_to_inventory(self, item_instance):
        """Adds a cloned item instance to NPC's inventory."""
        self.inventory.append(item_instance)
        item_instance.coordinates = None # Item is in inventory, not on map

    def drop_item(self, item_name):
        """NPC drops an item into its current location."""
        # Similar to player's drop
        return None # Or a message if implemented

    # --- NPC Actions ---

    def look_around_and_act(self):
        """NPC scans for items and decides to move or pick up."""
        if not self.location: return
        if self.action_cooldown > 0:
            self.action_cooldown -=1
            return
        
        action_message = None
        purchase_info = None # To store details of a shop purchase

        # -1. Check if Fleeing
        if self.is_fleeing and self.flee_timer > 0:
            self.flee_timer -= 1
            # Try to move to a connected area
            if self.location and self.location.connections:
                available_directions = list(self.location.connections.keys())
                if available_directions:
                    chosen_direction = random.choice(available_directions)
                    new_area = self.location.connections[chosen_direction]
                    old_area_name = self.location.name
                    self.set_location(new_area)
                    self.action_cooldown = 1 # Short cooldown after fleeing to new area
                    return f"{self.name} flees from {old_area_name} towards the {chosen_direction} into {new_area.name}!", None
            
            # If couldn't change area, move randomly within current area
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)]) # No idle (0,0) when fleeing
            if self.move_on_grid(dx, dy):
                action_message = f"{self.name} scurries around in panic!"
            self.action_cooldown = 0 # Act quickly when fleeing
            return action_message, None
        elif self.is_fleeing and self.flee_timer <= 0:
            self.is_fleeing = False # Stop fleeing

        my_gx, my_gy = self.get_grid_position()

        # 0. Consider Shopping if in a shop area
        if hasattr(self.location, 'shop_stock') and self.location.shop_stock:
            if random.random() < self.desire_to_shop_chance: # Small chance each turn to decide to shop
                action_message, purchase_info = self.attempt_to_buy_from_shop()
                return action_message, purchase_info # End turn after shopping attempt

        # 1. Check items at current location (picking up from floor)
        objects_here = self.location.get_objects_at_grid_cell(my_gx, my_gy)
        for obj in objects_here:
            if isinstance(obj, Item) and obj.pickupable:
                if random.random() < 0.7: # 70% chance to pick up if on same spot
                    action_message = self.pick_up_item(obj, my_gx, my_gy)
                    self.action_cooldown = 2 # Cooldown after picking up
                    return action_message, None # No shop purchase info

        # 2. Scan for nearby items (within 2 cells for simplicity)
        target_item = None
        min_dist = float('inf')
        item_target_pos = None

        for item_obj in self.location.items: # Iterate all items in area
            if not item_obj.pickupable or item_obj in self.inventory: continue

            item_gx, item_gy = self.location.get_relative_coordinates(item_obj.coordinates)[:2]
            dist = abs(my_gx - item_gx) + abs(my_gy - item_gy) # Manhattan distance
            # change item distance max from 2 to 10
            if dist <= 10 and dist > 0: # Nearby, but not on current spot
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
            moved = False
            if min_dist == 1: # Adjacent
                moved = self.move_on_grid(item_target_pos[0] - my_gx, item_target_pos[1] - my_gy)
            elif min_dist > 1 and min_dist <=2 : # Needs a couple of steps
                 # Move one step towards
                dx = 1 if item_target_pos[0] > my_gx else -1 if item_target_pos[0] < my_gx else 0
                dy = 1 if item_target_pos[1] > my_gy else -1 if item_target_pos[1] < my_gy else 0
                moved = self.move_on_grid(dx,dy)
            elif min_dist > 2: # "Teleport" for items further away
                action_message = self.teleport_to_grid_cell(item_target_pos[0], item_target_pos[1])
                if action_message: # Teleport successful
                    self.action_cooldown = 1 # Small cooldown after teleport
                    return action_message, None
            
            if moved:
                self.action_cooldown = 0 # Reset cooldown as moving towards item is significant
                return f"{self.name} moves towards {target_item.name}.", None

        # 3. If no item interaction, consider changing area
        if self.location and self.location.connections and random.random() < self.desire_to_change_area_chance:
            available_directions = list(self.location.connections.keys())
            if available_directions:
                chosen_direction = random.choice(available_directions)
                new_area = self.location.connections[chosen_direction]
                # Store old area name for message before it changes
                old_area_name = self.location.name 
                self.set_location(new_area) # This changes self.location
                self.action_cooldown = random.randint(2, 5) # Cooldown after changing area
                return f"{self.name} wanders from {old_area_name} towards the {chosen_direction} into {new_area.name}.", None

        # 4. If no other action, random wander within current area
        if random.random() < 0.7: # 70% chance to wander if nothing else to do
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (0,0)]) # (0,0) for idle
            if dx !=0 or dy !=0:
                if self.move_on_grid(dx, dy):
                    action_message = f"{self.name} wanders around."
            self.action_cooldown = random.randint(1,3) # Cooldown after attempting to wander
            return action_message, None
            
        return None, None


    def attempt_to_buy_from_shop(self):
        """NPC attempts to buy an item from the current area's shop_stock."""
        if not self.location or not hasattr(self.location, 'shop_stock') or not self.location.shop_stock:
            return f"{self.name} looks around but there's nothing to buy here.", None

        # For now, NPC picks a random item from the shop to consider
        available_items = list(self.location.shop_stock.keys())
        if not available_items:
            return f"{self.name} browsed {self.location.name}, but it's empty.", None
        
        item_name_to_buy = random.choice(available_items)
        item_details = self.location.shop_stock[item_name_to_buy]

        if item_details['stock'] <= 0:
            self.action_cooldown = 1
            return f"{self.name} wanted {item_details['prototype'].name}, but it's out of stock.", None

        if self.money >= item_details['price']:
            # Use the area's process_purchase method
            bought_item_instance, price = self.location.process_purchase(item_name_to_buy, self.money)
            if bought_item_instance:
                self.money -= price
                self.add_item_to_inventory(bought_item_instance)
                self.action_cooldown = random.randint(3, 5) # Cooldown after successful purchase
                purchase_details = {
                    'item_name': bought_item_instance.name,
                    'price': price,
                    'stock_symbol': self.location.associated_stock_symbol
                }
                return f"{self.name} bought {bought_item_instance.name} from {self.location.name} for ${price:.2f}.", purchase_details
            else: # Should not happen if checks above are correct, but as a fallback
                return f"{self.name} tried to buy {item_name_to_buy} but something went wrong.", None
        else:
            self.action_cooldown = random.randint(2, 4) # Cooldown to "save up" or "reconsider"
            return f"{self.name} wants {item_details['prototype'].name} (costs ${item_details['price']:.2f}), but cannot afford it.", None

    def start_fleeing(self, duration=5):
        """Makes the NPC start fleeing."""
        self.is_fleeing = True
        self.flee_timer = duration
        self.action_cooldown = 0 # Act immediately

    def update(self):
        """Called each game turn to allow NPC to perform actions."""
        return self.look_around_and_act()
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
        messages = []
        for npc in self.npcs.values():
            # npc.update() now returns (action_message, purchase_info)
            result = npc.update() 
            if result: # Ensure result is not None (e.g. if NPC is on cooldown and returns None early)
                action_message, purchase_info = result
                if action_message or purchase_info: # Only add if there's something to report
                    messages.append({'npc': npc, 'action_message': action_message, 'purchase_info': purchase_info})
        return messages