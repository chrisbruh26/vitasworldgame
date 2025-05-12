import json
import random
import time
from .player import Player
from .area import Area, create_area_from_template
from .items import Item, create_item_from_template
from .npc import NPC, create_npc_from_template
from .quest import Quest, create_quest_from_template
from .game_objects import GameObject, create_object_from_template
from .coordinates import Coordinates

class GameEngine:
    """Game engine for managing the game state and processing commands."""
    def __init__(self):
        self.player = Player()
        self.areas = {}
        self.npcs = {}
        self.quests = {}
        self.game_time = 0  # Time in minutes
        self.game_day = 1
        self.weather_conditions = ["clear", "cloudy", "rainy", "stormy", "foggy", "sunny"]
        self.current_weather = "clear"
        self.command_handlers = {
            "go": self.handle_go,
            "look": self.handle_look,
            "pick up": self.handle_pick_up,
            "drop": self.handle_drop,
            "inventory": self.handle_inventory,
            "inv": self.handle_inventory,
            "eat": self.handle_eat,
            "activate jetpack": self.handle_activate_jetpack,
            "deactivate jetpack": self.handle_deactivate_jetpack,
            "fly": self.handle_fly,
            "talk to": self.handle_talk_to,
            "status": self.handle_status,
            "quests": self.handle_quests,
            "accept quest": self.handle_accept_quest,
            "help": self.handle_help,
            "examine": self.handle_examine,
            "use": self.handle_use,
            "buy": self.handle_buy,
            "sell": self.handle_sell,
            "steal": self.handle_steal,
            "money": self.handle_money,
            "time": self.handle_time,
            "weather": self.handle_weather,
            "wait": self.handle_wait,
            "save": self.handle_save,
            "load": self.handle_load
        }
    
    def setup_game(self):
        """Set up the initial game state."""
        # Create areas
        park = create_area_from_template("park")
        house = create_area_from_template("house")
        street = create_area_from_template("street")
        mall = create_area_from_template("mall")
        airport = create_area_from_template("airport")
        farm = create_area_from_template("farm")
        casino = create_area_from_template("casino")
        
        # Add areas to the game
        self.areas = {
            "park": park,
            "house": house,
            "street": street,
            "mall": mall,
            "airport": airport,
            "farm": farm,
            "casino": casino
        }
        
        # Set up connections
        park.add_connection("north", house)
        park.add_connection("east", street)
        street.add_connection("north", mall)
        street.add_connection("east", airport)
        park.add_connection("south", farm)
        street.add_connection("northeast", casino)
        
        # Add items to areas
        park.add_item(create_item_from_template("carrot"))
        park.add_item(create_item_from_template("jetpack"))
        street.add_item(create_item_from_template("acorn"))
        farm.add_item(create_item_from_template("carrot"))
        farm.add_item(create_item_from_template("carrot"))
        casino.add_item(create_item_from_template("dollar", amount=100))
        
        # Add NPCs
        squirrel = create_npc_from_template("squirrel", name="Jeff")
        park.add_npc(squirrel)
        
        farmer = create_npc_from_template("farmer")
        farm.add_npc(farmer)
        
        dealer = create_npc_from_template("casino_dealer")
        casino.add_npc(dealer)
        
        pilot = create_npc_from_template("pilot")
        airport.add_npc(pilot)
        
        # Add multiple similar NPCs
        for i in range(1, 4):
            squirrel_clone = create_npc_from_template("squirrel", name_suffix=f"#{i}")
            park.add_npc(squirrel_clone)
        
        # Add quests
        acorn_quest = create_quest_from_template("acorn_collection")
        squirrel.quests.append(acorn_quest)
        acorn_quest.giver = squirrel
        
        # Add game objects
        elevator = create_object_from_template("elevator")
        mall.add_object(elevator)
        
        car = create_object_from_template("car")
        street.add_object(car)
        
        helicopter = create_object_from_template("helicopter")
        airport.add_object(helicopter)
        
        # Set player's starting area
        self.player.set_current_area(park)
        
        # Set initial game time (8:00 AM)
        self.game_time = 8 * 60
    
    def process_command(self, command):
        """Process a player command."""
        command = command.lower().strip()
        
        if command == "quit":
            return False
        
        # Check for exact command matches first
        if command in self.command_handlers:
            self.command_handlers[command]("")
            return True
        
        # Check for commands with parameters
        for cmd_prefix, handler in self.command_handlers.items():
            if command.startswith(cmd_prefix + " "):
                param = command[len(cmd_prefix) + 1:]
                handler(param)
                return True
        
        print("Command not recognized. Type 'help' for a list of commands.")
        return True
    
    def handle_go(self, direction):
        """Handle the 'go' command."""
        self.player.move(direction)
        self.advance_time(1)  # Moving takes 1 minute
    
    def handle_look(self, param):
        """Handle the 'look' command."""
        self.player.look_around()
    
    def handle_pick_up(self, item_name):
        """Handle the 'pick up' command."""
        item = next((i for i in self.player.current_area.items if i.name.lower() == item_name.lower()), None)
        if item:
            if hasattr(item, 'pickupable') and not item.pickupable:
                print(f"You can't pick up the {item.name}.")
                return
                
            self.player.add_item(item)
            self.player.current_area.remove_item(item_name)
            self.advance_time(1)  # Picking up takes 1 minute
        else:
            print(f"There is no {item_name} here.")
    
    def handle_drop(self, item_name):
        """Handle the 'drop' command."""
        self.player.remove_item(item_name)
        self.advance_time(1)  # Dropping takes 1 minute
    
    def handle_inventory(self, param):
        """Handle the 'inventory' command."""
        if self.player.inventory:
            print("Your inventory:")
            for item in self.player.inventory:
                print(f"- {item}")
        else:
            print("Your inventory is empty.")
    
    def handle_eat(self, item_name):
        """Handle the 'eat' command."""
        self.player.eat(item_name)
        self.advance_time(5)  # Eating takes 5 minutes
    
    def handle_activate_jetpack(self, param):
        """Handle the 'activate jetpack' command."""
        self.player.activate_jetpack()
    
    def handle_deactivate_jetpack(self, param):
        """Handle the 'deactivate jetpack' command."""
        self.player.deactivate_jetpack()
    
    def handle_fly(self, direction):
        """Handle the 'fly' command."""
        self.player.fly(direction)
        self.advance_time(1)  # Flying takes 1 minute
    
    def handle_talk_to(self, npc_name):
        """Handle the 'talk to' command."""
        npc = next((n for n in self.player.current_area.npcs if n.name.lower() == npc_name.lower()), None)
        if npc:
            npc.talk(self.player)
            self.advance_time(5)  # Talking takes 5 minutes
        else:
            print(f"There is no {npc_name} here to talk to.")
    
    def handle_status(self, param):
        """Handle the 'status' command."""
        print(f"Name: {self.player.name}")
        print(f"Street Cred: {self.player.street_cred}")
        print(f"Position: {self.player.coordinates}")
        print(f"Energy: {self.player.energy}/{self.player.max_energy}")
        print(f"Hunger: {self.player.hunger}/{self.player.max_hunger}")
        print(f"Money: ${self.player.money}")
        if self.player.is_flying:
            print("Status: Flying with jetpack")
        else:
            print("Status: On the ground")
    
    def handle_quests(self, param):
        """Handle the 'quests' command."""
        self.player.check_quests()
    
    def handle_accept_quest(self, quest_index):
        """Handle the 'accept quest' command."""
        try:
            index = int(quest_index) - 1
            # Find NPCs in the current area with available quests
            npcs_with_quests = []
            for npc in self.player.current_area.npcs:
                available_quests = [q for q in npc.quests if not hasattr(q, 'active') or (not q.active and not q.completed)]
                if available_quests:
                    npcs_with_quests.append((npc, available_quests))
            
            if not npcs_with_quests:
                print("There are no quests available in this area.")
                return
                
            # For simplicity, just use the first NPC with quests
            npc, quests = npcs_with_quests[0]
            if 0 <= index < len(quests):
                npc.give_quest(self.player, index)
                self.advance_time(2)  # Accepting a quest takes 2 minutes
            else:
                print(f"Invalid quest number. Available quests: 1-{len(quests)}")
        except ValueError:
            print("Please enter a valid quest number.")
    
    def handle_help(self, param):
        """Handle the 'help' command."""
        print("Available commands:")
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
        print("- 'status' to check your status")
        print("- 'quests' to check your active quests")
        print("- 'accept quest [number]' to accept a quest")
        print("- 'examine [object]' to examine something closely")
        print("- 'use [object]' to use an object")
        print("- 'buy [item]' to buy an item")
        print("- 'sell [item]' to sell an item")
        print("- 'steal [item]' to steal an item")
        print("- 'money' to check your money")
        print("- 'time' to check the current time")
        print("- 'weather' to check the weather")
        print("- 'wait [minutes]' to wait for a specified time")
        print("- 'save [slot]' to save your game")
        print("- 'load [slot]' to load a saved game")
        print("- 'quit' to exit the game")
    
    def handle_examine(self, object_name):
        """Handle the 'examine' command."""
        # Check inventory
        item = next((i for i in self.player.inventory if i.name.lower() == object_name.lower()), None)
        if item:
            print(f"You examine the {item.name}.")
            print(f"Description: {item.description}")
            if hasattr(item, 'edible') and item.edible:
                print(f"This is edible and provides {item.nutrition} nutrition.")
            if hasattr(item, 'value') and item.value > 0:
                print(f"Value: ${item.value}")
            return
        
        # Check area items
        item = next((i for i in self.player.current_area.items if i.name.lower() == object_name.lower()), None)
        if item:
            print(f"You examine the {item.name}.")
            print(f"Description: {item.description}")
            return
        
        # Check area NPCs
        npc = next((n for n in self.player.current_area.npcs if n.name.lower() == object_name.lower()), None)
        if npc:
            print(f"You examine {npc.name}.")
            print(f"Description: {npc.description}")
            return
        
        # Check area objects
        obj = next((o for o in self.player.current_area.objects if o.name.lower() == object_name.lower()), None)
        if obj:
            print(f"You examine the {obj.name}.")
            print(f"Description: {obj.description}")
            return
        
        print(f"You don't see a {object_name} here.")
    
    def handle_use(self, object_name):
        """Handle the 'use' command."""
        # Check inventory
        item = next((i for i in self.player.inventory if i.name.lower() == object_name.lower()), None)
        if item:
            item.use(self.player)
            self.advance_time(2)  # Using an item takes 2 minutes
            return
        
        # Check area objects
        obj = next((o for o in self.player.current_area.objects if o.name.lower() == object_name.lower()), None)
        if obj:
            obj.interact(self.player)
            self.advance_time(2)  # Interacting with an object takes 2 minutes
            return
        
        print(f"You don't have or see a {object_name} to use.")
    
    def handle_buy(self, item_name):
        """Handle the 'buy' command."""
        # Check if there's a shopkeeper NPC in the area
        shopkeeper = next((n for n in self.player.current_area.npcs if "shopkeeper" in n.name.lower()), None)
        if not shopkeeper:
            print("There's no one here to buy from.")
            return
        
        # Check if the shopkeeper has the item
        item = next((i for i in shopkeeper.inventory if i.name.lower() == item_name.lower()), None)
        if not item:
            print(f"{shopkeeper.name} doesn't have a {item_name} for sale.")
            return
        
        # Check if player has enough money
        if not hasattr(item, 'value') or item.value <= 0:
            print(f"The {item.name} is not for sale.")
            return
        
        if self.player.money < item.value:
            print(f"You don't have enough money. The {item.name} costs ${item.value} but you only have ${self.player.money}.")
            return
        
        # Buy the item
        self.player.remove_money(item.value)
        shopkeeper.remove_from_inventory(item_name)
        self.player.add_item(item)
        print(f"You bought the {item.name} for ${item.value}.")
        self.advance_time(5)  # Shopping takes 5 minutes
    
    def handle_sell(self, item_name):
        """Handle the 'sell' command."""
        # Check if there's a shopkeeper NPC in the area
        shopkeeper = next((n for n in self.player.current_area.npcs if "shopkeeper" in n.name.lower()), None)
        if not shopkeeper:
            print("There's no one here to sell to.")
            return
        
        # Check if the player has the item
        item = next((i for i in self.player.inventory if i.name.lower() == item_name.lower()), None)
        if not item:
            print(f"You don't have a {item_name} to sell.")
            return
        
        # Calculate sell price (usually less than buy price)
        if not hasattr(item, 'value') or item.value <= 0:
            print(f"The {item.name} has no value.")
            return
        
        sell_price = int(item.value * 0.7)  # 70% of buy price
        
        # Sell the item
        self.player.remove_item(item_name)
        shopkeeper.add_to_inventory(item)
        self.player.add_money(sell_price)
        print(f"You sold the {item.name} for ${sell_price}.")
        self.advance_time(5)  # Shopping takes 5 minutes
    
    def handle_steal(self, item_name):
        """Handle the 'steal' command."""
        # Check if there's an NPC with the item
        for npc in self.player.current_area.npcs:
            item = next((i for i in npc.inventory if i.name.lower() == item_name.lower()), None)
            if item:
                # Attempt to steal based on player's stealth skill
                stealth_skill = self.player.get_skill("stealth")
                detection_chance = 80 - (stealth_skill * 5)  # Higher stealth reduces detection chance
                
                if random.randint(1, 100) <= detection_chance:
                    # Caught stealing
                    print(f"{npc.name} caught you trying to steal the {item.name}!")
                    self.player.street_cred -= 10
                    npc.adjust_relationship(self.player, -20)
                    print("Your street cred decreased by 10.")
                else:
                    # Successful theft
                    npc.remove_from_inventory(item_name)
                    self.player.add_item(item)
                    print(f"You successfully stole the {item.name} from {npc.name}!")
                    self.player.improve_skill("stealth", 1)
                
                self.advance_time(5)  # Stealing takes 5 minutes
                return
        
        # Check if there's an item in the area that belongs to someone (not just lying around)
        area_items = [i for i in self.player.current_area.items if i.name.lower() == item_name.lower()]
        if area_items:
            item = area_items[0]
            if self.player.current_area.name in ["Shop", "Store", "Mall"]:
                # Attempt to steal from a store
                stealth_skill = self.player.get_skill("stealth")
                detection_chance = 70 - (stealth_skill * 5)
                
                if random.randint(1, 100) <= detection_chance:
                    # Caught stealing
                    print(f"A security guard caught you trying to steal the {item.name}!")
                    self.player.street_cred -= 15
                    print("Your street cred decreased by 15.")
                else:
                    # Successful theft
                    self.player.current_area.remove_item(item_name)
                    self.player.add_item(item)
                    print(f"You successfully stole the {item.name}!")
                    self.player.improve_skill("stealth", 1)
                
                self.advance_time(5)  # Stealing takes 5 minutes
                return
            else:
                # Just picking up an item that's lying around
                print(f"The {item.name} isn't owned by anyone. You can just pick it up.")
                return
        
        print(f"You don't see a {item_name} that you can steal.")
    
    def handle_money(self, param):
        """Handle the 'money' command."""
        print(f"You have ${self.player.money}.")
    
    def handle_time(self, param):
        """Handle the 'time' command."""
        hours = self.game_time // 60
        minutes = self.game_time % 60
        am_pm = "AM" if hours < 12 else "PM"
        display_hours = hours % 12
        if display_hours == 0:
            display_hours = 12
        print(f"The time is {display_hours}:{minutes:02d} {am_pm} on day {self.game_day}.")
    
    def handle_weather(self, param):
        """Handle the 'weather' command."""
        print(f"The current weather is {self.current_weather}.")
        print(f"In {self.player.current_area.name}, it's {self.player.current_area.weather}.")
    
    def handle_wait(self, minutes_str):
        """Handle the 'wait' command."""
        try:
            minutes = int(minutes_str)
            if minutes <= 0:
                print("Please enter a positive number of minutes to wait.")
                return
                
            if minutes > 60:
                print("You can only wait up to 60 minutes at a time.")
                minutes = 60
                
            print(f"You wait for {minutes} minutes...")
            self.advance_time(minutes)
        except ValueError:
            print("Please enter a valid number of minutes to wait.")
    
    def handle_save(self, slot):
        """Handle the 'save' command."""
        if not slot:
            slot = "1"
            
        try:
            # Create a dictionary with all game state
            game_state = {
                "player": self.player.to_dict(),
                "game_time": self.game_time,
                "game_day": self.game_day,
                "current_weather": self.current_weather,
                "current_area": self.player.current_area.name
            }
            
            # Save to file
            with open(f"save_slot_{slot}.json", "w") as f:
                json.dump(game_state, f, indent=2)
                
            print(f"Game saved to slot {slot}.")
        except Exception as e:
            print(f"Error saving game: {e}")
    
    def handle_load(self, slot):
        """Handle the 'load' command."""
        if not slot:
            slot = "1"
            
        try:
            # Load from file
            with open(f"save_slot_{slot}.json", "r") as f:
                game_state = json.load(f)
                
            # Restore player state
            # In a real implementation, you'd need to reconstruct all objects
            # For now, we'll just restore basic player attributes
            self.player.name = game_state["player"]["name"]
            self.player.street_cred = game_state["player"]["street_cred"]
            self.player.energy = game_state["player"]["energy"]
            self.player.max_energy = game_state["player"]["max_energy"]
            self.player.hunger = game_state["player"]["hunger"]
            self.player.max_hunger = game_state["player"]["max_hunger"]
            self.player.money = game_state["player"]["money"]
            self.player.skills = game_state["player"]["skills"]
            self.player.relationships = game_state["player"]["relationships"]
            self.player.properties = game_state["player"]["properties"]
            self.player.is_flying = game_state["player"]["is_flying"]
            
            # Restore game state
            self.game_time = game_state["game_time"]
            self.game_day = game_state["game_day"]
            self.current_weather = game_state["current_weather"]
            
            # Set current area
            area_name = game_state["current_area"]
            if area_name in self.areas:
                self.player.set_current_area(self.areas[area_name])
                
            print(f"Game loaded from slot {slot}.")
        except FileNotFoundError:
            print(f"No saved game found in slot {slot}.")
        except Exception as e:
            print(f"Error loading game: {e}")
    
    def advance_time(self, minutes):
        """Advance the game time by a specified number of minutes."""
        self.game_time += minutes
        
        # Handle day change
        if self.game_time >= 24 * 60:
            self.game_time %= (24 * 60)
            self.game_day += 1
            print(f"A new day dawns. It is now day {self.game_day}.")
        
        # Update weather occasionally
        if random.randint(1, 100) <= 5:  # 5% chance per time advancement
            self.update_weather()
        
        # Update NPCs based on time
        self.update_npcs()
        
        # Update player status
        self.update_player_status()
    
    def update_weather(self):
        """Update the weather conditions."""
        old_weather = self.current_weather
        self.current_weather = random.choice(self.weather_conditions)
        if old_weather != self.current_weather:
            print(f"The weather changes from {old_weather} to {self.current_weather}.")
    
    def update_npcs(self):
        """Update NPCs based on time of day."""
        current_hour = self.game_time // 60
        
        for npc_name, npc in self.npcs.items():
            if hasattr(npc, 'update_activity'):
                npc.update_activity(current_hour)
    
    def update_player_status(self):
        """Update player status based on time passage."""
        # Increase hunger over time
        self.player.hunger = min(self.player.max_hunger, self.player.hunger + 1)
        
        # Decrease energy if flying
        if self.player.is_flying and self.player.jetpack:
            self.player.energy = max(0, self.player.energy - 2)
            
            # If energy is too low, force deactivation of jetpack
            if self.player.energy <= 10:
                print("You're getting too tired to keep flying!")
                self.player.deactivate_jetpack()
        
        # Hunger effects
        if self.player.hunger >= 80:
            print("You're getting very hungry. You should eat something soon.")
            self.player.energy = max(0, self.player.energy - 1)
        
        # Energy recovery when not flying
        if not self.player.is_flying and self.player.energy < self.player.max_energy:
            self.player.energy = min(self.player.max_energy, self.player.energy + 1)
    
    def run(self):
        """Run the game loop."""
        self.setup_game()
        
        print("Welcome to the Vita Game!")
        print("You are Vita, a mischievous bunny with a jetpack and a taste for adventure.")
        print("Explore the world, cause some chaos, and have fun!")
        print("Type 'help' for a list of commands.")
        
        running = True
        while running:
            command = input("\n> ").lower()
            running = self.process_command(command)