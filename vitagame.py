# version 1 of the vita game, which will eventually be turned into a web-based game
# This is a text-based open-world game inspired by Goat Simulator but with a bunny protagonist

class Coordinates:
    """Represents a position in the 3D game world."""
    def __init__(self, x=0, y=0, z=0):
        self.x = x  # East-West position
        self.y = y  # North-South position
        self.z = z  # Height/Elevation
    
    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"
    
    def distance_to(self, other_coords):
        """Calculate horizontal distance to another coordinate."""
        return ((self.x - other_coords.x) ** 2 + (self.y - other_coords.y) ** 2) ** 0.5
    
    def height_difference(self, other_coords):
        """Calculate vertical distance to another coordinate."""
        return abs(self.z - other_coords.z)


class Item:
    """Item class representing items in the game world."""
    def __init__(self, name, description, coordinates=None, edible=False, nutrition=0):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.edible = edible
        self.nutrition = nutrition

    def __str__(self):
        return self.name
    
    def use(self, player):
        """Use the item."""
        print(f"You use the {self.name}.")


class Food(Item):
    """Food item that can be eaten."""
    def __init__(self, name, description, nutrition=10, effect=None):
        super().__init__(name, description, edible=True, nutrition=nutrition)
        self.effect_function = effect
    
    def effect(self, player):
        """Apply special effect when eaten."""
        if self.effect_function:
            self.effect_function(player)


class Jetpack(Item):
    """JetPack class representing the jetpack object."""
    def __init__(self):
        super().__init__("Jetpack", "A high-tech jetpack that allows you to fly.")
        self.fuel = 100
        self.max_fuel = 100
    
    def activate(self, player):
        """Activate the jetpack for the player."""
        if self.fuel > 0:
            player.is_flying = True
            return True
        return False
    
    def refuel(self, amount=100):
        """Refuel the jetpack."""
        self.fuel = min(self.max_fuel, self.fuel + amount)
        print(f"Jetpack refueled to {self.fuel}%")
    
    def __str__(self):
        return f"{self.name} (Fuel: {self.fuel}%)"


class Player:
    """Player class for the Vita game."""
    def __init__(self):
        self.name = "Vita"
        self.street_cred = 0
        self.inventory = []
        self.current_area = None
        self.coordinates = Coordinates(0, 0, 0)
        self.jetpack = None
        self.is_flying = False
        self.energy = 100
        self.max_energy = 100
        self.hunger = 0
        
    def set_current_area(self, area):
        """Set the current area for the player."""
        self.current_area = area
        # Update player coordinates to match area entrance coordinates
        self.coordinates = Coordinates(area.coordinates.x, area.coordinates.y, area.coordinates.z)
        print(f"You are now in {area.name}. {area.description}")
        self.look_around()
    
    def look_around(self):
        """Look around the current area."""
        # Display available directions
        if self.current_area.connections:
            print("You can go:")
            for direction, area in self.current_area.connections.items():
                print(f"- {direction} to {area.name}")
        
        # Display items in the area
        if self.current_area.items:
            print("You see:")
            for item in self.current_area.items:
                print(f"- {item.name}: {item.description}")
        
        # Display NPCs in the area
        if self.current_area.npcs:
            print("People around:")
            for npc in self.current_area.npcs:
                print(f"- {npc.name}: {npc.description}")
        
        # Display objects in the area
        if self.current_area.objects:
            print("Objects around:")
            for obj in self.current_area.objects:
                print(f"- {obj.name}: {obj.description}")

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
            return
        
        if self.jetpack.fuel <= 0:
            print("Your jetpack runs out of fuel!")
            self.is_flying = False
            return
        
        # Consume fuel
        self.jetpack.fuel -= distance
        if self.jetpack.fuel < 0:
            self.jetpack.fuel = 0
        
        # Move in the specified direction
        if direction == "up":
            self.coordinates.z += distance
            print(f"You fly upward to elevation {self.coordinates.z}.")
        elif direction == "down":
            if self.coordinates.z - distance < self.current_area.coordinates.z:
                # Don't go below ground level
                self.coordinates.z = self.current_area.coordinates.z
                print("You descend to ground level.")
            else:
                self.coordinates.z -= distance
                print(f"You fly downward to elevation {self.coordinates.z}.")
        else:
            print(f"You fly {direction}.")
            # Horizontal movement would be handled here
    
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


