
"""
Game Manager module for the game.
Handles game state, setup, and command processing.
"""
import os
import random
import sys # Required for stdout manipulation
from .player import Player
from .area import Area, AreaManager
from .item import Item, ItemManager
from .npc import NPC, NPCManager
from .coordinates import Coordinates
from .game_objects import Computer, InfluenceSource # Import Computer and InfluenceSource
from .save_system import SaveSystem
import json

class OutputMonitor:
    """
    A wrapper for sys.stdout to monitor if any actual text is written.
    """
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.texts_buffer = [] # Stores stripped text lines

    def write(self, text):
        # Add stripped, non-empty text to buffer
        stripped_text = text.strip()
        if stripped_text:
            self.texts_buffer.append(stripped_text)
        return self.original_stdout.write(text)

    def flush(self):
        return self.original_stdout.flush()

    def reset(self):
        """Clears the text buffer."""
        self.texts_buffer.clear()

    def get_buffered_texts_and_reset(self):
        """Returns a copy of buffered texts and clears the buffer."""
        texts = list(self.texts_buffer)
        self.texts_buffer.clear()
        return texts

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
        self._AMBIENT_NO_EVENT_MESSAGES = [
            "Time passes.",
            "The world is quiet for a moment.",
            "You take a breath; nothing remarkable happens right now.",
            "The air is still.",
            "A moment of calm.",
        ]
        # self.output_monitor will be initialized in run() or here if preferred
        
        # Initialize save system
        self.save_system = SaveSystem(self)

    def create_area_complex(self, complex_name, origin_coords, reference_area=None, reference_direction=None, distance=40):
        """
        Helper method to create a new area complex.
        
        Args:
            complex_name: Name of the complex
            origin_coords: Explicit coordinates, or None to calculate from reference
            reference_area: Area to position relative to (if origin_coords is None)
            reference_direction: Direction from reference area ('north', 'south', 'east', 'west')
            distance: Distance from reference area
            
        Returns:
            The created AreaGroup
        """
        if origin_coords is None and reference_area and reference_direction:
            # Calculate origin based on reference area and direction
            if reference_direction == "north":
                origin_coords = Coordinates(
                    reference_area.area_origin_coords.x,
                    reference_area.area_origin_coords.y - distance,
                    reference_area.area_origin_coords.z
                )
            elif reference_direction == "south":
                origin_coords = Coordinates(
                    reference_area.area_origin_coords.x,
                    reference_area.area_origin_coords.y + distance,
                    reference_area.area_origin_coords.z
                )
            elif reference_direction == "east":
                origin_coords = Coordinates(
                    reference_area.area_origin_coords.x + distance,
                    reference_area.area_origin_coords.y,
                    reference_area.area_origin_coords.z
                )
            elif reference_direction == "west":
                origin_coords = Coordinates(
                    reference_area.area_origin_coords.x - distance,
                    reference_area.area_origin_coords.y,
                    reference_area.area_origin_coords.z
                )
            else:
                # Default to same coordinates as reference area
                origin_coords = Coordinates(
                    reference_area.area_origin_coords.x,
                    reference_area.area_origin_coords.y,
                    reference_area.area_origin_coords.z
                )
        
        # Create and return the area group
        return self.area_manager.create_area_group(complex_name, origin_coords)
    
    def _initialize_mall_complex(self, park):
        """
        Initialize the mall complex to the west of the park.
        This demonstrates how to use the AreaGroup system to create a complex of connected areas.
        """
        from colors import print_colored, GameColors
        
        # Create a mall complex group with origin to the west of the park
        mall_group = self.create_area_complex("Vita Mall Complex", None, park, "west", 40)
        
        # Create the mall entrance area (this will be at the group's origin)
        mall_entrance = Area(
            name="Vita Mall Entrance", 
            description="A grand entrance to the Vita Mall. Gleaming glass doors welcome shoppers to a world of commerce.",
            grid_width=12, 
            grid_length=8
        )
        mall_entrance.associated_stock_symbol = "VMALL"  # Mall's stock symbol
        mall_group.add_area(mall_entrance, "center")
        
        # Create the main concourse/walkway
        main_concourse = Area(
            name="Main Concourse", 
            description="The central walkway of the mall. Shops line both sides, and the polished floor reflects the bright overhead lights.",
            grid_width=20, 
            grid_length=15
        )
        mall_group.add_area(main_concourse, {"from": mall_entrance.id, "direction": "west", "distance": 15})
        
        # Create the food court
        food_court = Area(
            name="Food Court", 
            description="A bustling food court with various eateries. The air is filled with delicious aromas.",
            grid_width=15, 
            grid_length=15
        )
        mall_group.add_area(food_court, {"from": main_concourse.id, "direction": "north", "distance": 20})
        
        # Create individual stores
        tech_store = Area(
            name="TechnoVita", 
            description="A sleek technology store selling the latest gadgets and electronics.",
            grid_width=10, 
            grid_length=8
        )
        tech_store.associated_stock_symbol = "TECH"  # Tech store stock symbol
        mall_group.add_area(tech_store, {"from": main_concourse.id, "direction": "south", "distance": 12})
        
        # Add a clothing store
        fashion_store = Area(
            name="VitaFashion", 
            description="A trendy clothing store with the latest styles.",
            grid_width=10, 
            grid_length=8
        )
        fashion_store.associated_stock_symbol = "VFASH"  # Fashion store stock symbol
        mall_group.add_area(fashion_store, {"from": main_concourse.id, "direction": "west", "distance": 15})
        
        # Add a luxury store
        luxury_store = Area(
            name="Luxe Vita", 
            description="An exclusive luxury goods store with high-end products.",
            grid_width=8, 
            grid_length=8
        )
        luxury_store.associated_stock_symbol = "LUXV"  # Luxury store stock symbol
        mall_group.add_area(luxury_store, {"from": fashion_store.id, "direction": "west", "distance": 12})
        
        # Connect areas within the mall manually for more control
        # Main connections
        mall_group.connect_areas_in_group(mall_entrance.id, "west", main_concourse.id)
        mall_group.connect_areas_in_group(main_concourse.id, "north", food_court.id)
        mall_group.connect_areas_in_group(main_concourse.id, "south", tech_store.id)
        mall_group.connect_areas_in_group(main_concourse.id, "west", fashion_store.id)
        mall_group.connect_areas_in_group(fashion_store.id, "west", luxury_store.id)
        
        # Add some items to the stores
        # Tech store items
        laptop = Item(name="Laptop", description="A high-performance laptop with the latest specs.")
        tech_store.add_item_to_shop(laptop, price=1200.00, quantity=5)
        
        smartphone = Item(name="Smartphone", description="The newest smartphone model with advanced features.")
        tech_store.add_item_to_shop(smartphone, price=800.00, quantity=10)
        
        # Fashion store items
        designer_jacket = Item(name="Designer Jacket", description="A stylish designer jacket that's all the rage.")
        fashion_store.add_item_to_shop(designer_jacket, price=350.00, quantity=8)
        
        luxury_watch = Item(name="Luxury Watch", description="An exquisite timepiece that exudes elegance.")
        luxury_store.add_item_to_shop(luxury_watch, price=5000.00, quantity=3)
        
        # Food court items
        pizza = Item(name="Pizza Slice", description="A delicious slice of pizza.")
        food_court.add_item_to_shop(pizza, price=4.50, quantity=float('inf'))
        
        soda = Item(name="Soda", description="A refreshing carbonated beverage.")
        food_court.add_item_to_shop(soda, price=2.00, quantity=float('inf'))
        
        # Add NPCs to the mall
        # Mall entrance security guard
        security_guard = NPC(
            name="Security Bot", 
            description="A robotic security guard monitoring the mall entrance.", 
            start_coords=mall_entrance.get_global_coordinates(6, 4),
            area=mall_entrance, 
            money=100
        )
        mall_entrance.add_object_to_grid(security_guard, 6, 4)
        self.npc_manager.add_npc(security_guard)
        
        # Food court vendor
        food_vendor = NPC(
            name="Chef Byte", 
            description="A cheerful robot chef running a popular food stall.", 
            start_coords=food_court.get_global_coordinates(7, 7),
            area=food_court, 
            money=250
        )
        food_court.add_object_to_grid(food_vendor, 7, 7)
        self.npc_manager.add_npc(food_vendor)
        
        # Tech store salesperson
        tech_salesperson = NPC(
            name="TechBot", 
            description="An enthusiastic robot with extensive knowledge of the latest gadgets.", 
            start_coords=tech_store.get_global_coordinates(5, 4),
            area=tech_store, 
            money=150
        )
        tech_store.add_object_to_grid(tech_salesperson, 5, 4)
        self.npc_manager.add_npc(tech_salesperson)
        
        # Fashion store assistant
        fashion_assistant = NPC(
            name="Styla", 
            description="A stylish robot with impeccable fashion sense.", 
            start_coords=fashion_store.get_global_coordinates(5, 4),
            area=fashion_store, 
            money=200
        )
        fashion_store.add_object_to_grid(fashion_assistant, 5, 4)
        self.npc_manager.add_npc(fashion_assistant)
        
        # Luxury store manager
        luxury_manager = NPC(
            name="Luxbot", 
            description="A sophisticated robot with an air of exclusivity.", 
            start_coords=luxury_store.get_global_coordinates(4, 4),
            area=luxury_store, 
            money=500
        )
        luxury_store.add_object_to_grid(luxury_manager, 4, 4)
        self.npc_manager.add_npc(luxury_manager)
        
        # Shopper in main concourse
        shopper = NPC(
            name="ShopperBot", 
            description="A robot browsing the stores with shopping bags in hand.", 
            start_coords=main_concourse.get_global_coordinates(10, 7),
            area=main_concourse, 
            money=300
        )
        main_concourse.add_object_to_grid(shopper, 10, 7)
        self.npc_manager.add_npc(shopper)
        
        # Register all mall areas with the main area manager
        self.area_manager.register_areas_from_group("Vita Mall Complex")
        
        # Connect the mall entrance to the park
        self.area_manager.connect_areas(park.id, "west", mall_entrance.id)
        
        print_colored("Mall complex initialized and connected to the park.", GameColors.SUCCESS_MESSAGE)
        
    def _initialize_tech_campus(self, reference_area):
        """
        Initialize a technology campus complex to the north of the reference area.
        This complex represents a high-tech research and development campus.
        """
        from colors import print_colored, GameColors
        
        # Create the tech campus group
        tech_campus_group = self.create_area_complex(
            "Vita Tech Campus", 
            None,
            reference_area, 
            "north", 
            40
        )
        
        # Create the main entrance/lobby
        campus_entrance = Area(
            name="Tech Campus Entrance", 
            description="A futuristic lobby with sleek glass walls and holographic displays welcoming visitors to the Vita Tech Campus.",
            grid_width=12, 
            grid_length=10
        )
        campus_entrance.associated_stock_symbol = "VTECH"  # Tech campus stock symbol
        tech_campus_group.add_area(campus_entrance, "center")
        
        # Create the research lab
        research_lab = Area(
            name="Research Laboratory", 
            description="A state-of-the-art laboratory with advanced equipment and robots working on cutting-edge technology.",
            grid_width=15, 
            grid_length=15
        )
        tech_campus_group.add_area(research_lab, {"from": campus_entrance.id, "direction": "north", "distance": 15})
        
        # Create the server room
        server_room = Area(
            name="Server Room", 
            description="A cold room filled with rows of humming servers. The digital heart of the campus.",
            grid_width=10, 
            grid_length=10
        )
        tech_campus_group.add_area(server_room, {"from": campus_entrance.id, "direction": "east", "distance": 15})
        
        # Create the cafeteria
        cafeteria = Area(
            name="Tech Cafeteria", 
            description="A modern cafeteria serving food to the campus workers. Screens on the walls display news and stock prices.",
            grid_width=12, 
            grid_length=12
        )
        tech_campus_group.add_area(cafeteria, {"from": campus_entrance.id, "direction": "west", "distance": 15})
        
        # Connect areas within the campus
        tech_campus_group.connect_areas_in_group(campus_entrance.id, "north", research_lab.id)
        tech_campus_group.connect_areas_in_group(campus_entrance.id, "east", server_room.id)
        tech_campus_group.connect_areas_in_group(campus_entrance.id, "west", cafeteria.id)
        
        # Add items to the areas
        # Research lab items
        prototype = Item(name="Prototype Device", description="A mysterious prototype device with unknown capabilities.")
        research_lab.add_item_to_shop(prototype, price=2000.00, quantity=1)
        
        # Server room items - add a computer for stock trading
        server_terminal = Computer(name="Advanced Server Terminal", description="A powerful terminal connected to the main servers.")
        server_room.add_object_to_grid(server_terminal, 5, 5)
        self.computers.append(server_terminal)
        
        # Cafeteria items
        energy_drink = Item(name="Tech Energy Drink", description="A highly caffeinated beverage popular among tech workers.")
        cafeteria.add_item_to_shop(energy_drink, price=5.00, quantity=float('inf'))
        
        # Add NPCs
        # Campus receptionist
        receptionist = NPC(
            name="ReceptoBot", 
            description="A helpful robot that greets visitors to the tech campus.", 
            start_coords=campus_entrance.get_global_coordinates(6, 5),
            area=campus_entrance, 
            money=150
        )
        campus_entrance.add_object_to_grid(receptionist, 6, 5)
        self.npc_manager.add_npc(receptionist)
        
        # Research scientist
        scientist = NPC(
            name="Dr. Circuit", 
            description="A brilliant robot scientist working on advanced AI algorithms.", 
            start_coords=research_lab.get_global_coordinates(7, 7),
            area=research_lab, 
            money=300
        )
        research_lab.add_object_to_grid(scientist, 7, 7)
        self.npc_manager.add_npc(scientist)
        
        # Server technician
        technician = NPC(
            name="TechBot", 
            description="A specialized robot that maintains the servers.", 
            start_coords=server_room.get_global_coordinates(3, 3),
            area=server_room, 
            money=200
        )
        server_room.add_object_to_grid(technician, 3, 3)
        self.npc_manager.add_npc(technician)
        
        # Register all campus areas with the main area manager
        self.area_manager.register_areas_from_group("Vita Tech Campus")
        
        # Connect the campus entrance to the reference area
        self.area_manager.connect_areas(reference_area.id, "north", campus_entrance.id)
        
        print_colored("Tech Campus initialized and connected to the park.", GameColors.SUCCESS_MESSAGE)
        
        return campus_entrance
    
    def _initialize_template_complex(self, reference_area, direction="north"):
        """
        Template method for creating a new area complex.
        Copy and modify this method to create new area complexes.
        
        Args:
            reference_area: The area to position the complex relative to
            direction: Direction from the reference area ('north', 'south', 'east', 'west')
        """
        from colors import print_colored, GameColors
        
        # Create the complex
        complex_group = self.create_area_complex(
            "Template Complex", 
            None,  # No explicit coordinates, calculate from reference
            reference_area, 
            direction, 
            40  # Distance from reference area
        )
        
        # Create the main area (entrance)
        main_area = Area(
            name="Template Main Area", 
            description="The main area of the template complex.",
            grid_width=10, 
            grid_length=10
        )
        complex_group.add_area(main_area, "center")
        
        # Create additional areas
        sub_area1 = Area(
            name="Template Sub Area 1", 
            description="A sub-area of the template complex.",
            grid_width=8, 
            grid_length=8
        )
        complex_group.add_area(sub_area1, {"from": main_area.id, "direction": "north", "distance": 15})
        
        sub_area2 = Area(
            name="Template Sub Area 2", 
            description="Another sub-area of the template complex.",
            grid_width=8, 
            grid_length=8
        )
        complex_group.add_area(sub_area2, {"from": main_area.id, "direction": "east", "distance": 15})
        
        # Connect areas within the complex
        complex_group.connect_areas_in_group(main_area.id, "north", sub_area1.id)
        complex_group.connect_areas_in_group(main_area.id, "east", sub_area2.id)
        
        # Add items and NPCs
        # [Add items and NPCs here]
        
        # Register all areas with the main area manager
        self.area_manager.register_areas_from_group("Template Complex")
        
        # Connect the complex to the reference area
        self.area_manager.connect_areas(reference_area.id, direction, main_area.id)
        
        print_colored("Template complex initialized and connected.", GameColors.SUCCESS_MESSAGE)
        
        # Return the main area for further connections
        return main_area
    
    def initialize_game(self):
        """Initialize the game with hardcoded areas, items, NPCs for testing."""
        # Import colors module
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from colors import print_colored, GameColors, format_info

        print_colored("Initializing game world...", GameColors.INFO_MESSAGE)

        # Create Areas
        park_origin = Coordinates(0,0,0)
        park = Area(name="Central Park", description="A grassy park with a few trees.", area_origin_coords=park_origin, grid_width=10, grid_length=10)
        self.area_manager.add_area(park)

        shop_origin = Coordinates(20,0,0) # Shop is to the east of the park
        shop = Area(name="General Store", description="A small store with various goods.", area_origin_coords=shop_origin, grid_width=8, grid_length=8)
        shop.associated_stock_symbol = "MALL" # Vita Mall Corp stock
        shop.is_shelter = True # The store is a shelter
        self.area_manager.add_area(shop)

        garden_origin = Coordinates(0, -20, 0) # Garden is south of the park
        garden = Area(name="Gray Bird Garden", description="A serene, slightly unsettling garden. A large, smooth stone sits in the center.", area_origin_coords=garden_origin, grid_width=7, grid_length=7)
        self.area_manager.add_area(garden)

        # Connect Areas
        # Park's east exit leads to Shop's west entrance
        self.area_manager.connect_areas(park.id, "east", shop.id)
        # Area.add_connection automatically adds reverse, so shop.west should connect to park.east

        # Park's south exit leads to Garden's north entrance
        self.area_manager.connect_areas(park.id, "south", garden.id)
        
        # Check if mall already exists before creating it
        mall_exists = any(area.name == "Vita Mall Entrance" for area in self.area_manager.areas.values())
        if not mall_exists:
            # Create the Mall Complex to the west of the park
            self._initialize_mall_complex(park)
        
        # Check if tech campus already exists before creating it
        tech_campus_exists = any(area.name == "Tech Campus Entrance" for area in self.area_manager.areas.values())
        if not tech_campus_exists:
            # Create the Tech Campus to the north of the park
            self._initialize_tech_campus(park)
        
        # Uncomment to add more complexes using the template
        # self._initialize_template_complex(park, "north")

        # Create Items
        # ... (existing item creation) ...
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
        park.add_object_to_grid(yellow_star, 2, 2)

        ysx = 3
        ysy = 3
        for i in range(5):
            ysx+=1
            ysy+=1
            park.add_object_to_grid(yellow_star, ysx, ysy)
            print(f"yellow star added to {ysx}, {ysy}")

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


        # Create Influence Sources
        # 1. Shopping Influence
        apple_advert = InfluenceSource(
            name="Shiny Apple Poster",
            description="A vibrant poster exclaiming 'An Apple a Day Keeps the Doctor Away! Buy Apples!'",
            action_type="shop",
            target_item_name="Apple", # Must match the name in shop_stock (case-insensitive later)
            influence_radius=4,  # NPCs within 4 grid cells might see it
            influence_strength=0.75 # 75% chance to be influenced if noticed
        )
        park.add_object_to_grid(apple_advert, 7, 7) # Place the poster in the park

        # 2. Delivery Influence for Gray Bird Garden
        offering_whisper = InfluenceSource(
            name="Mysterious Whisper Stone",
            description="A faint, almost inaudible whisper seems to emanate from this oddly smooth stone, urging devotion.",
            action_type="deliver_item",
            delivery_item_name="Yellow Star", # The item to be delivered
            delivery_target_area_name="Gray Bird Garden",
            delivery_target_coords=(garden.grid_width // 2, garden.grid_length // 2), # Center of the garden
            influence_radius=5,
            influence_strength=0.60
        )
        park.add_object_to_grid(offering_whisper, 2, 8) # Place this influence in the Park
        # Create NPCs
        # NPC1: Near Item1 and Item2 in Park, has some money
        robo_coords = park.get_global_coordinates(3,2) # Robo starts at (3,2)
        robo = NPC(name="Robo", description="A small, curious robot.", start_coords=robo_coords, area=park, money=25)
        # robo.set_location(park, 3, 2) # This is now handled by add_object_to_grid if area is passed to NPC constructor
        # Give Robo an item for testing dropping
        shiny_trinket = Item(name="Shiny Trinket", description="A small, glittering object.")
        robo.add_item_to_inventory(shiny_trinket)

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

        print_colored("Game initialized.", GameColors.SUCCESS_MESSAGE)
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
                    #print(f"DEBUG: Purchase of {bought_item.name} for ${price} at {self.player.current_area.name} (Stock: {stock_symbol}) noted.")
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
        elif action == "npcinfo":
            if args:
                npc_name_query = " ".join(args)
                self.show_npc_info(npc_name_query)
            else:
                print("Usage: npcinfo <npc_name>")
        elif action == "npc" and args and args[0] == "missions" or action == "npcmissions":
            self.show_npc_missions()
        elif action == "save":
            # Handle save command
            save_name = " ".join(args) if args else None
            save_path = self.save_system.save_game(save_name)
            if save_path:
                print(f"Game saved successfully to: {os.path.basename(save_path)}")
            else:
                print("Failed to save game.")
        
        elif action == "saveinfo":
            # Handle saveinfo command
            if not args:
                # List available saves with info if no save name provided
                saves = self.save_system.list_saves()
                if saves:
                    print("Available saves:")
                    for i, save in enumerate(saves, 1):
                        save_info = self.save_system.get_save_info(save)
                        if save_info:
                            version_status = "Up to date" if save_info['version'] == self.save_system.current_version else f"v{save_info['version']} (will upgrade to v{self.save_system.current_version})"
                            print(f"  {i}. {save} - {version_status}, Turn: {save_info['game_turn']}, Money: ${save_info['player_money']}")
                        else:
                            print(f"  {i}. {save} - Could not read save info")
                else:
                    print("No save files found.")
            else:
                save_name = " ".join(args)
                # Check if user entered a number instead of a name
                if save_name.isdigit():
                    try:
                        saves = self.save_system.list_saves()
                        if not saves:
                            print("No save files found.")
                            return
                            
                        index = int(save_name) - 1
                        if 0 <= index < len(saves):
                            save_name = saves[index]
                        else:
                            print(f"Invalid save number. Use a number between 1 and {len(saves)}.")
                            return
                    except Exception as e:
                        print(f"Error: {str(e)}")
                        return
                
                # Get and display detailed save info
                save_info = self.save_system.get_save_info(save_name)
                if save_info:
                    print(f"Save: {save_name}")
                    print(f"Version: {save_info['version']} (Current game version: {self.save_system.current_version})")
                    print(f"Timestamp: {save_info['timestamp']}")
                    print(f"Game Turn: {save_info['game_turn']}")
                    print(f"Player Money: ${save_info['player_money']}")
                    print(f"Areas: {save_info['area_count']}")
                    print(f"NPCs: {save_info['npc_count']}")
                    if save_info['upgrade_needed']:
                        print("This save will be upgraded to the current version when loaded.")
                        print("New areas (Mall Complex and Tech Campus) will be added.")
                else:
                    print(f"Could not read save info for {save_name}")
        elif action == "ver":
            # Display current game version
            print(f"Current game version: {self.save_system.current_version}")
        elif action == "areas":
            # Display list of areas
            self.area_manager.list_areas()
        elif action == "upgradesave" and args:
            # Force upgrade a save file without loading it
            save_name = " ".join(args)
            
            # Check if user entered a number instead of a name
            if save_name.isdigit():
                try:
                    saves = self.save_system.list_saves()
                    if not saves:
                        print("No save files found.")
                        return
                        
                    index = int(save_name) - 1
                    if 0 <= index < len(saves):
                        save_name = saves[index]
                    else:
                        print(f"Invalid save number. Use a number between 1 and {len(saves)}.")
                        return
                except Exception as e:
                    print(f"Error: {str(e)}")
                    return
            
            # Ensure save name has .json extension
            if not save_name.endswith('.json'):
                save_name += '.json'
                
            save_path = os.path.join(self.save_system.save_directory, save_name)
            
            # Check if save file exists
            if not os.path.exists(save_path):
                print(f"Save file '{save_name}' not found.")
                return
                
            try:
                # Load save data
                with open(save_path, 'r') as save_file:
                    save_data = json.load(save_file)
                
                # Get save version
                save_version = save_data.get('version', '1.0')
                
                if save_version == self.save_system.current_version:
                    print(f"Save is already at current version {save_version}. No upgrade needed.")
                    return
                    
                print(f"Forcing upgrade of save from version {save_version} to {self.save_system.current_version}...")
                
                # Create a backup
                backup_path = save_path + ".backup"
                import shutil
                shutil.copy2(save_path, backup_path)
                print(f"Created backup at {os.path.basename(backup_path)}")
                
                # Update version
                save_data['version'] = self.save_system.current_version
                
                # Save updated file
                with open(save_path, 'w') as save_file:
                    json.dump(save_data, save_file, indent=2)
                    
                print(f"Save file version updated to {self.save_system.current_version}")
                print("Note: This only updates the version number. To add new areas, load the save.")
                
            except Exception as e:
                print(f"Error upgrading save: {str(e)}")

                    
        elif action == "load":
            # Handle load command
            if not args:
                # List available saves if no save name provided
                saves = self.save_system.list_saves()
                if saves:
                    print("Available saves:")
                    for i, save in enumerate(saves, 1):
                        save_info = self.save_system.get_save_info(save)
                        version_info = f" (v{save_info['version']})" if save_info else ""
                        print(f"  {i}. {save}{version_info}")
                    print("Use 'load <save_name>' or 'load <number>' to load a specific save.")
                    print("Use 'saveinfo' to see detailed information about saves.")
                else:
                    print("No save files found.")
            else:
                save_name = " ".join(args)
                # Check if user entered a number instead of a name
                if save_name.isdigit():
                    try:
                        saves = self.save_system.list_saves()
                        if not saves:
                            print("No save files found.")
                            return
                            
                        index = int(save_name) - 1
                        if 0 <= index < len(saves):
                            save_name = saves[index]
                            print(f"Loading save #{index + 1}: {save_name}")
                        else:
                            print(f"Invalid save number. Use a number between 1 and {len(saves)}.")
                            return
                    except Exception as e:
                        print(f"Error processing save number: {str(e)}")
                        return
                
                try:
                    success = self.save_system.load_game(save_name)
                    if success:
                        print(f"Game loaded successfully from: {save_name}")
                        self.player.look_around()  # Show the player where they are
                    else:
                        print(f"Failed to load game from: {save_name}")
                except Exception as e:
                    print(f"Error loading game: {str(e)}")
        
        elif action == "saves":
            # List all available saves
            saves = self.save_system.list_saves()
            if saves:
                print("Available saves:")
                for i, save in enumerate(saves, 1):
                    print(f"  {i}. {save}")
            else:
                print("No save files found.")
                
        elif action == "help":
            self.show_help()
        else:
            print(f"Unknown command: {action}")

    def show_npc_info(self, npc_name_query):
        npc = self.npc_manager.get_npc(npc_name_query)
        if npc:
            print(npc.get_status_info(self.game_turn))
        else:
            print(f"NPC '{npc_name_query}' not found.")
            
    def show_help(self):
        """Shows a list of available commands."""
        # Import colors module
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from colors import colorize, GameColors, TextColor
        
        print(colorize("\n=== AVAILABLE COMMANDS ===", TextColor.BOLD + TextColor.BRIGHT_CYAN))
        
        commands = [
            ("Movement", "n, north, s, south, e, east, w, west", "Move in a direction"),
            ("Look", "look, l", "Look around your current location"),
            ("Inventory", "inventory, i", "Show your inventory"),
            ("Get Item", "get, take, pickup <item>", "Pick up an item"),
            ("Drop Item", "drop <item>", "Drop an item from your inventory"),
            ("Buy Item", "buy <item>", "Buy an item from a shop"),
            ("Interact", "interact <object>", "Interact with an object"),
            ("Teleport", "teleport, tp <area> [x] [y]", "Teleport to an area"),
            ("NPC Info", "npcinfo <npc>", "Show detailed info about an NPC"),
            ("NPC Missions", "npc missions, npcmissions", "Show all NPCs with active missions or influences"),
            ("Save Game", "save [name]", "Save your game progress (optional name)"),
            ("Load Game", "load [name|number]", "Load a saved game (name or number from list)"),
            ("List Saves", "saves", "List all available save files"),
            ("Save Info", "saveinfo [name|number]", "Show detailed information about saves"),
            ("Game Version", "ver", "Show current game version"),
            ("List Areas", "areas", "List all areas in the game"),
            ("Upgrade Save", "upgradesave [name|number]", "Force upgrade a save file to current version"),
            ("Help", "help", "Show this help message"),
            ("Quit", "quit, exit", "Exit the game")
        ]
        
        for category, cmd, desc in commands:
            print(f"{colorize(category + ':', TextColor.BOLD):<15} {colorize(cmd, GameColors.COMMAND_PROMPT):<30} {colorize(desc, GameColors.INFO_MESSAGE)}")
        
        print(colorize("\n=== END OF HELP ===", TextColor.BOLD + TextColor.BRIGHT_CYAN))
        
    def show_npc_missions(self):
        """Shows information about all NPCs that are currently influenced or on missions."""
        # Import colors module
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from colors import colorize, GameColors, format_npc_name, format_item_name, format_area_name, TextColor
        
        influenced_npcs = self.npc_manager.get_influenced_npcs()
        
        if not influenced_npcs:
            print(colorize("No NPCs are currently influenced or on missions.", GameColors.INFO_MESSAGE))
            return
            
        print(colorize("\n=== NPC MISSIONS AND INFLUENCES ===", TextColor.BOLD + TextColor.BRIGHT_CYAN))
        
        for npc in influenced_npcs:
            # Print NPC name and location
            print(f"\n{format_npc_name(npc.name)} at {format_area_name(npc.location.name if npc.location else 'Unknown')}")
            
            # If NPC is on a mission
            if npc.current_mission_type:
                mission_type = colorize(f"Mission Type: {npc.current_mission_type}", GameColors.NPC_INFLUENCE_ACTIVE)
                mission_item = colorize(f"Target Item: {format_item_name(npc.mission_item_name)}", GameColors.NPC_INFLUENCE_ACTIVE)
                mission_area = colorize(f"Target Area: {format_area_name(npc.mission_target_area_name)}", GameColors.NPC_INFLUENCE_ACTIVE)
                mission_coords = colorize(f"Target Coords: {npc.mission_target_coords}", GameColors.NPC_INFLUENCE_ACTIVE)
                mission_phase = colorize(f"Current Phase: {npc.mission_phase}", GameColors.NPC_INFLUENCE_ACTIVE)
                
                print(f"  {mission_type}")
                print(f"  {mission_item}")
                print(f"  {mission_area}")
                print(f"  {mission_coords}")
                print(f"  {mission_phase}")
                
                # Check if NPC has the mission item
                has_mission_item = False
                for item in npc.inventory:
                    if item.name.lower() == npc.mission_item_name.lower():
                        has_mission_item = True
                        break
                
                item_status = "Has Item: Yes" if has_mission_item else "Has Item: No"
                print(f"  {colorize(item_status, TextColor.BRIGHT_GREEN if has_mission_item else TextColor.BRIGHT_RED)}")
            
            # If NPC is influenced for shopping
            elif npc.is_currently_shopping and npc.shopping_target_item_name:
                shopping_target = colorize(f"Craving: {format_item_name(npc.shopping_target_item_name)}", GameColors.NPC_INFLUENCE_ACTIVE)
                print(f"  {shopping_target}")
                
                # Check if NPC has the shopping target item
                has_target_item = False
                for item in npc.inventory:
                    if item.name.lower() == npc.shopping_target_item_name.lower():
                        has_target_item = True
                        break
                
                item_status = "Has Item: Yes" if has_target_item else "Has Item: No"
                print(f"  {colorize(item_status, TextColor.BRIGHT_GREEN if has_target_item else TextColor.BRIGHT_RED)}")
                
                if npc.shopping_frustration_cooldown > 0:
                    frustration = colorize(f"Frustration Cooldown: {npc.shopping_frustration_cooldown} turns", TextColor.BRIGHT_RED)
                    print(f"  {frustration}")
        
        print(colorize("\n=== END OF NPC MISSIONS ===", TextColor.BOLD + TextColor.BRIGHT_CYAN))

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

        # Update stock prices on all computers first
        for computer in self.computers:
            if hasattr(computer, 'set_property'): # Ensure it's a computer object that can store game_turn
                computer.set_property('game_turn', self.game_turn)
            computer.update_stock_prices()
        
        # --- Initialize sets to track processed NPCs for different message types ---
        processed_npc_ids_for_message = set() # Tracks NPCs whose flee actions are consolidated and printed
        
        npc_updates = self.npc_manager.update_all_npcs(self.game_turn)

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

        # --- Consolidate Thematically Similar NPC Actions ---
        processed_npc_ids_for_thematic_grouping = set()
        thematic_action_groups = {} # Key: action_type, Value: list of {'npc_id', 'npc_name', **details}

        if npc_updates:
            for update_data in npc_updates:
                npc = update_data['npc']
                structured_details = update_data.get('structured_action_details')
                original_location = update_data.get('original_location_for_action')

                # Skip if already processed by flee grouping or if no structured details
                if npc.id in processed_npc_ids_for_message or not structured_details:
                    continue

                if original_location: # Ensure there's an original location
                    action_is_visible = (npc.location == self.player.current_area or \
                                         (original_location == self.player.current_area and npc.location != self.player.current_area))
                    
                    if action_is_visible:
                        action_type = structured_details['type']
                        action_data_for_grouping = {
                            'npc_id': npc.id,
                            'npc_name': npc.name,
                            **structured_details # Unpack all other details like target_coords, item_name
                        }
                        thematic_action_groups.setdefault(action_type, []).append(action_data_for_grouping)

            for action_type, actions_data_list in thematic_action_groups.items():
                if len(actions_data_list) >= 2: # Only group if 2 or more
                    if action_type == 'spotted_and_ran_to_coords':
                        # Sub-group by (target_coords, item_name) for contested items
                        contested_targets = {} # Key: (coords_tuple, item_name_str), Value: list of npc_data
                        remaining_runners_data = [] # For those not in a contested group of 2+

                        for npc_action_data in actions_data_list:
                            target_key = (
                                tuple(npc_action_data['target_coords']), # Ensure coords are hashable tuple
                                npc_action_data.get('item_name')
                            )
                            contested_targets.setdefault(target_key, []).append(npc_action_data)

                        for target_key, contenders_data in contested_targets.items():
                            target_coords_tuple, item_name_str = target_key
                            if len(contenders_data) >= 2:
                                # This is a contested item/spot
                                names = [data['npc_name'] for data in contenders_data]
                                if len(names) == 2:
                                    name_list_str = f"{names[0]} and {names[1]}"
                                else: # >= 3
                                    name_list_str = ", ".join(names[:-1]) + f", and {names[-1]}"
                                
                                item_desc = f" {item_name_str}" if item_name_str else " something"
                                consolidated_message = f"{name_list_str} both spotted{item_desc} at {target_coords_tuple} and rushed towards it, possibly about to argue over it!"
                                print(consolidated_message)
                                for data in contenders_data:
                                    processed_npc_ids_for_thematic_grouping.add(data['npc_id'])
                            else:
                                # Only one NPC for this specific target_key, add to remaining
                                remaining_runners_data.extend(contenders_data)

                        # Now handle the remaining_runners_data with the old "each spotted" logic if >= 2
                        if len(remaining_runners_data) >= 2:
                            names = [data['npc_name'] for data in remaining_runners_data]
                            if len(names) == 2:
                                name_list_str = f"{names[0]} and {names[1]}"
                            else: # >= 3
                                name_list_str = ", ".join(names[:-1]) + f", and {names[-1]}"

                            first_part = f"{name_list_str} each spotted something and ran."
                            
                            individual_clauses = []
                            for data in remaining_runners_data:
                                item_info = f" towards {data['item_name']}" if data.get('item_name') else ""
                                individual_clauses.append(f"{data['npc_name']} ran to {data['target_coords']}{item_info}")
                            
                            if len(remaining_runners_data) == 2:
                                second_part = f" {individual_clauses[0]} while {individual_clauses[1]}."
                            else: # >= 3
                                second_part = " " + "; ".join(individual_clauses) + "."
                                
                            consolidated_message = first_part + second_part
                            print(consolidated_message)
                            for data in remaining_runners_data: # Mark these as processed too
                                processed_npc_ids_for_thematic_grouping.add(data['npc_id'])
                        elif len(remaining_runners_data) == 1:
                            # If only one runner is left after contested groups, they will be handled by later individual message printing
                            # No action needed here for a single remaining runner.
                            pass
                        
                    # Add other action_type handlers here in the future
                    # Note: The printing and marking as processed is now handled within the
                    # 'spotted_and_ran_to_coords' block for its specific sub-groupings.
                    # If you add other action_types, ensure they also print and mark processed NPCs.
                    pass

        # --- Consolidate General NPC Action Messages ---
        # This set tracks NPCs whose general actions are consolidated by identical suffix
        processed_npc_ids_for_action_grouping = set()
        action_message_groups = {} # Key: (message_suffix, original_location_obj), Value: list of npc_names

        if npc_updates:
            for update_data in npc_updates:
                npc = update_data['npc']
                action_message = update_data.get('action_message')
                original_location = update_data.get('original_location_for_action') # Area object where action occurred

                # Skip if already processed by flee or thematic grouping
                if npc.id in processed_npc_ids_for_message or \
                   npc.id in processed_npc_ids_for_thematic_grouping:
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
                   npc.id not in processed_npc_ids_for_thematic_grouping and \
                   npc.id not in processed_npc_ids_for_action_grouping: # Check all three sets
                    
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
                    #print(f"DEBUG: NPC Purchase by {npc.name} of {purchase_info['item_name']} for ${price} (Stock: {stock_symbol}) noted.")
                    for computer in self.computers:
                        if hasattr(computer, 'record_sale_for_stock'):
                            computer.record_sale_for_stock(stock_symbol, price)

    def run(self):
        """Main game loop."""
        # Import colors module
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from colors import print_colored, colorize, GameColors, format_info, format_ambient

        print_colored("\nWelcome to Vita Game Hustle!", GameColors.PLAYER_NAME)
        print_colored("Type 'help' for a list of commands or 'quit' to exit.", GameColors.INFO_MESSAGE)

        original_stdout = sys.stdout
        output_monitor = OutputMonitor(original_stdout)
        sys.stdout = output_monitor

        while self.running:
            # The input() prompt itself will write to the monitor.
            # We reset the monitor's flag *after* the prompt and *before* game logic.
            command_input = input(f"\n{colorize('> ', GameColors.COMMAND_PROMPT)}").strip()
            
            output_monitor.reset() # Reset for game logic output for this turn

            if command_input:
                self.process_command(command_input)
                if self.running: # Don't update world if quit command was issued
                    self.update_world() 
            elif self.running: # If empty input, still update world (pass turn)
                 self.update_world()
            
            buffered_texts = output_monitor.get_buffered_texts_and_reset()

            if self.running:
                # Scenario 1: Absolutely nothing was printed by game logic this turn.
                if not buffered_texts:
                    print(format_ambient(random.choice(self._AMBIENT_NO_EVENT_MESSAGES)))
                # Scenario 2: Only a basic player movement confirmation or failure was printed.
                elif len(buffered_texts) == 1 and \
                     (buffered_texts[0].startswith("You move ") or \
                      buffered_texts[0] == "You can't go that way."):
                    print(format_ambient(random.choice(self._AMBIENT_NO_EVENT_MESSAGES)))
                # Otherwise, enough happened, or a different kind of single message was printed.

        sys.stdout = original_stdout # Restore original stdout
        print("Thanks for playing!") # This goes to the original stdout