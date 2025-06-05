"""
NPC module for the game.
Handles Non-Player Characters.
"""
import random
from .coordinates import Coordinates
from .game_objects import InfluenceSource # Import InfluenceSource
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
        self.desire_to_change_area_chance = random.uniform(0.02, 0.10) # Corrected: Small chance to wander to a new area
        self.shopping_target_item_name = None # Specific item NPC might want

        # Fleeing related attributes
        self.is_fleeing = False
        self.flee_timer = 0
        self.recently_failed_to_buy = {} # item_key_lower: expiry_turn
        self.shopping_frustration_cooldown = 0 # Turns to wait before trying to shop again after a failure
        self.recently_processed_influences = {} # influence_source_id: expiry_turn
        self.active_influence_source_id = None # ID of the influence source for the current shopping_target_item_name
        self.MIN_MONEY_TO_CONSIDER_SHOPPING = 1.50 # Minimum money to even attempt shopping

        # Mission-related attributes for item delivery
        self.current_mission_type = None # e.g., "deliver_item"
        self.mission_item_name = None    # Name of the item to acquire/deliver
        self.mission_target_area_name = None # Name of the area to deliver to
        self.mission_target_coords = None    # (gx, gy) tuple for delivery spot
        self.mission_phase = None            # e.g., "acquire_item", "travel_to_area", "travel_to_spot", "deliver"
        self.active_mission_influence_id = None # ID of the influence source that assigned the mission

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

    def teleport_to_grid_cell(self, target_gx, target_gy, item_name_teleported_for=None):
        """Teleport NPC to a specific grid cell within its current area."""
        if not self.location: return None
        message = None
        structured_details = None

        if self.location.is_valid_grid_position(target_gx, target_gy):
            current_gx, current_gy = self.get_grid_position()
            self.location.remove_object_from_grid(self, current_gx, current_gy)
            self.location.add_object_to_grid(self, target_gx, target_gy)
            message = f"{self.name} spotted something and ran to ({target_gx}, {target_gy})."
            structured_details = {
                'type': 'spotted_and_ran_to_coords',
                'target_coords': (target_gx, target_gy)
            }
            if item_name_teleported_for:
                structured_details['item_name'] = item_name_teleported_for # Optional: for more detailed clauses
            return message, structured_details
        return None, None

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

    def drop_item_from_inventory(self, item_to_drop, drop_gx, drop_gy):
        """
        NPC drops a specific item object from inventory at specified grid coords in current area.
        Returns a message string.
        """
        if not self.location:
            return f"{self.name} tries to drop {item_to_drop.name}, but is nowhere."
        if item_to_drop not in self.inventory:
            return f"{self.name} tries to drop {item_to_drop.name}, but doesn't have it."
        if not self.location.is_valid_grid_position(drop_gx, drop_gy):
            return f"{self.name} tries to drop {item_to_drop.name} at ({drop_gx},{drop_gy}), but that's not a valid spot in {self.location.name}."

        self.inventory.remove(item_to_drop)
        self.location.add_object_to_grid(item_to_drop, drop_gx, drop_gy) # This updates item's coords
        return f"{self.name} dropped {item_to_drop.name} at ({drop_gx},{drop_gy}) in {self.location.name}."

    def drop_item_by_name_at_current_location(self, item_name_query):
        """NPC finds an item by name in inventory and drops it at their current location."""
        item_to_drop = None
        for item_in_inv in self.inventory:
            if item_in_inv.name.lower() == item_name_query.lower():
                item_to_drop = item_in_inv
                break
        if not item_to_drop:
            return f"{self.name} tried to drop '{item_name_query}' but doesn't have one."
        
        current_gx, current_gy = self.get_grid_position()
        return self.drop_item_from_inventory(item_to_drop, current_gx, current_gy)

    # --- NPC Actions ---

    def look_around_and_act(self, current_game_turn):
        """NPC scans for items and decides to move or pick up."""
        if not self.location: return
        if self.action_cooldown > 0:
            self.action_cooldown -=1
            return
        
        if self.shopping_frustration_cooldown > 0:
            self.shopping_frustration_cooldown -= 1

        # Clear expired items from recently_failed_to_buy list
        for item_key, expiry_turn in list(self.recently_failed_to_buy.items()):
            if current_game_turn >= expiry_turn:
                del self.recently_failed_to_buy[item_key]
        
        # Clear expired processed influences
        for source_id, expiry_turn in list(self.recently_processed_influences.items()):
            if current_game_turn >= expiry_turn:
                del self.recently_processed_influences[source_id]


        my_gx, my_gy = self.get_grid_position()
        if my_gx is None or my_gy is None: # NPC not properly placed
            return {'message': None, 'purchase_info': None, 'flee_event': None}
        
        # --- MISSION EXECUTION LOGIC (Highest Priority if active) ---
        if self.current_mission_type == "deliver_item":
            # Check if mission item is in inventory
            mission_item_in_inventory = None
            for item_in_inv in self.inventory:
                if item_in_inv.name.lower() == self.mission_item_name.lower():
                    mission_item_in_inventory = item_in_inv
                    break

            if self.mission_phase == "acquire_item":
                if mission_item_in_inventory:
                    self.mission_phase = "travel_to_area"
                    # Fall through to next phase in the same turn if possible, or wait for next turn
                else:
                    # Try to acquire the item. Set shopping target.
                    # This will leverage existing shopping/pickup logic in subsequent parts of this method.
                    self.shopping_target_item_name = self.mission_item_name
                    self.is_currently_shopping = True # Actively seek it out

                    # Check if mission item has become unobtainable or if NPC is too frustrated to get it
                    failed_to_acquire_mission_item = False
                    mission_item_key = self.mission_item_name.lower()

                    if mission_item_key in self.recently_failed_to_buy and \
                       self.recently_failed_to_buy[mission_item_key] > current_game_turn + 50000: # Unaffordable
                        failed_to_acquire_mission_item = True
                    
                    # Condition 2: Frustration from trying to buy, but only if it's NOT a special free item like Yellow Star.
                    # For Yellow Star, frustration from failing to "buy" it in a shop shouldn't end the mission.
                    # They should continue to look on the ground.
                    is_special_free_mission_item = (mission_item_key == "yellow star") # Expand if more such items

                    if not is_special_free_mission_item:
                        # If shopping frustration is active AND the current shopping target IS the mission item,
                        # it implies a recent failure to acquire it (e.g., not found in shop, out of stock).
                        if self.shopping_frustration_cooldown > 0 and \
                           self.shopping_target_item_name and \
                           self.shopping_target_item_name.lower() == mission_item_key:
                            failed_to_acquire_mission_item = True
                    
                    if failed_to_acquire_mission_item:
                        # Import colors module
                        import sys
                        import os
                        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                        from colors import colorize, GameColors, format_item_name, format_npc_name, TextColor
                        
                        msg = f"{format_npc_name(self.name)} gives up on the mission to deliver {format_item_name(self.mission_item_name)} as it seems unobtainable right now."
                        msg = colorize(msg, TextColor.BRIGHT_RED)  # Use red for mission failure
                        self.recently_processed_influences[self.active_mission_influence_id] = current_game_turn + random.randint(15, 25)
                        self._clear_mission_state()
                        return {'message': msg, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

            elif self.mission_phase == "travel_to_area":
                if not mission_item_in_inventory: # Lost the item somehow? Revert to acquire.
                    self.mission_phase = "acquire_item"
                    # Fall through
                elif self.location.name.lower() == self.mission_target_area_name.lower():
                    self.mission_phase = "travel_to_spot"
                    # Fall through
                else:
                    # NPC needs to change area. This will be handled by the area changing logic (section 3)
                    # which is now mission-aware. No direct return here; let it fall through.
                    pass # Rely on general movement for now, or specific travel logic in section 3.

            elif self.mission_phase == "travel_to_spot":
                # Debug logging
                # print(f"DEBUG: {self.name} in travel_to_spot phase at {my_gx}, {my_gy}, target: {self.mission_target_coords}")
                # print(f"DEBUG: Mission item in inventory: {mission_item_in_inventory is not None}")
                
                if not mission_item_in_inventory:
                    # print(f"DEBUG: {self.name} lost mission item, reverting to acquire phase")
                    self.mission_phase = "acquire_item" # Lost item
                elif self.location.name.lower() != self.mission_target_area_name.lower():
                    # print(f"DEBUG: {self.name} in wrong area ({self.location.name} vs {self.mission_target_area_name}), reverting to travel_to_area phase")
                    self.mission_phase = "travel_to_area" # Wrong area
                elif not isinstance(self.mission_target_coords, tuple) or len(self.mission_target_coords) < 2:
                    print(f"ERROR: Invalid mission_target_coords: {self.mission_target_coords}, fixing...")
                    # Try to fix it - use center of area as fallback
                    self.mission_target_coords = (self.location.grid_width // 2, self.location.grid_length // 2)
                    # print(f"DEBUG: Fixed mission_target_coords to {self.mission_target_coords}")
                elif (my_gx, my_gy) == self.mission_target_coords:
                    # print(f"DEBUG: {self.name} reached target spot, advancing to deliver phase")
                    self.mission_phase = "deliver"
                    # Fall through
                else: # Move towards target_coords
                    # Import colors module
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from colors import colorize, GameColors, format_item_name, format_npc_name
                    
                    try:
                        # Ensure coordinates are integers
                        target_gx = int(self.mission_target_coords[0])
                        target_gy = int(self.mission_target_coords[1])
                        # print(f"DEBUG: {self.name} moving towards ({target_gx}, {target_gy}) from ({my_gx}, {my_gy})")
                        
                        dx = 1 if target_gx > my_gx else -1 if target_gx < my_gx else 0
                        dy = 1 if target_gy > my_gy else -1 if target_gy < my_gy else 0
                        
                        move_success = self.move_on_grid(dx, dy)
                        # print(f"DEBUG: Move attempt {'succeeded' if move_success else 'failed'} with dx={dx}, dy={dy}")
                        
                        self.action_cooldown = 1
                        mission_msg = f"{format_npc_name(self.name)} heads towards the offering spot for {format_item_name(self.mission_item_name)}."
                        return {'message': colorize(mission_msg, GameColors.NPC_INFLUENCE_ACTIVE), 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}
                    except Exception as e:
                        print(f"ERROR during travel_to_spot movement: {e}")
                        # Emergency fallback - just advance to deliver phase at current spot
                        self.mission_target_coords = (my_gx, my_gy)
                        self.mission_phase = "deliver"
                        return {'message': f"{self.name} seems confused about where to go, but decides this spot will do.", 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}
            
            elif self.mission_phase == "deliver":
                # Debug logging
                # print(f"DEBUG: {self.name} in delivery phase at {my_gx}, {my_gy}, target: {self.mission_target_coords}")
                # print(f"DEBUG: Mission item in inventory: {mission_item_in_inventory is not None}")
                
                if mission_item_in_inventory:
                    # Import colors module
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from colors import colorize, GameColors, format_item_name, format_npc_name
                    
                    # Ensure mission_target_coords is a valid tuple
                    if not isinstance(self.mission_target_coords, tuple) or len(self.mission_target_coords) < 2:
                        print(f"ERROR: Invalid mission_target_coords: {self.mission_target_coords}, fixing...")
                        # Try to fix it - use current position as fallback
                        self.mission_target_coords = (my_gx, my_gy)
                    
                    try:
                        # Ensure coordinates are integers
                        target_x = int(self.mission_target_coords[0])
                        target_y = int(self.mission_target_coords[1])
                        
                        # print(f"DEBUG: Attempting to drop {mission_item_in_inventory.name} at ({target_x}, {target_y})")
                        drop_msg = self.drop_item_from_inventory(mission_item_in_inventory, target_x, target_y)
                        delivery_msg = f"{format_npc_name(self.name)} carefully places the {format_item_name(mission_item_in_inventory.name)} at ({target_x}, {target_y}) in {self.location.name} as an offering. "
                        delivery_msg += colorize(drop_msg, GameColors.NPC_INFLUENCE_ACTIVE)
                        self.recently_processed_influences[self.active_mission_influence_id] = current_game_turn + random.randint(20, 40) # Longer cooldown after completing mission
                        self._clear_mission_state()
                        self.action_cooldown = random.randint(2,4)
                        return {'message': delivery_msg, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}
                    except Exception as e:
                        print(f"ERROR during delivery: {e}")
                        # Emergency fallback - drop at current position
                        try:
                            drop_msg = self.drop_item_from_inventory(mission_item_in_inventory, my_gx, my_gy)
                            delivery_msg = f"{format_npc_name(self.name)} had trouble with the offering spot, so places the {format_item_name(mission_item_in_inventory.name)} right here instead. "
                            delivery_msg += colorize(drop_msg, GameColors.NPC_INFLUENCE_ACTIVE)
                            self._clear_mission_state()
                            return {'message': delivery_msg, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}
                        except Exception as e2:
                            print(f"CRITICAL ERROR during emergency delivery: {e2}")
                            # Last resort - just clear the mission
                            self._clear_mission_state()
                            return {'message': f"{self.name} seems confused and gives up on their mission.", 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}
                else: # Lost item just before delivery
                    # print(f"DEBUG: {self.name} lost the mission item just before delivery, reverting to acquire phase")
                    self.mission_phase = "acquire_item" 
                    # Fall through to general logic which might try to re-acquire

        # Early check: If influenced to shop but has no/low money, give up on the influence.
        if self.is_currently_shopping and \
           self.shopping_target_item_name and \
           self.money < self.MIN_MONEY_TO_CONSIDER_SHOPPING:
            
            abandon_message = f"{self.name} realizes they don't have enough money for {self.shopping_target_item_name} and sighs, giving up the idea."
            self.shopping_target_item_name = None
            self.is_currently_shopping = False
            if self.active_influence_source_id:
                self.recently_processed_influences[self.active_influence_source_id] = current_game_turn + random.randint(10, 20)
                self.active_influence_source_id = None # Clear shopping influence ID
            self.shopping_frustration_cooldown = random.randint(3, 5) # Get frustrated
            # This message might be overridden if another action is taken, but sets the state.
            # No immediate return, let other logic proceed.

        # -2. Check for Influence Sources (before fleeing, as influence might be a subtle background thing)
        # This check happens even if on cooldown for other actions, representing a passive perception.
        # However, the reaction (changing shopping target) might be delayed if already busy.
        if not self.is_fleeing: # Don't get influenced while panicking
            # For "shop" type influences, skip if broke.
            # For "deliver_item", more nuanced check below.
            can_be_influenced_financially = True
            if self.money < self.MIN_MONEY_TO_CONSIDER_SHOPPING: # General check for shopping
                 can_be_influenced_financially = False

            for obj_coords, objects_in_cell in self.location.grid_objects.items():
                for obj in objects_in_cell:
                    if isinstance(obj, InfluenceSource):
                            source_gx, source_gy = obj_coords # These are already grid coordinates
                            # Check if recently processed this specific influence
                            if obj.id in self.recently_processed_influences:
                                continue # Ignore this influence for now
                            
                            dist_to_source = abs(my_gx - source_gx) + abs(my_gy - source_gy)
    
                            if dist_to_source <= obj.influence_radius:
                                if random.random() < obj.influence_strength:
                                    if obj.action_type == "shop" and can_be_influenced_financially and not self.current_mission_type:
                                        # Check if already targeting this or if it's a new influence
                                        if self.shopping_target_item_name != obj.target_item_name:
                                            self.active_influence_source_id = obj.id # Store which influence caused this
                                            self.shopping_target_item_name = obj.target_item_name
                                            self.desire_to_shop_chance = min(1.0, self.desire_to_shop_chance + 0.1)
                                            self.is_currently_shopping = True 
                                            self.action_cooldown = 0 
                                            
                                            # Import colors module
                                            import sys
                                            import os
                                            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                                            from colors import colorize, GameColors
                                            
                                            msg = f"{self.name} notices the {obj.name}. "
                                            if obj.target_item_name:
                                                msg += colorize(f"Suddenly, they feel a strong craving for {obj.target_item_name}!", GameColors.NPC_INFLUENCE_ACTIVE)
                                            else:
                                                msg += colorize(obj.influence_message, GameColors.NPC_INFLUENCE_ACTIVE)
                                            return {'message': msg, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}
                                    
                                    elif obj.action_type == "deliver_item" and not self.current_mission_type: # Not already on a mission
                                        item_already_possessed = any(item.name.lower() == obj.delivery_item_name.lower() for item in self.inventory)
                                        
                                        # Determine if the item is considered "free" to acquire (e.g., specific named items like Yellow Star)
                                        is_item_free_to_acquire = obj.delivery_item_name.lower() == "yellow star" 

                                        if not item_already_possessed and not is_item_free_to_acquire and self.money < self.MIN_MONEY_TO_CONSIDER_SHOPPING:
                                            # Can't afford to acquire the item for delivery if it's not free
                                            continue 

                                        # Import colors module
                                        import sys
                                        import os
                                        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                                        from colors import colorize, GameColors, format_item_name, format_npc_name, format_area_name
                                        
                                        # print(f"DEBUG: Assigning delivery mission to {self.name}")
                                        # print(f"DEBUG: Item: {obj.delivery_item_name}, Target area: {obj.delivery_target_area_name}")
                                        # print(f"DEBUG: Target coords: {obj.delivery_target_coords}, type: {type(obj.delivery_target_coords)}")
                                        
                                        self.current_mission_type = "deliver_item"
                                        self.mission_item_name = obj.delivery_item_name
                                        self.mission_target_area_name = obj.delivery_target_area_name
                                        # Ensure coordinates are stored as a tuple of integers
                                        if isinstance(obj.delivery_target_coords, tuple) and len(obj.delivery_target_coords) >= 2:
                                            self.mission_target_coords = (int(obj.delivery_target_coords[0]), int(obj.delivery_target_coords[1]))
                                        else:
                                            print(f"WARNING: Invalid delivery target coordinates: {obj.delivery_target_coords}")
                                            # Use center of current area as fallback
                                            self.mission_target_coords = (self.location.grid_width // 2, self.location.grid_length // 2)
                                            
                                        self.mission_phase = "acquire_item"
                                        self.active_mission_influence_id = obj.id
                                        
                                        # print(f"DEBUG: Mission assigned. Target coords set to: {self.mission_target_coords}, type: {type(self.mission_target_coords)}")
                                        self.action_cooldown = 0

                                        msg = f"{format_npc_name(self.name)} feels a divine calling from the {obj.name}! "
                                        mission_details = f"They must find a {format_item_name(self.mission_item_name)} and bring it to {format_area_name(self.mission_target_area_name)}."
                                        msg += colorize(mission_details, GameColors.NPC_INFLUENCE_ACTIVE)
                                        return {'message': msg, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

        
        action_message = None
        purchase_info = None # To store details of a shop purchase

        # -1. Check if Fleeing
        if self.is_fleeing and self.flee_timer > 0:
            self.flee_timer -= 1
            action_message = None # Initialize action_message for this block

            # A. If currently in a shelter, stay put and move randomly inside
            if self.location and getattr(self.location, 'is_shelter', False):
                dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)]) # No idle (0,0) when fleeing
                if self.move_on_grid(dx, dy):
                    action_message = f"{self.name} scurries around nervously inside {self.location.name}."
                else: # Can't move, maybe stuck in a corner
                    action_message = f"{self.name} huddles in a corner of {self.location.name}."
                self.action_cooldown = 0 # Act quickly when fleeing

                return {'message': action_message, 'purchase_info': None, 'flee_event': None}



            # Try to move to a connected area
            # B. Not in a shelter, try to find one or flee to any connected area
            if self.location and self.location.connections:
                shelters = []
                other_exits = []
                for direction, connected_area in self.location.connections.items():
                    if getattr(connected_area, 'is_shelter', False):
                        shelters.append((direction, connected_area))
                    else:
                        other_exits.append((direction, connected_area))
                
                moved_to_new_area = False
                if shelters: # Prioritize shelters
                    chosen_direction, new_area = random.choice(shelters)
                    moved_to_new_area = True
                elif other_exits: # No shelters, pick any other exit
                    chosen_direction, new_area = random.choice(other_exits)
                    moved_to_new_area = True

                if moved_to_new_area:
                    old_area_name = self.location.name
                    self.set_location(new_area)
                    
                    self.action_cooldown = 1 
                    flee_event_data = {
                        'npc_id': self.id,
                        'npc_name': self.name,
                        'old_area_name': old_area_name,
                        'new_area_name': new_area.name,
                        'direction': chosen_direction
                    }




                    if getattr(new_area, 'is_shelter', False):

                        action_message = f"{self.name} flees from {old_area_name} towards the {chosen_direction} and ducks into {new_area.name}!"


                    else:
                        action_message = f"{self.name} flees from {old_area_name} towards the {chosen_direction} into {new_area.name}!"
                    return {'message': action_message, 'purchase_info': None, 'flee_event': flee_event_data}
            
            # C. No connections or couldn't move to a new area, move randomly within current (unsafe) area
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)]) # No idle (0,0) when fleeing
            if self.move_on_grid(dx, dy):
                action_message = f"{self.name} scurries around in panic!"
            else: # NPC couldn't move
                action_message = f"{self.name} looks panicked but is stuck!"
            self.action_cooldown = 0 # Act quickly when fleeing

            return {'message': action_message, 'purchase_info': None, 'flee_event': None}


        elif self.is_fleeing and self.flee_timer <= 0:
            self.is_fleeing = False # Stop fleeing
            self.action_cooldown = random.randint(1,3) # Cooldown after calming down
            return {'message': f"{self.name} seems to calm down.", 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

        # 0. Consider Shopping if in a shop area
        #    BUT NOT if on a delivery mission and already have the item (or past acquire phase for other reasons)
        can_consider_general_shopping = True
        if self.current_mission_type == "deliver_item":
            # If on a mission, only consider general shopping if in 'acquire_item' phase
            # AND the shopping_target_item_name is NOT the mission item (meaning mission item acquired, but now general shopping)
            # OR if mission_phase is not acquire_item (meaning item acquired or other phase)
            if self.mission_phase != "acquire_item":
                 can_consider_general_shopping = False
            elif self.shopping_target_item_name and self.shopping_target_item_name.lower() != self.mission_item_name.lower():
                 pass # This means mission item acquired, now considering other shopping. This is the "distraction". Let's prevent this.
                 # Actually, if shopping_target is NOT mission item, it means they are distracted.
                 # If mission_phase is acquire_item, shopping_target SHOULD be mission_item.
                 # So, if mission_phase is acquire_item, this block IS for the mission item.

        if can_consider_general_shopping and hasattr(self.location, 'shop_stock') and self.location.shop_stock:
            if self.money >= self.MIN_MONEY_TO_CONSIDER_SHOPPING and \
               self.shopping_frustration_cooldown <= 0 and \
               random.random() < self.desire_to_shop_chance: # Consider shopping
                action_message, purchase_info = self.attempt_to_buy_from_shop(current_game_turn)
                if not purchase_info and action_message: # If shopping failed (no purchase, but got a message)
                    self.shopping_frustration_cooldown = random.randint(3, 6) # Get frustrated for a bit longer
                    self.is_currently_shopping = False # Ensure active shopping flag is cleared on any failure
                # Return the result of the shopping attempt. Area change logic below will consider frustration.
                return {'message': action_message, 'purchase_info': purchase_info, 'flee_event': None, 'structured_action_details': None}

        # 1. Check items at current location (picking up from floor)
        objects_here = self.location.get_objects_at_grid_cell(my_gx, my_gy)
        for obj in objects_here:
            if isinstance(obj, Item) and obj.pickupable:
                if random.random() < 0.7: # 70% chance to pick up if on same spot
                    action_message = self.pick_up_item(obj, my_gx, my_gy)
                    self.action_cooldown = 2 # Cooldown after picking up
                    return {'message': action_message, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

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
                action_message, structured_details = self.teleport_to_grid_cell(item_target_pos[0], item_target_pos[1], item_name_teleported_for=target_item.name)
                if action_message: # Teleport successful
                    self.action_cooldown = 1 # Small cooldown after teleport
                    return {'message': action_message, 'purchase_info': None, 'flee_event': None, 'structured_action_details': structured_details}
            
            if moved:
                self.action_cooldown = 0 # Reset cooldown as moving towards item is significant
                # This "moves towards" could also be a structured action in the future
                return {'message': f"{self.name} moves towards {target_item.name}.", 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

        # 3. If no item interaction, consider changing area
        if self.location and self.location.connections:
            # --- Area Changing Logic ---
            # Priority: 1. Mission Travel, 2. Shopping Travel, 3. Frustrated/General Wandering

            # 1. Mission Travel to Area
            if self.current_mission_type == "deliver_item" and \
               self.mission_phase == "travel_to_area" and \
               self.location.name.lower() != self.mission_target_area_name.lower():
                
                best_direction_for_mission = None
                # Prefer direct connections to the target area
                for direction, connected_area in self.location.connections.items():
                    if connected_area.name.lower() == self.mission_target_area_name.lower():
                        best_direction_for_mission = direction
                        break
                
                if best_direction_for_mission:
                    new_area = self.location.connections[best_direction_for_mission]
                    old_area_name = self.location.name
                    self.set_location(new_area)
                    self.action_cooldown = random.randint(1,2)
                    msg = f"{self.name} purposefully heads from {old_area_name} towards {new_area.name} (via {best_direction_for_mission}) for their mission."
                    return {'message': msg, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}
                else:
                    # No direct connection, will fall through to general wandering with high desire.
                    pass # Fall through to general area change with boosted desire

            # 2. Shopping Travel (only if not on a mission or mission is in acquire phase for that item)
            if not (self.current_mission_type == "deliver_item" and self.mission_phase != "acquire_item"):
                if self.is_currently_shopping and self.shopping_target_item_name and not self.is_fleeing:
                    # ... (existing shopping travel logic to find 'chosen_shop_info') ...
                    # This is the block that finds potential_shops_to_visit etc.
                    # For brevity, assuming this block correctly sets chosen_shop_info
                    potential_shops_to_visit = [] # Placeholder for actual logic
                    for direction, connected_area in self.location.connections.items():
                        if hasattr(connected_area, 'shop_stock') and connected_area.shop_stock:
                            if self.shopping_target_item_name.lower() in connected_area.shop_stock:
                                potential_shops_to_visit.append({'direction': direction, 'area': connected_area, 'sells_target': True})
                            else:
                                potential_shops_to_visit.append({'direction': direction, 'area': connected_area, 'sells_target': False})
                    chosen_shop_info = None
                    if potential_shops_to_visit:
                        preferred_shops = [s for s in potential_shops_to_visit if s['sells_target']]
                        if preferred_shops: chosen_shop_info = random.choice(preferred_shops)
                        else: chosen_shop_info = random.choice(potential_shops_to_visit)

                    if chosen_shop_info: # If shopping travel decided on a move
                        old_area_name = self.location.name
                        new_area = chosen_shop_info['area']
                        chosen_direction = chosen_shop_info['direction']
                        self.set_location(new_area)
                        self.action_cooldown = random.randint(1, 3) # Shorter cooldown as it's purposeful
                        action_message = f"{self.name} heads from {old_area_name} towards {new_area.name} (via {chosen_direction}), looking for {self.shopping_target_item_name}."
                        return {'message': action_message, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

            # 3. Frustrated / General Wandering to New Area
            current_desire_to_change_area = self.desire_to_change_area_chance
            if self.shopping_frustration_cooldown > 1: # If recently frustrated by shopping (e.g. cooldown is 2+)
                # Significantly increase chance to leave if frustrated
                current_desire_to_change_area = max(current_desire_to_change_area, random.uniform(0.60, 0.85)) 
            elif self.current_mission_type == "deliver_item" and \
               self.mission_phase == "travel_to_area" and \
               self.location.name.lower() != self.mission_target_area_name.lower():
                # If mission travel didn't find a direct route, desire is high.
                current_desire_to_change_area = max(current_desire_to_change_area, 0.90) 

            if random.random() < current_desire_to_change_area:
                available_directions = list(self.location.connections.keys())
                if available_directions:
                    chosen_direction = random.choice(available_directions)
                    new_area = self.location.connections[chosen_direction]
                    old_area_name = self.location.name
                    self.set_location(new_area)
                    self.action_cooldown = random.randint(2, 5)
                    return {'message': f"{self.name} wanders from {old_area_name} towards the {chosen_direction} into {new_area.name}.", 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

        # 4. If no other action, random wander within current area
        if random.random() < 0.7: # 70% chance to wander if nothing else to do
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (0,0)]) # (0,0) for idle
            if dx !=0 or dy !=0:
                if self.move_on_grid(dx, dy):
                    action_message = f"{self.name} wanders around."
            self.action_cooldown = random.randint(1,3) # Cooldown after attempting to wander
            if action_message: # Only return if they actually wandered
                return {'message': action_message, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None}

        return {'message': None, 'purchase_info': None, 'flee_event': None, 'structured_action_details': None} # Default empty action


    def attempt_to_buy_from_shop(self, current_game_turn):
        """NPC attempts to buy an item from the current area's shop_stock."""
        if not self.location or not hasattr(self.location, 'shop_stock') or not self.location.shop_stock:
            return f"{self.name} looks around but there's nothing to buy here.", None

        # For now, NPC picks a random item from the shop to consider
        available_items = list(self.location.shop_stock.keys())
        if not available_items:
            return f"{self.name} browsed {self.location.name}, but it's empty.", None
        
        item_to_buy_key = None # This will be the lowercased key for shop_stock
        # Prioritize shopping_target_item_name if set by influence and available
        if self.shopping_target_item_name:
            target_key_lower = self.shopping_target_item_name.lower()
            if target_key_lower in available_items: # available_items are already lowercased keys
                item_to_buy_key = target_key_lower
        
        if not item_to_buy_key and available_items: # If no specific target, or target not found/available, pick randomly from eligible items
            eligible_random_items = [key for key in available_items if key not in self.recently_failed_to_buy]
            if eligible_random_items:
                item_to_buy_key = random.choice(eligible_random_items)
            else:
                # All available items were recently failed, or no items initially.
                self.is_currently_shopping = False # Stop active shopping if any
                return f"{self.name} browsed {self.location.name} but found nothing suitable or affordable right now.", None

        elif not item_to_buy_key and not available_items: # No target and no items
             return f"{self.name} browsed {self.location.name}, but it's empty.", None
        elif not item_to_buy_key and self.shopping_target_item_name: # Target item not in this shop
            # If they had a target but it's not here, they shouldn't pick randomly yet, they should try to find their target.
            # This case might be better handled by the logic that moves them to a shop.
            # For now, if they are in a shop and their target isn't here, they "give up" on it for this shop.
            failed_item_key = self.shopping_target_item_name.lower()
            self.recently_failed_to_buy[failed_item_key] = current_game_turn + random.randint(2,4)
            self.is_currently_shopping = False
            if self.active_influence_source_id: # If this was due to an influence
                self.recently_processed_influences[self.active_influence_source_id] = current_game_turn + random.randint(10, 20) # Cooldown for this specific influence
                self.active_influence_source_id = None
            return f"{self.name} was looking for {self.shopping_target_item_name}, but couldn't find it in {self.location.name}.", None
        elif not item_to_buy_key: # Should be caught by earlier conditions, but as a fallback
            return f"{self.name} is undecided in {self.location.name}.", None

        item_details = self.location.shop_stock[item_to_buy_key]
        item_prototype_name = item_details['prototype'].name # Get the proper name for messages

        if item_details['stock'] <= 0 and item_details['stock'] != float('inf'):
            self.action_cooldown = 1
            message = f"{self.name} wanted {item_prototype_name}, but it's out of stock."
            self.is_currently_shopping = False # Stop active shopping mode
            self.recently_failed_to_buy[item_to_buy_key] = current_game_turn + random.randint(3, 5)

            if self.shopping_target_item_name and self.shopping_target_item_name.lower() == item_to_buy_key:
                self.shopping_target_item_name = None
                if self.active_influence_source_id: # If this was due to an influence
                    self.recently_processed_influences[self.active_influence_source_id] = current_game_turn + random.randint(10, 20)
                    self.active_influence_source_id = None
                message += " They sigh and give up on finding it for now."
            return message, None

        if self.money >= item_details['price']:
            # Use the area's process_purchase method with the item_to_buy_key
            bought_item_instance, price = self.location.process_purchase(item_to_buy_key, self.money)
            if bought_item_instance:
                self.money -= price
                self.add_item_to_inventory(bought_item_instance)
                self.action_cooldown = random.randint(3, 5) # Cooldown after successful purchase
                # If this was their specific shopping target, reset flags
                if self.shopping_target_item_name and self.shopping_target_item_name.lower() == item_to_buy_key:
                    self.shopping_target_item_name = None # Fulfilled the craving
                    self.is_currently_shopping = False    # Stop active shopping mode
                    if self.active_influence_source_id: # If this was due to an influence
                        self.recently_processed_influences[self.active_influence_source_id] = current_game_turn + random.randint(10, 20)
                        self.active_influence_source_id = None
                purchase_details = {
                    'item_name': bought_item_instance.name,
                    'price': price,
                    'stock_symbol': self.location.associated_stock_symbol
                }
                return f"{self.name} bought {bought_item_instance.name} from {self.location.name} for ${price:.2f}.", purchase_details
            else: 
                # This case implies process_purchase failed for reasons other than stock/money,
                # which shouldn't happen with current Area.process_purchase logic if checks here are right.
                return f"{self.name} tried to buy {item_prototype_name} but something went wrong with the transaction.", None
        else:
            self.action_cooldown = random.randint(2, 4) # Cooldown to "save up" or "reconsider"
            message = f"{self.name} wants {item_prototype_name} (costs ${item_details['price']:.2f}), but cannot afford it."
            self.is_currently_shopping = False # Stop active shopping mode
            # Give up "permanently" if cannot afford, as money doesn't change for NPCs yet
            self.recently_failed_to_buy[item_to_buy_key] = current_game_turn + 99999 # Effectively permanent

            if self.shopping_target_item_name and self.shopping_target_item_name.lower() == item_to_buy_key:
                self.shopping_target_item_name = None
                if self.active_influence_source_id: # If this was due to an influence
                    self.recently_processed_influences[self.active_influence_source_id] = current_game_turn + random.randint(10, 20)
                    self.active_influence_source_id = None
                message += f" They decide they can't afford {item_prototype_name} right now."
            return message, None

    def start_fleeing(self, duration=5):
        """Makes the NPC start fleeing."""
        self.is_fleeing = True
        self.flee_timer = duration
        self.action_cooldown = 0 # Act immediately

    def _clear_mission_state(self):
        """Helper to reset all mission-related attributes."""
        self.current_mission_type = None
        self.mission_item_name = None
        self.mission_target_area_name = None
        self.mission_target_coords = None
        self.mission_phase = None
        self.active_mission_influence_id = None # This ID is for the mission influence, distinct from shopping one

    def get_status_info(self, current_game_turn):
        """Returns a string with the NPC's current status for debugging."""
        status = [
            f"--- Status for {self.name} (ID: {self.id}) ---",
            f"Location: {self.location.name if self.location else 'None'} at grid {self.get_grid_position()}",
            f"Money: ${self.money:.2f}",
            "Inventory:"
        ]
        if self.inventory:
            for item in self.inventory:
                status.append(f"  - {item.name}")
        else:
            status.append("  - Empty")
        
        status.append(f"Action Cooldown: {self.action_cooldown} turns")
        status.append(f"Shopping Frustration Cooldown: {self.shopping_frustration_cooldown} turns")
        status.append(f"Is Currently Shopping: {self.is_currently_shopping}")
        status.append(f"Shopping Target Item: {self.shopping_target_item_name if self.shopping_target_item_name else 'None'}")
        status.append(f"Active Shopping Influence ID: {self.active_influence_source_id if self.active_influence_source_id else 'None'}") # For shopping
        status.append(f"Is Fleeing: {self.is_fleeing}, Flee Timer: {self.flee_timer} turns")
        status.append("Recently Failed to Buy (Item: Expires in X turns):")
        if self.recently_failed_to_buy:
            for item_key, expiry_turn in self.recently_failed_to_buy.items():
                status.append(f"  - {item_key}: Expires in {expiry_turn - current_game_turn} turns (at turn {expiry_turn})")
        else:
            status.append("  - None")
        status.append("Recently Processed Influences (Source ID: Expires in X turns):")
        if self.recently_processed_influences:
            for source_id, expiry_turn in self.recently_processed_influences.items():
                status.append(f"  - {source_id}: Expires in {expiry_turn - current_game_turn} turns (at turn {expiry_turn})")
        status.append(f"Current Mission: {self.current_mission_type}, Item: {self.mission_item_name}, Target: {self.mission_target_area_name} at {self.mission_target_coords}, Phase: {self.mission_phase}")
        status.append(f"Active Mission Influence ID: {self.active_mission_influence_id if self.active_mission_influence_id else 'None'}")
        status.append(f"--- End Status (Game Turn: {current_game_turn}) ---")
        return "\n".join(status)

    def update(self, current_game_turn):
        """Called each game turn to allow NPC to perform actions."""
        return self.look_around_and_act(current_game_turn)
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
        
    def get_influenced_npcs(self):
        """Returns a list of NPCs that are currently influenced or on a mission."""
        influenced_npcs = []
        for npc in self.npcs.values():
            # Check if NPC is influenced for shopping
            if npc.is_currently_shopping and npc.shopping_target_item_name:
                influenced_npcs.append(npc)
            # Check if NPC is on a mission
            elif npc.current_mission_type:
                influenced_npcs.append(npc)
        return influenced_npcs

    def update_all_npcs(self, game_turn):
        messages = []
        
        # Safety check to ensure npcs is a dictionary
        if not isinstance(self.npcs, dict):
            print(f"Warning: NPC manager's npcs attribute is not a dictionary. It's a {type(self.npcs)}. Resetting to empty dictionary.")
            self.npcs = {}
            return messages
            
        # Iterate over a copy of values if NPCs could be removed during iteration, though not currently the case.
        for npc_obj in list(self.npcs.values()): 
            original_location = npc_obj.location # Capture location BEFORE action

            # npc.update() now returns a dictionary
            result = npc_obj.update(game_turn) 

            if result: # Ensure result is not None (e.g. if NPC is on cooldown and returns None/empty dict early)
                action_message = result.get('message')
                purchase_info = result.get('purchase_info')
                flee_event = result.get('flee_event')
                structured_action_details = result.get('structured_action_details')

                if action_message or purchase_info or flee_event or structured_action_details: # Only add if there's something to report
                    messages.append({'npc': npc_obj, 
                                     'action_message': action_message, 
                                     'purchase_info': purchase_info,
                                     'flee_event': flee_event,
                                     'structured_action_details': structured_action_details,
                                     'original_location_for_action': original_location})
        return messages