class Area:
    """Area class representing different locations in the game world."""
    def __init__(self, name, description, coordinates=None, height=1):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.height = height  # How tall this area is (for buildings)
        self.connections = {}
        self.items = []
        self.npcs = []
        self.objects = []

    def add_connection(self, direction, area):
        """Add a connection to another area."""
        self.connections[direction] = area
        # Add reverse connection if it doesn't exist
        reverse_directions = {
            "north": "south", "south": "north", 
            "east": "west", "west": "east",
            "up": "down", "down": "up"
        }
        if direction in reverse_directions and reverse_directions[direction] not in area.connections:
            area.connections[reverse_directions[direction]] = self

    def add_item(self, item):
        """Add an item to the area."""
        self.items.append(item)

    def remove_item(self, item_name):
        """Remove an item from the area."""
        item = next((i for i in self.items if i.name.lower() == item_name.lower()), None)
        if item:
            self.items.remove(item)
            return item
        return None
    
    def add_npc(self, npc):
        """Add an NPC to the area."""
        self.npcs.append(npc)
        npc.location = self
    
    def remove_npc(self, npc):
        """Remove an NPC from the area."""
        if npc in self.npcs:
            self.npcs.remove(npc)
            npc.location = None
    
    def add_object(self, obj):
        """Add an object to the area."""
        self.objects.append(obj)
    
    def remove_object(self, obj_name):
        """Remove an object from the area."""
        obj = next((o for o in self.objects if o.name.lower() == obj_name.lower()), None)
        if obj:
            self.objects.remove(obj)
            return obj
        return None
    
    def __str__(self):
        return f"{self.name} at {self.coordinates}"


