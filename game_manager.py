"""
Game Manager module for Vita Game.
Handles game state, saving/loading, and overall game flow.
"""

import json
import os
import time
from .player import Player
from .area import Area, Building, AreaManager
from .items import Item, Food, Jetpack, Money, CraftingIngredient, ItemManager
from .game_objects import GameObject, Transport, Elevator, Door, Vehicle, Computer, VendingMachine, GameObjectManager
from .npc import NPC, NPCManager
from .crafting import Recipe, CraftingSystem
from .coordinates import Coordinates

class GameManager:
    """Manages the overall game state and systems."""
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.player = Player()
        self.area_manager = AreaManager()
        self.item_manager = ItemManager()
        self.object_manager = GameObjectManager()
        self.npc_manager = NPCManager()
        self.crafting_system = CraftingSystem(self.item_manager)
        self.game_time = 0  # In-game time in minutes
        self.running = True
        
        # Ensure data directory exists
        os.makedirs(data_dir, exist_ok=True)
    
    def initialize_game(self):
        """Initialize the game with default areas, items, NPCs, etc."""
        self.load_templates()
        self.create_starting_world()
        self.place_player_in_starting_area()
    
    def load_templates(self):
        """Load templates from JSON files."""
        # Load area templates
        area_templates_file = os.path.join(self.data_dir, "area_templates.json")
        if os.path.exists(area_templates_file):
            with open(area_templates_file, 'r') as f:
                self.area_manager.templates = json.load(f)
        
        # Load item templates
        item_templates_file = os.path.join(self.data_dir, "item_templates.json")
        if os.path.exists(item_templates_file):
            with open(item_templates_file, 'r') as f:
                self.item_manager.templates = json.load(f)
        
        # Load object templates
        object_templates_file = os.path.join(self.data_dir, "object_templates.json")
        if os.path.exists(object_templates_file):
            with open(object_templates_file, 'r') as f:
                self.object_manager.templates = json.load(f)
        
        # Load NPC templates
        npc_templates_file = os.path.join(self.data_dir, "npc_templates.json")
        if os.path.exists(npc_templates_file):
            with open(npc_templates_file, 'r') as f:
                self.npc_manager.templates = json.load(f)
        
        # Load crafting recipes
        recipe_file = os.path.join(self.data_dir, "recipes.json")
        if os.path.exists(recipe_file):
            self.crafting_system.load_from_json(recipe_file, self.item_manager.get_item)
    
    def create_starting_world(self):
        """Create the starting world with areas, items, NPCs, etc."""
        # Create areas
        self.create_starting_areas()
        
        # Create additional areas for Vita's hustle activities
        self.create_hustle_areas()
        
        # Create items
        self.create_starting_items()
        
        # Create NPCs
        self.create_starting_npcs()
        
        # Create objects
        self.create_starting_objects()
        
        # Create crafting recipes
        self.create_starting_recipes()
        
    def create_hustle_areas(self):
        """Create additional areas for Vita's hustle activities."""
        # Check if templates are loaded
        if not self.area_manager.templates:
            print("Warning: No area templates loaded. Cannot create hustle areas.")
            return
            
        # Create downtown area
        downtown = self.area_manager.create_area_from_template(
            "street",
            Coordinates(0, 20, 0),
            custom_name="Downtown",
            custom_description="The bustling downtown area with tall buildings and businesses."
        )
        
        # Connect downtown to street
        street = self.area_manager.get_area("street")
        if street and downtown:
            self.area_manager.connect_areas(street.id, "north", downtown.id)
        
        # Create apartment building in downtown
        apartment_building = self.area_manager.create_area_from_template(
            "apartment_building",
            Coordinates(5, 25, 0),
            custom_name="Luxury Apartments",
            custom_description="A high-end apartment building with multiple units for rent."
        )
        
        # Connect downtown to apartment building
        if downtown and apartment_building:
            self.area_manager.connect_areas(downtown.id, "east", apartment_building.id)
        
        # Create apartment floors and units
        if apartment_building and isinstance(apartment_building, Building):
            for floor in range(1, apartment_building.num_floors + 1):
                floor_area = self.area_manager.create_area_from_template(
                    "apartment_floor",
                    Coordinates(5, 25, floor - 1),
                    custom_name=f"Apartment Floor {floor}",
                    custom_description=f"Floor {floor} of the luxury apartment building."
                )
                
                if floor_area:
                    apartment_building.add_floor(floor, floor_area)
                    
                    # Add 4 apartment units per floor
                    for unit in range(1, 5):
                        unit_coords = Coordinates(5 + unit, 25 + unit, floor - 1)
                        unit_area = self.area_manager.create_area_from_template(
                            "apartment_unit",
                            unit_coords,
                            custom_name=f"Apartment {floor}{unit:02d}",
                            custom_description=f"Apartment unit {floor}{unit:02d} on floor {floor}."
                        )
                        
                        if unit_area and floor_area:
                            # Connect floor to unit
                            self.area_manager.connect_areas(floor_area.id, f"unit{unit}", unit_area.id)
        
        # Create a shopping mall
        mall = self.area_manager.create_area_from_template(
            "mall",
            Coordinates(15, 25, 0),
            custom_name="Grayton Mall",
            custom_description="A large shopping mall with various stores and shops."
        )
        
        # Connect downtown to mall
        if downtown and mall:
            self.area_manager.connect_areas(downtown.id, "northeast", mall.id)
        
        # Create stores inside the mall
        # First floor stores - create these regardless of whether mall is a Building
        convenience_store = self.area_manager.create_area_from_template(
            "convenience_store",
            Coordinates(16, 26, 0),
            custom_name="QuickMart",
            custom_description="A convenience store selling everyday items."
        )
        
        apparel_store = self.area_manager.create_area_from_template(
            "apparel_store",
            Coordinates(18, 28, 0),
            custom_name="Fashion Trends",
            custom_description="A trendy clothing store with the latest fashions."
        )
        
        cafe = self.area_manager.create_area_from_template(
            "cafe",
            Coordinates(20, 30, 0),
            custom_name="Bean Dreams",
            custom_description="A cozy cafe serving coffee and pastries."
        )
        
        # Connect mall to stores if mall exists
        if mall:
            if convenience_store:
                self.area_manager.connect_areas(mall.id, "store1", convenience_store.id)
            if apparel_store:
                self.area_manager.connect_areas(mall.id, "store2", apparel_store.id)
            if cafe:
                self.area_manager.connect_areas(mall.id, "store3", cafe.id)
                
            # If mall is a Building, add stores as floors
            if isinstance(mall, Building):
                if convenience_store:
                    mall.add_floor(1, convenience_store)
                if apparel_store:
                    mall.add_floor(2, apparel_store)
                if cafe:
                    mall.add_floor(3, cafe)
        
        # Create a bank
        bank = self.area_manager.create_area_from_template(
            "bank",
            Coordinates(10, 20, 0),
            custom_name="First National Bank",
            custom_description="A secure bank for managing finances."
        )
        
        # Connect downtown to bank
        if downtown and bank:
            self.area_manager.connect_areas(downtown.id, "west", bank.id)
        
        # Create a tech company
        tech_company = self.area_manager.create_area_from_template(
            "tech_company",
            Coordinates(-10, 20, 0),
            custom_name="BunnyTech Inc.",
            custom_description="A cutting-edge technology company with investment opportunities."
        )
        
        # Connect downtown to tech company
        if downtown and tech_company:
            self.area_manager.connect_areas(downtown.id, "northwest", tech_company.id)
        
        # Create a restaurant
        restaurant = self.area_manager.create_area_from_template(
            "restaurant",
            Coordinates(5, 15, 0),
            custom_name="Carrot Cuisine",
            custom_description="An upscale restaurant serving gourmet vegetable dishes."
        )
        
        # Connect street to restaurant
        if street and restaurant:
            self.area_manager.connect_areas(street.id, "northeast", restaurant.id)
    
    def create_starting_areas(self):
        """Create the starting areas for the game."""
        # Check if templates are loaded
        if not self.area_manager.templates:
            print("Warning: No area templates loaded. Using default areas.")
            self.create_default_areas()
            return
            
        # Create areas from templates
        # Create park area
        park = self.area_manager.create_area_from_template(
            "park", 
            Coordinates(0, 0, 0),
            custom_description="A peaceful park with trees, benches, and a small pond."
        )
        
        # Create street area
        street = self.area_manager.create_area_from_template(
            "street", 
            Coordinates(0, 10, 0)
        )
        
        # Create suburbs area
        suburbs = self.area_manager.create_area_from_template(
            "suburbs", 
            Coordinates(15, 10, 0)
        )
        
        # Create a house in the suburbs
        house = self.area_manager.create_area_from_template(
            "house", 
            Coordinates(20, 15, 0),
            custom_description="A cozy suburban house with a small garden."
        )
        
        # Create office building
        office_building = self.area_manager.create_area_from_template(
            "office_building", 
            Coordinates(10, 0, 0)
        )
        
        # Create floors for the office building
        if office_building and isinstance(office_building, Building):
            for floor in range(1, 6):
                floor_area = self.area_manager.create_area_from_template(
                    "office_floor",
                    Coordinates(10, 0, floor - 1),
                    custom_name=f"Office Floor {floor}",
                    custom_description=f"Floor {floor} of the office building."
                )
                if floor_area:
                    office_building.add_floor(floor, floor_area)
        
        # Connect areas if they were created successfully
        if park and street:
            self.area_manager.connect_areas(park.id, "north", street.id)
        if street and suburbs:
            self.area_manager.connect_areas(street.id, "east", suburbs.id)
        if suburbs and house:
            self.area_manager.connect_areas(suburbs.id, "north", house.id)
        if park and office_building:
            self.area_manager.connect_areas(park.id, "east", office_building.id)
            
    def create_default_areas(self):
        """Create default areas when templates are not available."""
        # Create park area
        park = Area(
            "Park",
            "A peaceful park with trees, benches, and a small pond.",
            Coordinates(0, 0, 0),
            grid_width=10,
            grid_length=10
        )
        self.area_manager.add_area(park)
        
        # Create street area
        street = Area(
            "Street",
            "A busy city street with shops and traffic.",
            Coordinates(0, 10, 0),
            grid_width=15,
            grid_length=5
        )
        self.area_manager.add_area(street)
        
        # Create suburbs area
        suburbs = Area(
            "Suburbs",
            "A quiet suburban neighborhood with houses.",
            Coordinates(15, 10, 0),
            grid_width=20,
            grid_length=10
        )
        self.area_manager.add_area(suburbs)
        
        # Create a house in the suburbs
        house = Area(
            "House",
            "A cozy suburban house with a small garden.",
            Coordinates(20, 15, 0),
            grid_width=5,
            grid_length=5
        )
        self.area_manager.add_area(house)
        
        # Create office building
        office_building = Building(
            "Office Building",
            "A tall office building with multiple floors.",
            Coordinates(10, 0, 0),
            num_floors=5,
            grid_width=8,
            grid_length=8
        )
        self.area_manager.add_area(office_building)
        
        # Create floors for the office building
        for floor in range(1, 6):
            floor_area = Area(
                f"Office Floor {floor}",
                f"Floor {floor} of the office building.",
                Coordinates(10, 0, floor - 1),
                grid_width=8,
                grid_length=8
            )
            self.area_manager.add_area(floor_area)
            office_building.add_floor(floor, floor_area)
        
        # Connect areas
        self.area_manager.connect_areas(park.id, "north", street.id)
        self.area_manager.connect_areas(street.id, "east", suburbs.id)
        self.area_manager.connect_areas(suburbs.id, "north", house.id)
        self.area_manager.connect_areas(park.id, "east", office_building.id)
    
    def create_starting_items(self):
        """Create the starting items for the game."""
        # Create a jetpack
        jetpack = Jetpack(
            "Standard Jetpack",
            "A basic jetpack that allows you to fly.",
            fuel=100,
            max_fuel=100,
            fuel_efficiency=1.0
        )
        self.item_manager.add_item(jetpack)
        
        # Create some food items
        carrot = Food(
            "Carrot",
            "A fresh orange carrot. Good for bunnies!",
            nutrition=15,
            effects={"energy": 10}
        )
        self.item_manager.add_item(carrot)
        
        apple = Food(
            "Apple",
            "A juicy red apple.",
            nutrition=20,
            effects={"energy": 15}
        )
        self.item_manager.add_item(apple)
        
        # Create some money
        money = Money(50)
        self.item_manager.add_item(money)
        
        # Create crafting ingredients
        metal = CraftingIngredient(
            "Metal Scrap",
            "A piece of scrap metal. Useful for crafting.",
            "metal",
            value=10
        )
        self.item_manager.add_item(metal)
        
        fabric = CraftingIngredient(
            "Fabric",
            "A piece of fabric. Useful for crafting.",
            "fabric",
            value=5
        )
        self.item_manager.add_item(fabric)
        
        # Place items in areas
        park = self.area_manager.get_area("park")
        if park:
            park.place_object_at(carrot, 3, 3)
            park.place_object_at(jetpack, 5, 5)
        
        house = self.area_manager.get_area("house")
        if house:
            house.place_object_at(apple, 2, 2)
            house.place_object_at(metal, 3, 3)
            house.place_object_at(fabric, 4, 4)
    
    def create_starting_npcs(self):
        """Create the starting NPCs for the game."""
        # Create a squirrel NPC
        squirrel = NPC(
            "Squirrel",
            "A bushy-tailed squirrel looking for acorns.",
            dialogue={
                "default": "Squeak! (He seems to be looking for acorns.)",
                "friendly": "Squeak squeak! (He seems happy to see you.)"
            },
            personality={
                "nervousness": 70,
                "friendliness": 50
            },
            money=10
        )
        self.npc_manager.add_npc(squirrel)
        
        # Create a random guy NPC
        Dave = NPC(
            "Dave",
            "An average civilian.",
            dialogue={
                "default": "Whoa, are you the gray bird I've been hearing about?",
                "friendly": "Sup, gray bird? I mean-uh, your highness?"
            }, 
            personality={
                "friendliness": 60,
                "greed": 40
            },
            money=500
        )
        self.npc_manager.add_npc(Dave)
        
        # Place NPCs in areas
        park = self.area_manager.get_area("park")
        if park:
            park.place_object_at(squirrel, 7, 7)
        
        street = self.area_manager.get_area("street")
        if street:
            street.place_object_at(Dave, 5, 2)
            
        # Add NPCs to Fashion Trends store
        self.populate_fashion_trends_store()
        
    def populate_fashion_trends_store(self):
        """
        Populate the Fashion Trends store with NPCs and clothing items.
        
        # AREA POPULATION: This method shows how to add NPCs and items to an area
        
        This method:
        1. Finds the Fashion Trends store
        2. Adds clothing items to the store
        3. Creates 5 NPCs with shopping interests
        4. Places the NPCs in the store
        """
        # Find the Fashion Trends store
        fashion_trends = None
        mall = self.area_manager.get_area("grayton_mall")
        
        # If we can't find it directly, look for it in all areas
        if not fashion_trends:
            for area in self.area_manager.areas.values():
                if area.name == "Fashion Trends":
                    fashion_trends = area
                    break
        
        # If still not found, it might not have been created yet
        if not fashion_trends:
            print("Warning: Fashion Trends store not found. Cannot populate with NPCs.")
            return
            
        # Add clothing items to the store
        try:
            # Create items with proper error handling
            clothing_items = [
                {"template": "T-shirt", "position": (1, 1)},
                {"template": "Skirt", "position": (1, 2)},
                {"template": "Pants", "position": (2, 1)},
                {"template": "Shoes", "position": (2, 2)},
                {"template": "Hat", "position": (3, 1)},
                {"template": "Backpack", "position": (3, 2)},
                {"template": "Headband", "position": (4, 1)}
            ]
            
            # Try to create each item
            for item_info in clothing_items:
                try:
                    item = self.item_manager.create_from_template(item_info["template"])
                    if item:
                        fashion_trends.place_object_at(item, item_info["position"][0], item_info["position"][1])
                        print(f"Added {item.name} to Fashion Trends store")
                except ValueError as e:
                    print(f"Error creating {item_info['template']}: {e}")
                    
                    # If template not found, create the item directly
                    from modules.items import Item
                    
                    # Get template data from JSON file
                    template_data = None
                    try:
                        with open(os.path.join(self.data_dir, "item_templates.json"), 'r') as f:
                            templates = json.load(f)
                            if item_info["template"] in templates:
                                template_data = templates[item_info["template"]]
                    except Exception as json_err:
                        print(f"Error loading template data: {json_err}")
                    
                    # Create item directly if we have template data
                    if template_data:
                        item = Item(
                            template_data.get("name", item_info["template"]),
                            template_data.get("description", "A clothing item."),
                            template_data.get("type", "Clothing"),
                            template_data.get("value", 20)
                        )
                        fashion_trends.place_object_at(item, item_info["position"][0], item_info["position"][1])
                        print(f"Created {item.name} directly and added to Fashion Trends store")
        except Exception as e:
            print(f"Error adding clothing items: {e}")
            
        # Create 5 NPCs with shopping interests
        for i in range(1, 6):
            # Create a shopper NPC
            shopper = NPC(
                f"Shopper {i}",
                f"A person shopping for clothes.",
                dialogue={
                    "default": "I'm just looking around for some new clothes.",
                    "friendly": "Hey there! Do you think this would look good on me?"
                },
                personality={
                    "friendliness": 50,
                    "fashion_sense": 70
                },
                money=100 + (i * 20)  # Give each shopper a different amount of money
            )
            
            # Set shopping preference
            shopper.set_property("likes_shopping", True)
            
            # Add to manager
            self.npc_manager.add_npc(shopper)
            
            # Place in store at different positions
            fashion_trends.place_object_at(shopper, i, 3)
            
        # Add a store clerk
        clerk = NPC(
            "Store Clerk",
            "A helpful employee of Fashion Trends.",
            dialogue={
                "default": "Welcome to Fashion Trends! Let me know if you need any help.",
                "friendly": "Great to see you again! We just got some new items in stock."
            },
            personality={
                "friendliness": 80,
                "helpfulness": 90
            },
            money=200
        )
        self.npc_manager.add_npc(clerk)
        fashion_trends.place_object_at(clerk, 4, 4)
        
        print(f"Added 5 shoppers and a clerk to Fashion Trends store with clothing items.")
    
    def create_starting_objects(self):
        """Create the starting objects for the game."""
        # Create an elevator in the office building
        elevator = Elevator(
            "Office Elevator",
            "An elevator that can take you to different floors of the office building."
        )
        self.object_manager.add_object(elevator)
        
        # Add floors to the elevator
        office_building = self.area_manager.get_area("office_building")
        if office_building and isinstance(office_building, Building):
            for floor_num, floor_area in office_building.floors.items():
                elevator.add_floor(floor_num, floor_area, 4, 4)  # Place elevator at center of each floor
        
        # Place elevator in the office building
        if office_building:
            office_building.place_object_at(elevator, 4, 4)
        
        # Create a car on the street
        car = Vehicle(
            "Car",
            "A standard car that can be driven around.",
            speed=3,
            fuel=100,
            max_fuel=100
        )
        self.object_manager.add_object(car)
        
        # Place car on the street
        street = self.area_manager.get_area("street")
        if street:
            street.place_object_at(car, 10, 2)
        
        # Create a door between the suburbs and the house
        door = Door(
            "House Door",
            "The front door of the house."
        )
        self.object_manager.add_object(door)
        
        # Set door destination
        house = self.area_manager.get_area("house")
        suburbs = self.area_manager.get_area("suburbs")
        if house and suburbs:
            door.set_destination(house, 2, 4)  # Enter at the front of the house
            suburbs.place_object_at(door, 18, 8)  # Place door in suburbs
    
    def create_starting_recipes(self):
        """Create the starting crafting recipes."""
        # Create a recipe for an upgraded jetpack
        upgraded_jetpack = {
            "type": "Jetpack",
            "name": "Upgraded Jetpack",
            "description": "An improved jetpack with better fuel efficiency.",
            "fuel": 150,
            "max_fuel": 150,
            "fuel_efficiency": 0.7,
            "value": 800
        }
        
        jetpack_recipe = Recipe(
            "Upgraded Jetpack",
            "Craft an improved jetpack with better fuel efficiency.",
            {
                "Jetpack": 1,
                "Metal Scrap": 3,
                "Fabric": 2
            },
            upgraded_jetpack,
            {"engineering": 1}
        )
        self.crafting_system.add_recipe(jetpack_recipe)
        
        # Create a recipe for a health potion
        health_potion = {
            "type": "Food",
            "name": "Health Potion",
            "description": "A potion that restores health and energy.",
            "nutrition": 30,
            "effects": {"energy": 50},
            "value": 30
        }
        
        potion_recipe = Recipe(
            "Health Potion",
            "Craft a potion that restores health and energy.",
            {
                "Apple": 2,
                "Carrot": 1
            },
            health_potion,
            {"alchemy": 1}
        )
        self.crafting_system.add_recipe(potion_recipe)
    
    def place_player_in_starting_area(self):
        """Place the player in the starting area."""
        starting_area = self.area_manager.get_area("park")
        if starting_area:
            self.player.set_current_area(starting_area, 5, 5)
            
            # Give player some starting items
            money = Money(100)
            self.player.add_item(money)
            self.player.money = 100
    
    def save_game(self, filename="savegame.json"):
        """Save the current game state to a file."""
        save_path = os.path.join(self.data_dir, filename)
        
        # Create save data
        save_data = {
            "player": self.player.to_dict(),
            "game_time": self.game_time
        }
        
        # Save to file
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=4)
        
        print(f"Game saved to {save_path}")
    
    def load_game(self, filename="savegame.json"):
        """Load a game state from a file."""
        save_path = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(save_path):
            print(f"Save file {save_path} not found.")
            return False
        
        try:
            with open(save_path, 'r') as f:
                save_data = json.load(f)
            
            # Load game time
            self.game_time = save_data.get("game_time", 0)
            
            # Load player
            player_data = save_data.get("player", {})
            self.player = Player.from_dict(
                player_data,
                self.area_manager.get_area,
                self.item_manager.get_item,
                self.object_manager.get_object
            )
            
            print(f"Game loaded from {save_path}")
            return True
        except Exception as e:
            print(f"Error loading game: {e}")
            return False
    
    def update_game_time(self, minutes=1):
        """Update the game time and related systems."""
        self.game_time += minutes
        
        # Update NPCs based on time, passing the player for influence checks
        self.npc_manager.update_all_npcs(self.game_time, self.player)
        
        # Update player hunger
        self.player.hunger = min(self.player.max_hunger, self.player.hunger + minutes * 0.1)
        
        # Check if player is too hungry
        if self.player.hunger >= self.player.max_hunger:
            print("You're starving! You need to eat something.")
            self.player.energy = max(0, self.player.energy - minutes)
            
            # Check if player has no energy
            if self.player.energy <= 0:
                print("You collapsed from hunger and exhaustion!")
                # In a real game, this might trigger a game over or respawn
    
    def process_command(self, command):
        """Process a player command."""
        parts = command.lower().split()
        if not parts:
            return
        
        action = parts[0]
        
        # Movement commands
        if action in ["north", "south", "east", "west", "forward", "backward", "right", "left"]:
            self.player.move(action)
        
        # Look command
        elif action == "look":
            self.player.look_around()
        
        # Inventory command
        elif action == "inventory":
            self.show_inventory()
        
        # Pick up command
        elif action in ["pickup", "take", "get", "grab"]:
            if len(parts) > 1:
                item_name = " ".join(parts[1:])
                self.player.pick_up(item_name)
            else:
                print("What do you want to pick up?")
        
        # Drop command
        elif action == "drop":
            if len(parts) > 1:
                item_name = " ".join(parts[1:])
                self.player.drop(item_name)
            else:
                print("What do you want to drop?")
        
        # Use command
        elif action == "use":
            if len(parts) > 1:
                item_name = " ".join(parts[1:])
                self.player.use(item_name)
            else:
                print("What do you want to use?")
        
        # Eat command
        elif action == "eat":
            if len(parts) > 1:
                item_name = " ".join(parts[1:])
                self.player.eat(item_name)
            else:
                print("What do you want to eat?")
        
        # Talk command
        elif action == "talk":
            if len(parts) > 1:
                npc_name = " ".join(parts[1:])
                self.player.talk_to(npc_name)
            else:
                print("Who do you want to talk to?")
        
        # Interact command
        elif action == "interact":
            if len(parts) > 1:
                object_name = " ".join(parts[1:])
                self.player.interact_with(object_name)
            else:
                print("What do you want to interact with?")
        
        # Jetpack commands
        elif action == "fly":
            if len(parts) > 1:
                direction = parts[1]
                if self.player.is_flying:
                    self.player.fly(direction)
                else:
                    print("You need to activate your jetpack first.")
            else:
                print("Which direction do you want to fly?")
        
        elif action == "activate":
            if len(parts) > 1 and parts[1] == "jetpack":
                self.player.activate_jetpack()
            else:
                print("What do you want to activate?")
        
        elif action == "deactivate":
            if len(parts) > 1 and parts[1] == "jetpack":
                self.player.deactivate_jetpack()
            else:
                print("What do you want to deactivate?")
        
        # Crafting command
        elif action == "craft":
            if len(parts) > 1:
                recipe_name = " ".join(parts[1:])
                self.player.craft(recipe_name, self.crafting_system)
            else:
                self.show_crafting_menu()
        
        # Investment commands
        elif action == "invest":
            if len(parts) >= 3:
                try:
                    amount = int(parts[1])
                    business = " ".join(parts[2:])
                    self.player.invest(business, amount)
                except ValueError:
                    print("Invalid amount. Please enter a number.")
            else:
                print("Usage: invest [amount] [business]")
        
        elif action == "investments":
            self.player.check_investments()
        
        # Save and load commands
        elif action == "save":
            if len(parts) > 1:
                filename = parts[1] + ".json"
                self.save_game(filename)
            else:
                self.save_game()
        
        elif action == "load":
            if len(parts) > 1:
                filename = parts[1] + ".json"
                self.load_game(filename)
            else:
                self.load_game()
        
        # Help command
        elif action == "help":
            self.show_help()


        # Position/coordinates command
        elif action in ["position", "pos", "coordinates", "coords", "where"]:
            # If no arguments, show player's position
            if len(parts) == 1:
                if self.player.current_area:
                    grid_x, grid_y, grid_z = self.player.get_grid_position()
                    print(f"You are in: {self.player.current_area.name}")
                    print(f"Grid coordinates: ({grid_x}, {grid_y})")
                    print(f"Area dimensions: {self.player.current_area.grid_width}x{self.player.current_area.grid_length}")
                else:
                    print("You're not in any area.")
            # If arguments, find the coordinates of the specified entity
            else:
                entity_name = " ".join(parts[1:]).lower()
                self.find_entity_coordinates(entity_name)



        elif action in ["teleport", "tp"]:
            if len(parts) > 1:
                # Parse the command to extract area name and/or coordinates
                area = None
                grid_x = None
                grid_y = None
                
                # Check for coordinates in the format "x,y" or "x y"
                coord_parts = []
                area_name_parts = []
                
                for part in parts[1:]:
                    # Check if part is a coordinate pair (x,y)
                    if "," in part:
                        try:
                            x, y = map(int, part.split(","))
                            grid_x, grid_y = x, y
                            continue  # Skip this part in further processing
                        except ValueError:
                            pass  # Not valid coordinates, treat as part of area name
                    
                    # Check if part is a number (potential coordinate)
                    if part.isdigit():
                        coord_parts.append(int(part))
                        continue  # Skip this part in further processing
                    
                    # If we get here, it's part of the area name
                    area_name_parts.append(part)
                
                # Process coordinates if found as separate numbers
                if len(coord_parts) >= 2:
                    grid_x, grid_y = coord_parts[0], coord_parts[1]
                
                # Process area name if found
                if area_name_parts:
                    area_name = " ".join(area_name_parts)
                    area = next((a for a in self.area_manager.areas.values() 
                                if a.name.lower() == area_name.lower()), None)
                    if not area:
                        print(f"Area '{area_name}' not found.")
                        return
                
                # If only coordinates were specified (no area name), use current area
                if area is None and (grid_x is not None or grid_y is not None):
                    area = self.player.current_area
                
                # Teleport the player
                self.player.teleport(area, grid_x, grid_y)
            else:
                print("Usage: teleport [area name] [x,y]")
                print("Examples:")
                print("  teleport Home")
                print("  teleport 3,4")
                print("  teleport Home 3,4")
                print("  teleport Home 3 4")
 


        
        # Areas command to list all areas
        elif action == "areas":
            self.show_all_areas()
        
        # Quit command
        elif action == "quit":
            self.running = False
        
        # Unknown command
        else:
            print(f"Unknown command: {command}")
    
    def show_inventory(self):
        """Show the player's inventory."""
        if not self.player.inventory:
            print("Your inventory is empty.")
            return
        
        print("\nInventory:")
        for i, item in enumerate(self.player.inventory, 1):
            print(f"{i}. {item.name}: {item.description}")
        
        print(f"\nMoney: ${self.player.money}")
        print(f"Energy: {self.player.energy}/{self.player.max_energy}")
        print(f"Hunger: {self.player.hunger}/{self.player.max_hunger}")
        print(f"Street Cred: {self.player.street_cred}")
    
    def show_crafting_menu(self):
        """Show the crafting menu with available recipes."""
        available_recipes = self.crafting_system.list_available_recipes(self.player)
        
        if not available_recipes:
            print("You don't have the ingredients or skills to craft anything right now.")
            return
        
        print("\nAvailable Recipes:")
        for i, recipe in enumerate(available_recipes, 1):
            print(f"{i}. {recipe.name}: {recipe.description}")
            print("   Ingredients:")
            for ingredient, quantity in recipe.ingredients.items():
                print(f"   - {ingredient} x{quantity}")
        
        choice = input("\nEnter recipe number to craft (or 'cancel'): ")
        if choice.lower() == 'cancel':
            return
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(available_recipes):
                recipe = available_recipes[index]
                self.player.craft(recipe.name, self.crafting_system)
            else:
                print("Invalid recipe number.")
        except ValueError:
            print("Please enter a number.")
    
    def show_all_areas(self):
        """Show all areas in the game world."""
        if not self.area_manager.areas:
            print("No areas found in the world.")
            return
            
        print("\nAll Areas in the World:")
        print("======================")
        
        # Group areas by type for better organization
        areas_by_type = {}
        
        for area in self.area_manager.areas.values():
            area_type = area.__class__.__name__
            if area_type not in areas_by_type:
                areas_by_type[area_type] = []
            areas_by_type[area_type].append(area)
        
        # Print areas by type
        for area_type, areas in areas_by_type.items():
            print(f"\n{area_type}s:")
            for area in sorted(areas, key=lambda a: a.name):
                coords = area.coordinates
                print(f"- {area.name}")
                print(f"  ID: {area.id}")
                print(f"  Coordinates: ({coords.x}, {coords.y}, {coords.z})")
                
                # Show connections
                if area.connections:
                    print("  Connections:")
                    for direction, connected_area in area.connections.items():
                        print(f"    {direction} → {connected_area.name}")
                
                # Show special properties for buildings
                if isinstance(area, Building):
                    print(f"  Floors: {len(area.floors)}")
                    if area.floors:
                        print("  Floor Areas:")
                        for floor_num, floor_area in sorted(area.floors.items()):
                            print(f"    Floor {floor_num}: {floor_area.name}")
                
                print()  # Empty line between areas
                
        # Print total count
        total_areas = len(self.area_manager.areas)
        print(f"Total areas: {total_areas}")
        
        # Print teleportation instructions
        print("\nTo teleport to an area, use:")
        print("  teleport <area name>  or  tp <area name>")
        print("You can use partial names like 'mall' or 'cafe'.")



    def find_entity_coordinates(self, entity_name):
        """Find the coordinates of an entity (NPC, item, or object) by name."""
        found_entities = []
        entity_name = entity_name.lower()
        
        # Search for NPCs in areas
        for area in self.area_manager.areas.values():
            for npc in area.npcs:
                if entity_name in npc.name.lower():
                    # Get relative coordinates within the area
                    rel_x, rel_y, rel_z = area.get_relative_coordinates(npc.coordinates)
                    found_entities.append({
                        "type": "NPC",
                        "name": npc.name,
                        "area": area.name,
                        "rel_coords": (rel_x, rel_y, rel_z),
                        "global_coords": (npc.coordinates.x, npc.coordinates.y, npc.coordinates.z),
                        "activity": npc.current_activity
                    })
        
        # Also search for NPCs in the NPC manager (in case they're not in an area yet)
        for npc_id, npc in self.npc_manager.npcs.items():
            if entity_name in npc.name.lower():
                # Check if this NPC is already in our results (from an area)
                if not any(e["type"] == "NPC" and e["name"] == npc.name for e in found_entities):
                    # NPC not in an area, add with unknown location
                    found_entities.append({
                        "type": "NPC",
                        "name": npc.name,
                        "area": "Unknown (not in any area)",
                        "rel_coords": "Unknown",
                        "global_coords": (npc.coordinates.x, npc.coordinates.y, npc.coordinates.z) if hasattr(npc, 'coordinates') else "Unknown",
                        "activity": npc.current_activity
                    })
        
        # Search for items
        for area in self.area_manager.areas.values():
            for item in area.items:
                if entity_name in item.name.lower():
                    # Get relative coordinates within the area
                    rel_x, rel_y, rel_z = area.get_relative_coordinates(item.coordinates)
                    found_entities.append({
                        "type": "Item",
                        "name": item.name,
                        "area": area.name,
                        "rel_coords": (rel_x, rel_y, rel_z),
                        "global_coords": (item.coordinates.x, item.coordinates.y, item.coordinates.z)
                    })
        
        # Search for objects
        for area in self.area_manager.areas.values():
            for obj in area.objects:
                if entity_name in obj.name.lower():
                    # Get relative coordinates within the area
                    rel_x, rel_y, rel_z = area.get_relative_coordinates(obj.coordinates)
                    found_entities.append({
                        "type": "Object",
                        "name": obj.name,
                        "area": area.name,
                        "rel_coords": (rel_x, rel_y, rel_z),
                        "global_coords": (obj.coordinates.x, obj.coordinates.y, obj.coordinates.z)
                    })
        
        # Display results
        if found_entities:
            # If there's an exact match, prioritize it
            exact_matches = [e for e in found_entities if e["name"].lower() == entity_name]
            if exact_matches:
                found_entities = exact_matches
            
            # If we have multiple matches, show all of them
            if len(found_entities) > 1:
                print(f"Found {len(found_entities)} entities matching '{entity_name}':")
                for i, entity in enumerate(found_entities, 1):
                    print(f"{i}. {entity['type']} '{entity['name']}' in {entity['area']}")
                    if entity['rel_coords'] != "Unknown":
                        print(f"   Area coordinates: {entity['rel_coords']}")
                    if entity['type'] == 'NPC':
                        print(f"   Current activity: {entity['activity']}")
            else:
                # Just one match, show detailed info
                entity = found_entities[0]
                print(f"Found {entity['type']} '{entity['name']}' in {entity['area']}")
                if entity['rel_coords'] != "Unknown":
                    print(f"Area coordinates: {entity['rel_coords']}")
                if entity['global_coords'] != "Unknown":
                    print(f"Global coordinates: {entity['global_coords']}")
                if entity['type'] == 'NPC':
                    print(f"Current activity: {entity['activity']}")
        else:
            print(f"Could not find any entity matching '{entity_name}' in the game world.")
    
    def show_help(self):
        """Show help information."""
        print("\nVita Game Help:")
        print("Movement: north, south, east, west, forward, backward, right, left")
        print("Look around: look")
        print("Inventory: inventory")
        print("Pick up item: pickup/take/get/grab [item]")
        print("Drop item: drop [item]")
        print("Use item: use [item]")
        print("Eat item: eat [item]")
        print("Talk to NPC: talk [npc]")
        print("Interact with object: interact [object]")
        print("Jetpack: activate jetpack, deactivate jetpack, fly [direction]")
        print("Teleport: teleport [area] or tp [area]")
        print("Areas: areas (list all areas in the world)")
        print("Crafting: craft, craft [recipe]")
        print("Investments: invest [amount] [business], investments")
        print("Save/Load: save [filename], load [filename]")
        print("Help: help")
        print("Quit: quit")
    
    def run(self):
        """Run the game loop."""
        print("Welcome to Vita Game!")
        print("Type 'help' for a list of commands.")
        
        while self.running:
            command = input("\n> ")
            self.process_command(command)
            
            # Update game time after each command
            self.update_game_time(1)
        
        print("Thanks for playing Vita Game!")