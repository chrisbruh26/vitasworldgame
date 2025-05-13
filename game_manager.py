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
        
        # Create items
        self.create_starting_items()
        
        # Create NPCs
        self.create_starting_npcs()
        
        # Create objects
        self.create_starting_objects()
        
        # Create crafting recipes
        self.create_starting_recipes()
    
    def create_starting_areas(self):
        """Create the starting areas for the game."""
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
        
        # Create a shopkeeper NPC
        shopkeeper = NPC(
            "Shopkeeper",
            "A friendly shopkeeper selling various goods.",
            dialogue={
                "default": "Welcome to my shop! Feel free to browse around.",
                "friendly": "Ah, my favorite customer! What can I get for you today?"
            },
            personality={
                "friendliness": 60,
                "greed": 40
            },
            money=500
        )
        self.npc_manager.add_npc(shopkeeper)
        
        # Place NPCs in areas
        park = self.area_manager.get_area("park")
        if park:
            park.place_object_at(squirrel, 7, 7)
        
        street = self.area_manager.get_area("street")
        if street:
            street.place_object_at(shopkeeper, 5, 2)
    
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
        
        # Update NPCs based on time
        self.npc_manager.update_all_npcs(self.game_time)
        
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