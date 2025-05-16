
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

class GameManager:
    """Manages the overall game state and systems."""
    def __init__(self):
        self.player = Player(start_money=50)
        self.area_manager = AreaManager()
        self.item_manager = ItemManager() # Simplified, items created directly for now
        self.npc_manager = NPCManager()
        self.running = True
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
                self.player.buy_item(item_to_buy)
            else:
                print("Buy what? (e.g., buy apple)")
                
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
            
            self.player.teleport(target_area, tp_x, tp_y)

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


    def update_world(self):
        """Update game state, like NPC actions."""
        self.game_turn += 1
        # print(f"\n--- Turn {self.game_turn} ---") # Optional: For debugging turn progression
        self.npc_manager.update_all_npcs()
        # Other time-based updates could go here

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