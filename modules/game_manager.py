
"""
Game Manager module for the game.
Handles game state, setup, and command processing.
"""
import random
from .player import Player
from .area import Area, AreaManager
from .item import Item, ItemManager
from .npc import NPC, NPCManager
from .coordinates import Coordinates
from .game_objects import Computer # Import Computer

class GameManager:
    """Manages the overall game state and systems."""
    def __init__(self):
        self.player = Player(start_money=500)
        self.area_manager = AreaManager()
        self.item_manager = ItemManager() # Simplified, items created directly for now
        self.npc_manager = NPCManager()
        self.running = True
        self.computers = [] # Keep track of all computer objects
        self.game_turn = 0

    def initialize_game(self):
        """Initialize the game with hardcoded areas, items, NPCs for testing."""
        print("Initializing game world...")

        # Create Areas
        park_origin = Coordinates(0,0,0)
        park = Area(name="Central Park", description="A grassy park with a few trees.", area_origin_coords=park_origin, grid_width=10, grid_length=10)
        self.area_manager.add_area(park)

        shop_origin = Coordinates(20,0,0) # Shop is to the east of the park
        shop = Area(name="General Store", description="A small store with various goods.", area_origin_coords=shop_origin, grid_width=8, grid_length=8)
        shop.associated_stock_symbol = "MALL" # Vita Mall Corp stock
        shop.is_shelter = True # The store is a shelter
        self.area_manager.add_area(shop)

        # Connect Areas
        # Park's east exit leads to Shop's west entrance
        self.area_manager.connect_areas(park.id, "east", shop.id)
        # Area.add_connection automatically adds reverse, so shop.west should connect to park.east

        # Create Items
        # Item1: Near NPC1 in Park
        red_ball = Item(name="Red Ball", description="A bouncy red ball.", value=5, coordinates=park.get_global_coordinates(3,3))
        park.add_object_to_grid(red_ball, 3, 3)
        self.item_manager.items_master_list[red_ball.id] = red_ball

        # Item2: Also near NPC1 in Park, but one step further
        blue_cube = Item(name="Blue Cube", description="A smooth blue cube.", value=10, coordinates=park.get_global_coordinates(3,4))
        park.add_object_to_grid(blue_cube, 3, 4)
        self.item_manager.items_master_list[blue_cube.id] = blue_cube

        # Item3: Far from NPC2 in Park
        green_pyramid = Item(name="Green Pyramid", description="A shiny green pyramid.", value=15, coordinates=park.get_global_coordinates(8,8))
        park.add_object_to_grid(green_pyramid, 8, 8)
        self.item_manager.items_master_list[green_pyramid.id] = green_pyramid

        # Item4: In the park, free
        yellow_star = Item(name="Yellow Star", description="A bright yellow star.", value=0, coordinates=park.get_global_coordinates(5,5))
        park.add_object_to_grid(yellow_star, 5, 5)
        self.item_manager.items_master_list[yellow_star.id] = yellow_star

        # Item5: In the shop
        # apple = Item(name="Apple", description="A juicy red apple.", value=2, coordinates=shop.get_global_coordinates(2,2))
        # shop.add_object_to_grid(apple, 2,2) # We won't put it on the floor if it's for sale via shop_stock
        # self.item_manager.items_master_list[apple.id] = apple

        # Stock the shop
        shop_apple_prototype = Item(name="Apple", description="A juicy red apple.", value=2)
        shop.add_item_to_shop(shop_apple_prototype, price=3.00, quantity=10) # Sell for $3
        shop_water_prototype = Item(name="Bottled Water", description="Clean drinking water.", value=1)
        shop.add_item_to_shop(shop_water_prototype, price=1.50, quantity=float('inf')) # Unlimited water


        # Create NPCs
        # NPC1: Near Item1 and Item2 in Park, has some money
        robo_coords = park.get_global_coordinates(3,2) # Robo starts at (3,2)
        robo = NPC(name="Robo", description="A small, curious robot.", start_coords=robo_coords, area=park, money=25)
        # robo.set_location(park, 3, 2) # This is now handled by add_object_to_grid if area is passed to NPC constructor
        park.add_object_to_grid(robo, 3, 2)
        self.npc_manager.add_npc(robo)

        # NPC2: Far from Item3 in Park
        zippy_coords = park.get_global_coordinates(1,8)
        zippy = NPC(name="Zippy", description="A fast-moving drone.", start_coords=zippy_coords, area=park, money=10) # Zippy has less money
        # zippy.set_location(park, 1, 8)
        park.add_object_to_grid(zippy, 1, 8)
        self.npc_manager.add_npc(zippy)


        # NPC3: Far from Zippy in Park
        gus_gus_coords = park.get_global_coordinates(5,5)
        gus_gus = NPC(name="Gus-Gus", description="A robotic cow.", start_coords=gus_gus_coords, area=park, money=50) # Gus-Gus has more money
        # gus_gus.set_location(park, 5, 5)
        park.add_object_to_grid(gus_gus, 5, 5)
        self.npc_manager.add_npc(gus_gus)

        # NPC3: Next to Gus-Gus in Park
        abertathur_coords = park.get_global_coordinates(6,5)
        abertathur = NPC(name="Abertathur", description="An old genie.", start_coords=abertathur_coords, area=park, money=75) # Abertathur has more money
        # abertathur.set_location(park, 6, 5)
        park.add_object_to_grid(abertathur, 6, 5)
        self.npc_manager.add_npc(abertathur)




        # Create and place a Computer
        stock_computer = Computer(name="Stock Terminal", description="A terminal for trading stocks.")
        # Place it in the shop, for example at grid (1,1)
        shop.add_object_to_grid(stock_computer, 1, 1)
        self.computers.append(stock_computer) # Add to list for updates

        # Place Player
        self.player.set_current_area(park, 1, 1)

        print("Game initialized.")
        self.player.look_around()

    def process_command(self, command_input):
        """Process a player command."""
        parts = command_input.lower().split()
        if not parts:
            return

        action = parts[0]
        args = parts[1:]

        if action in ["n", "north", "s", "south", "e", "east", "w", "west"]:
            direction_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
            self.player.move(direction_map.get(action, action))
        elif action == "look" or action == "l":
            self.player.look_around()
        elif action == "inventory" or action == "i":
            self.player.show_inventory()
        elif action == "get" or action == "take" or action == "pickup":
            if args:
                self.player.pick_up(" ".join(args))
            else:
                print("Pickup what?")
        elif action == "drop":
            if args:
                self.player.remove_item(" ".join(args)) # remove_item now handles dropping
            else:
                print("Drop what?")

        elif action == "buy":
            if args:
                item_to_buy = " ".join(args)
                success, bought_item, price, stock_symbol = self.player.buy_item(item_to_buy)
                if success and stock_symbol:
                    print(f"DEBUG: Purchase of {bought_item.name} for ${price} at {self.player.current_area.name} (Stock: {stock_symbol}) noted.")
                    for computer in self.computers:
                        if hasattr(computer, 'record_sale_for_stock'):
                            computer.record_sale_for_stock(stock_symbol, price)
            else:
                print("Buy what? (e.g., buy apple)")

        elif action == "interact":
            if not args:
                print("Interact with what?")
                return
            
            object_name_query = " ".join(args)
            player_gx, player_gy = self.player.get_grid_position()
            
            # Check objects at player's current cell
            objects_here = self.player.current_area.get_objects_at_grid_cell(player_gx, player_gy)
            target_object = None
            for obj in objects_here:
                if object_name_query.lower() in obj.name.lower():
                    target_object = obj
                    break
            
            if target_object and hasattr(target_object, 'interact'):
                target_object.interact(self.player)
            else:
                print(f"You don't see a '{object_name_query}' here to interact with.")
                
        elif action == "teleport" or action == "tp":
            if not args:
                print("Teleport where? Usage: tp <area_name> [x] [y]")
                return
            
            area_name_parts = []
            tp_x, tp_y = None, None
            
            # Try to parse coordinates at the end
            if len(args) >= 2 and args[-2].isdigit() and args[-1].isdigit():
                tp_x = int(args[-2])
                tp_y = int(args[-1])
                area_name_parts = args[:-2]
            elif len(args) >= 1 and args[-1].count(',') == 1 and all(p.isdigit() for p in args[-1].split(',')):
                try:
                    tp_x, tp_y = map(int, args[-1].split(','))
                    area_name_parts = args[:-1]
                except ValueError: # Not a coordinate pair
                    area_name_parts = args
            else: # No coordinates, all args are area name
                area_name_parts = args

            target_area_name = " ".join(area_name_parts)
            target_area = self.area_manager.get_area(target_area_name)
            
            if not target_area: # If no area name given, but coords were, assume current area
                if not area_name_parts and (tp_x is not None and tp_y is not None) and self.player.current_area:
                    target_area = self.player.current_area
                else:
                    print(f"Area '{target_area_name}' not found.")
                    return
            
            self.player.teleport(target_area, tp_x, tp_y) # Actually perform the teleport
        
        elif action == "scare":
            if not self.player.current_area:
                print("You shout into the void, but nothing happens.")
                return

            npcs_in_area = list(self.player.current_area.npcs) # Create a copy to iterate over
            if not npcs_in_area:
                print("You try to look menacing, but there's no one here to scare.")
                return

            print("You let out a terrifying shout!")
            for npc in npcs_in_area:
                if hasattr(npc, 'start_fleeing'):
                    npc.start_fleeing() # Default duration
        
        elif action == "birds" or action == "summon_birds":
            if not self.player.current_area:
                print("You whistle, but you're in a void. No birds answer.")
                return

            npcs_in_area = list(self.player.current_area.npcs) # Create a copy
            if not npcs_in_area:
                print("You summon a flock of birds, but there's no one around to appreciate (or fear) them.")
                return

            print("With a sharp whistle, you summon a chaotic flock of birds!")
            print("They dive and circle, causing a ruckus!")
            for npc in npcs_in_area:
                if hasattr(npc, 'start_fleeing'):
                    # We could potentially have different flee durations or intensities for different scares
                    npc.start_fleeing(duration=random.randint(4, 7)) # Birds might scare for a slightly varied time

        elif action == "where":
            if args:
                self.find_entity_coordinates(" ".join(args))
            else:
                # Player's own location
                if self.player.current_area:
                    gx, gy = self.player.get_grid_position()
                    print(f"You are in {self.player.current_area.name} at grid ({gx},{gy}). Global: {self.player.coordinates}")
                else:
                    print("You are nowhere.")
        elif action == "quit" or action == "exit":
            self.running = False
        else:
            print(f"Unknown command: {action}")

    def find_entity_coordinates(self, entity_name_query):
        """Find and print coordinates of NPCs or Items."""
        query = entity_name_query.lower()
        found = False
        for area in self.area_manager.areas.values():
            # Check NPCs in area
            for npc in area.npcs:
                if query in npc.name.lower():
                    npc_gx, npc_gy = area.get_relative_coordinates(npc.coordinates)[:2]
                    print(f"NPC '{npc.name}' found in {area.name} at grid ({int(npc_gx)},{int(npc_gy)}). Global: {npc.coordinates}")
                    found = True
            # Check Items in area
            for item in area.items:
                if query in item.name.lower():
                    item_gx, item_gy = area.get_relative_coordinates(item.coordinates)[:2]
                    print(f"Item '{item.name}' found in {area.name} at grid ({int(item_gx)},{int(item_gy)}). Global: {item.coordinates}")
                    found = True
        if not found:
            print(f"No entity matching '{entity_name_query}' found in any loaded area.")

    def _get_plural_verb_form(self, verb):
        """
        Converts a third-person singular present tense verb to its base form.
        E.g., "goes" -> "go", "has" -> "have", "scurries" -> "scurry", "seems" -> "seem".
        This is a simplified rule-based approach.
        """
        if verb == "is" or verb == "was": # These are special and usually change to "are"/"were"
            return verb # For this function's purpose, don't change them to base form like "be"

        if verb == "has":
            return "have"
        
        # Rule for verbs ending in "ies": change "ies" to "y"
        # (e.g., "tries" -> "try", "scurries" -> "scurry")
        if verb.endswith("ies"):
            return verb[:-3] + "y"

        # Rule for verbs ending in "es" after s, z, x, sh, ch
        # (e.g., "watches" -> "watch", "kisses" -> "kiss", "fixes" -> "fix", "buzzes" -> "buzz")
        # Also handles special "goes" -> "go", "does" -> "do"
        if verb.endswith("es"):
            if verb.endswith("ches") or verb.endswith("shes") or \
               verb.endswith("xes") or verb.endswith("zes") or verb.endswith("sses"):
                return verb[:-2]
            if verb == "goes" or verb == "does":
                return verb[:-2]

        # General rule for verbs ending in "s" (but not "ss", "us", "is")
        # (e.g., "seems" -> "seem", "wanders" -> "wander", "huddles" -> "huddle", "uses" -> "use")
        if verb.endswith("s"):
            if not (verb.endswith("ss") or verb.endswith("us") or verb.endswith("is")):
                if len(verb) > 1: 
                    return verb[:-1]
                    
        return verb # Return original if no rule matched or not applicable

    def _format_action_suffix_for_plural(self, message_suffix):
        words = message_suffix.split(' ', 1)
        first_word = words[0]
        rest_of_phrase = words[1] if len(words) > 1 else ""
        plural_verb = self._get_plural_verb_form(first_word)
        return plural_verb + (" " + rest_of_phrase if rest_of_phrase else "")

    def update_world(self):
        """Update game state, like NPC actions."""
        self.game_turn += 1

        # Update stock prices on all computers
        #for computer in self.computers:
        #    computer.update_stock_prices() # This will print changes if any
        
        processed_npc_ids_for_message = set() # Tracks NPCs whose flee actions are consolidated and printed
        
        npc_updates = self.npc_manager.update_all_npcs()

        # --- Consolidate Fleeing Messages ---
        if npc_updates:
            flee_groups = {} # Key: (origin_area_obj, old_area_name, new_area_name, direction), Value: list of npc_names
            
            for update_data in npc_updates:
                flee_event = update_data.get('flee_event')
                original_location = update_data.get('original_location_for_action')
                if flee_event and original_location == self.player.current_area:
                    # Only group events originating from player's current area for consolidated display
                    group_key = (
                        original_location, # Area object
                        flee_event['old_area_name'],
                        flee_event['new_area_name'],
                        flee_event['direction']
                    )
                    if group_key not in flee_groups:
                        flee_groups[group_key] = []
                    flee_groups[group_key].append(flee_event['npc_name']) # Store names for the message
                    processed_npc_ids_for_message.add(flee_event['npc_id']) # Mark as handled for individual message

            for key_info, names in flee_groups.items():
                _origin_area_obj, old_area_name, new_area_name, direction = key_info
                
                count = len(names)
                consolidated_message = ""
                if count == 1: # Should not happen if we only process groups > 1, but as fallback
                    consolidated_message = f"{names[0]} flees from {old_area_name} towards the {direction} into {new_area_name}!"
                elif count == 2:
                    consolidated_message = f"{names[0]} and {names[1]} flee from {old_area_name} towards the {direction} into {new_area_name}!"
                elif count >= 3:
                    # e.g., "Robo, Zippy, and 1 other flee..." or "Robo, Zippy, and 2 others flee..."
                    # For simplicity now: "Robo, Zippy, and X others..."
                    # Or just "{count} NPCs flee..."
                    # Let's use your suggestion: "{name1}, {name2}, and {remaining} others..." for 3+
                    if count == 3:
                         consolidated_message = f"{names[0]}, {names[1]}, and {names[2]} flee from {old_area_name} towards the {direction} into {new_area_name}!"
                    else: # More than 3
                        consolidated_message = f"{names[0]}, {names[1]}, {names[2]}, and {count - 3} others flee from {old_area_name} towards the {direction} into {new_area_name}!"
                
                if consolidated_message: # Check if a message was actually formed
                    print(consolidated_message)

        # --- Consolidate General NPC Action Messages ---
        # This set tracks NPCs whose general actions are consolidated and printed
        processed_npc_ids_for_action_grouping = set()
        action_message_groups = {} # Key: (message_suffix, original_location_obj), Value: list of npc_names

        if npc_updates:
            for update_data in npc_updates:
                npc = update_data['npc']
                action_message = update_data.get('action_message')
                original_location = update_data.get('original_location_for_action') # Area object where action occurred

                # Skip if this NPC's action was already part of a consolidated flee message
                if npc.id in processed_npc_ids_for_message:
                    continue

                if action_message and original_location:
                    # Determine if this action is visible/relevant to the player for grouping
                    action_is_visible_for_grouping = False
                    if npc.location == self.player.current_area: # NPC is currently in player's area
                        action_is_visible_for_grouping = True
                    elif original_location == self.player.current_area and npc.location != self.player.current_area:
                        # Action happened in player's current area, but NPC has since moved out.
                        # The message pertains to what happened in player's current area.
                        action_is_visible_for_grouping = True
                    
                    if action_is_visible_for_grouping:
                        npc_name = npc.name
                        # Ensure the message starts with the NPC's name followed by a space
                        if action_message.startswith(npc_name + " "):
                            message_suffix = action_message[len(npc_name) + 1:] # Get the part after "NpcName "
                            group_key = (message_suffix, original_location)
                            
                            action_message_groups.setdefault(group_key, []).append(npc_name)
                            processed_npc_ids_for_action_grouping.add(npc.id)

            # Print consolidated/single general action messages from groups
            # This should appear after flee messages are printed.
            for key_info, names in action_message_groups.items():
                message_suffix, _origin_area_obj = key_info
                count = len(names)
                
                effective_message_suffix = message_suffix
                if count > 1:
                    effective_message_suffix = self._format_action_suffix_for_plural(message_suffix)

                consolidated_message = ""
                if count == 1:
                    # For a single NPC, use the original message_suffix as it's already correctly conjugated
                    consolidated_message = f"{names[0]} {message_suffix}" 
                elif count == 2:
                    consolidated_message = f"{names[0]} and {names[1]} {effective_message_suffix}"
                elif count == 3:
                    consolidated_message = f"{names[0]}, {names[1]}, and {names[2]} {effective_message_suffix}"
                else: # count > 3
                    consolidated_message = f"{names[0]}, {names[1]}, {names[2]}, and {count - 3} others {effective_message_suffix}"
                
                if consolidated_message:
                    print(consolidated_message)

        # --- Handle Purchase Info and any other individual messages (e.g., not grouped) ---
        if npc_updates:
            for update_data in npc_updates:
                npc = update_data['npc']
                action_message = update_data.get('action_message')
                purchase_info = update_data.get('purchase_info')
                original_npc_location_for_action = update_data['original_location_for_action']

                # Print any action messages that were not handled by flee grouping or general action grouping
                if action_message and \
                   npc.id not in processed_npc_ids_for_message and \
                   npc.id not in processed_npc_ids_for_action_grouping:
                    
                    print_this_individual_message = False
                    if npc.location == self.player.current_area: # NPC is currently in player's area
                        print_this_individual_message = True
                    elif original_npc_location_for_action == self.player.current_area and npc.location != self.player.current_area: # NPC was in player's area and moved out
                        print_this_individual_message = True
                    
                    if print_this_individual_message:
                        print(action_message) # Print the original, full action message

                if purchase_info and purchase_info.get('stock_symbol'):
                    stock_symbol = purchase_info['stock_symbol'] 
                    price = purchase_info['price']                     
                    print(f"DEBUG: NPC Purchase by {npc.name} of {purchase_info['item_name']} for ${price} (Stock: {stock_symbol}) noted.")
                    for computer in self.computers:
                        if hasattr(computer, 'record_sale_for_stock'):
                            computer.record_sale_for_stock(stock_symbol, price)

    def run(self):
        """Main game loop."""
        print("\nWelcome to the Simplified Game!")
        print("Type 'quit' to exit.")
        
        while self.running:
            command_input = input("\n> ").strip()
            if command_input:
                self.process_command(command_input)
                if self.running: # Don't update world if quit command was issued
                    self.update_world() 
            elif self.running: # If empty input, still update world (pass turn)
                 self.update_world()

        print("Thanks for playing!")