class GameObject:
    """Base class for all game objects that can be interacted with."""
    def __init__(self, name, description, coordinates=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
    
    def interact(self, player):
        """Base interaction method."""
        print(f"You interact with the {self.name}.")

class Transport(GameObject):
    """Base class for objects that provide transportation for the player."""
    # need to make an elevator as an instance of this, or its own class
    # this class can include cars, which will be controllable by the player, whereas an elevator will be automatic
    def __init__(self, name, description, coordinates=None):
        super().__init__(name, description, coordinates)
        self.destination = None  # Where this transport leads to
    def set_destination(self, area):
        """Set the destination for this transport."""
        self.destination = area
        print(f"{self.name} will take you to {area.name}.")
    def use(self, player):
        """Use the transport to travel to its destination."""
        if self.destination:
            player.set_current_area(self.destination)
            print(f"You travel to {self.destination.name}.")
        else:
            print(f"{self.name} has no destination set.")


class NPC:
    """NPC class representing non-player characters in the game world."""
    def __init__(self, name, description, coordinates=None, dialogue=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.location = None
        self.dialogue = dialogue if dialogue else {"default": "Hello there!"}
        self.quest = None

    def set_location(self, area):
        """Set the location of the NPC."""
        if self.location:
            self.location.remove_npc(self)
        self.location = area
        area.add_npc(self)
        # Update NPC coordinates to match area
        self.coordinates = Coordinates(area.coordinates.x, area.coordinates.y, area.coordinates.z)

    def remove_location(self):
        """Remove the NPC from its current location."""
        if self.location:
            self.location.remove_npc(self)
            self.location = None
    
    def talk(self, player):
        """Talk to the NPC."""
        if self.quest and self.quest.is_active and not self.quest.is_completed:
            print(f"{self.name}: {self.quest.get_status()}")
        else:
            print(f"{self.name}: {self.dialogue.get('default')}")
    
    def assign_quest(self, quest):
        """Assign a quest to this NPC."""
        self.quest = quest
        quest.giver = self


class Quest:
    """Quest class for side missions."""
    def __init__(self, name, description, objective, reward=None):
        self.name = name
        self.description = description
        self.objective = objective  # Function that checks if quest is completed
        self.reward = reward
        self.is_active = False
        self.is_completed = False
        self.giver = None
    
    def start(self, player):
        """Start the quest."""
        self.is_active = True
        print(f"Quest started: {self.name}")
        print(self.description)
    
    def check_completion(self, player):
        """Check if the quest is completed."""
        if self.objective(player):
            self.complete(player)
            return True
        return False
    
    def complete(self, player):
        """Complete the quest and give rewards."""
        self.is_completed = True
        print(f"Quest completed: {self.name}")
        if self.reward:
            self.reward(player)
    
    def get_status(self):
        """Get the current status of the quest."""
        if self.is_completed:
            return f"You've already completed my quest. Thank you!"
        elif self.is_active:
            return f"Have you completed my quest yet? {self.description}"
        else:
            return f"I have a quest for you: {self.description} Will you accept it?"


# set up items and add them to areas
def create_areas(): 
    """Create areas and set up their connections."""
    # Create areas with coordinates
    park = Area("Park", "A beautiful park with trees, some low hills, and a fountain.", Coordinates(0, 0, 0))
    house = Area("House", "A cozy little house with a small garden.", Coordinates(0, 10, 0), height=2)
    street = Area("Street", "A busy street with shops and cafes.", Coordinates(10, 0, 0))
    alley = Area("Alley", "A dark alley with a shady vibe.", Coordinates(15, 5, 0))
    rooftop = Area("Rooftop", "A high rooftop with a great view of the city.", Coordinates(0, 10, 2))
    
    # Tall building
    skyscraper_lobby = Area("Skyscraper Lobby", "The grand entrance to a massive skyscraper.", Coordinates(20, 20, 0), height=50)
    skyscraper_mid = Area("Skyscraper Mid-Level", "The middle floor of the skyscraper with offices.", Coordinates(20, 20, 25))
    skyscraper_top = Area("Skyscraper Top", "The top floor with an observation deck.", Coordinates(20, 20, 50))

    # Set up connections
    park.add_connection("north", house)
    park.add_connection("east", street)
    street.add_connection("north", alley)
    house.add_connection("up", rooftop)  # Can go up to the rooftop from the house
    
    # Skyscraper connections
    street.add_connection("northeast", skyscraper_lobby)
    skyscraper_lobby.add_connection("southwest", street)
    skyscraper_lobby.add_connection("up", skyscraper_mid)
    skyscraper_mid.add_connection("up", skyscraper_top)

    # Add items to areas
    park.add_item(Item("Bench", "A wooden bench to sit on."))
    acorn = Item("Acorn", "A small acorn, perfect for planting.", edible=True, nutrition=5)
    park.add_item(acorn)
    
    house.add_item(Item("Key", "A small key that might open something."))
    street.add_item(Item("Map", "A map of the city showing all major landmarks."))
    
    # Add food items
    park.add_item(Food("Carrot", "A fresh orange carrot. Bunnies love these!", 15))
    street.add_item(Food("Ice Cream", "A delicious ice cream cone. Might give you a sugar rush!", 10, 
                         lambda player: setattr(player, 'energy', min(player.max_energy, player.energy + 20))))
    
    # Add jetpack to the game
    rooftop.add_item(Jetpack())
    
    # Add some acorns for the side quest
    alley.add_item(Item("Acorn", "A small acorn, perfect for planting.", edible=True, nutrition=5))
    rooftop.add_item(Item("Acorn", "A small acorn, perfect for planting.", edible=True, nutrition=5))
    skyscraper_top.add_item(Item("Golden Acorn", "A rare golden acorn! It looks valuable.", edible=True, nutrition=20))

    return park, house, street, alley, rooftop, skyscraper_lobby, skyscraper_mid, skyscraper_top


def main():
    # Create the game world
    areas = create_areas()
    park, house, street, alley, rooftop, skyscraper_lobby, skyscraper_mid, skyscraper_top = areas
    
    # Create player
    player = Player()
    
    # Create NPCs
    squirrel = NPC("Jeff", "A bushy-tailed squirrel with a worried expression.", 
                  dialogue={"default": "I've lost my acorns! Can you help me find 10 acorns?",
                           "quest_active": "Have you found my acorns yet?",
                           "quest_complete": "Thank you for finding my acorns! Now I can survive the winter."})
    
    # need templates for NPCs using json so that I can create several similar NPCs, like multiple squirrels

    park.add_npc(squirrel)
    
    # Create the acorn collection quest
    def acorn_quest_objective(player):
        """Check if player has 10 acorns."""
        acorn_count = sum(1 for item in player.inventory if item.name.lower() == "acorn")
        golden_acorn_count = sum(1 for item in player.inventory if item.name.lower() == "golden acorn")
        return acorn_count + (golden_acorn_count * 2) >= 10
    
    def acorn_quest_reward(player):
        """Reward for completing the acorn quest."""
        # Remove acorns from inventory
        acorns_to_remove = []
        count = 0
        for item in player.inventory:
            if item.name.lower() == "acorn" and count < 10:
                acorns_to_remove.append(item)
                count += 1
            elif item.name.lower() == "golden acorn" and count < 10:
                acorns_to_remove.append(item)
                count += 2  # Golden acorns count as 2
        
        for acorn in acorns_to_remove:
            player.inventory.remove(acorn)
        
        # Give reward
        player.street_cred += 20
        print("Your street cred increased by 20 points!")
        print("Jeff (the squirrel) is very grateful and spreads the word about your helpfulness.")
        
        # Add a special item as reward
        jetpack_upgrade = Item("Jetpack Fuel Upgrade", "A special upgrade that increases jetpack efficiency.")
        player.add_item(jetpack_upgrade)
        if player.jetpack:
            player.jetpack.max_fuel = 150
            player.jetpack.fuel = 150
            print("Your jetpack has been upgraded with a larger fuel tank!")
    
    acorn_quest = Quest("Acorn Collector", 
                       "Find 10 acorns for the squirrels. Golden acorns count as 2!", 
                       acorn_quest_objective, 
                       acorn_quest_reward)
    squirrel.assign_quest(acorn_quest)
    
    # Set player's starting area
    player.set_current_area(park)
    
    print("Welcome to the Vita Game!")
    print("You are Vita, a mischievous bunny with a jetpack and a taste for adventure.")
    print("Explore the world, cause some chaos, and have fun!")
    print("\nCommands:")
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
    print("- 'quit' to exit the game")
    
    # Main game loop
    while True:
        action = input("\n> ").lower()
        
        if action == "quit":
            print("Thanks for playing!")
            break
            
        elif action == "look":
            player.look_around()
            
        elif action.startswith("pick up "):
            item_name = action[8:]  # Remove "pick up " from the beginning
            item = next((i for i in player.current_area.items if i.name.lower() == item_name.lower()), None)
            if item:
                player.add_item(item)
                player.current_area.remove_item(item_name)
            else:
                print(f"There is no {item_name} here.")
                
        elif action.startswith("drop "):
            item_name = action[5:]  # Remove "drop " from the beginning
            player.remove_item(item_name)
            
        elif action.startswith("go "):
            direction = action[3:]  # Remove "go " from the beginning
            if direction in player.current_area.connections:
                # Check if player needs to fly to reach this area
                target_area = player.current_area.connections[direction]
                height_diff = target_area.coordinates.z - player.current_area.coordinates.z
                
                if height_diff > 0 and not player.is_flying:
                    print(f"You need to fly to reach {target_area.name}. Try activating your jetpack first!")
                else:
                    new_area = player.current_area.connections[direction]
                    player.set_current_area(new_area)
            else:
                print(f"You can't go {direction} from here.")
                
        elif action in ["inventory", "inv"]:
            if player.inventory:
                print("Your inventory:")
                for item in player.inventory:
                    print(f"- {item}")
            else:
                print("Your inventory is empty.")
                
        elif action.startswith("eat "):
            item_name = action[4:]  # Remove "eat " from the beginning
            player.eat(item_name)
            
        elif action == "activate jetpack":
            player.activate_jetpack()
            
        elif action == "deactivate jetpack":
            player.deactivate_jetpack()
            
        elif action.startswith("fly "):
            direction = action[4:]  # Remove "fly " from the beginning
            player.fly(direction)
            
        elif action.startswith("talk to "):
            npc_name = action[8:]  # Remove "talk to " from the beginning
            npc = next((n for n in player.current_area.npcs if n.name.lower() == npc_name.lower()), None)
            if npc:
                npc.talk(player)
                if npc.quest and not npc.quest.is_active and not npc.quest.is_completed:
                    accept = input("Accept quest? (yes/no): ").lower()
                    if accept == "yes":
                        npc.quest.start(player)
                elif npc.quest and npc.quest.is_active and not npc.quest.is_completed:
                    if npc.quest.check_completion(player):
                        npc.talk(player)  # Talk again to get completion dialogue
            else:
                print(f"There is no {npc_name} here to talk to.")
                
        elif action == "status":
            print(f"Name: {player.name}")
            print(f"Street Cred: {player.street_cred}")
            print(f"Position: {player.coordinates}")
            print(f"Energy: {player.energy}/{player.max_energy}")
            print(f"Hunger: {player.hunger}")
            if player.is_flying:
                print("Status: Flying with jetpack")
            else:
                print("Status: On the ground")
                
        else:
            print("Command not recognized. Try again.")


# The game will be very open-world but one side mission that the player can do is find 10 acorns and bring them to a tree in the park

if __name__ == "__main__":
    main()