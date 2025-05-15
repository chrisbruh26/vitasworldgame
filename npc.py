"""
NPC module for Vita Game.
Handles all non-player characters in the game world.
"""

import json
import random
from .coordinates import Coordinates

class NPC:
    """NPC class representing non-player characters in the game world."""
    def __init__(self, name, description, coordinates=None, dialogue=None, personality=None, 
                 money=0, relationships=None, properties=None, inventory=None, schedule=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.location = None
        self.dialogue = dialogue if dialogue else {"default": "Hello there!"}
        self.inventory = inventory or []  # NPC's inventory
        self.personality = personality or {}  # Personality traits
        self.relationships = relationships or {}  # Relationships with other NPCs and the player
        self.schedule = schedule or {}  # Daily schedule
        self.current_activity = "idle"
        self.money = money
        self.properties = properties or {}  # Custom properties
        self.influence_level = 0  # How much the player has influenced this NPC
        self.id = f"npc_{name.lower().replace(' ', '_')}"

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
        # Check relationship with player
        relationship = self.get_relationship(player)
        
        # Determine dialogue based on relationship
        if relationship < -50:
            print(f"{self.name}: {self.dialogue.get('hostile', 'Go away! I do not want to talk to you.')}")
            return
        
        # Regular dialogue
        if relationship > 50:
            print(f"{self.name}: {self.dialogue.get('friendly', self.dialogue['default'])}")
        else:
            print(f"{self.name}: {self.dialogue['default']}")
        
        # Show interaction options
        self.show_interaction_options(player)
    
    def show_interaction_options(self, player):
        """Show interaction options for the player."""
        print("\nInteraction options:")
        print("1. Chat")
        print("2. Trade")
        print("3. Influence")
        print("4. Leave")
        
        choice = input("What would you like to do? ")
        
        if choice == "1":
            self.chat(player)
        elif choice == "2":
            self.trade(player)
        elif choice == "3":
            self.attempt_influence(player)
        elif choice == "4":
            print(f"You end your conversation with {self.name}.")
        else:
            print("Invalid choice.")
    
    def chat(self, player):
        """Chat with the NPC."""
        relationship = self.get_relationship(player)
        
        # Different chat topics based on relationship
        if relationship > 30:
            topics = ["weather", "life", "gossip", "advice"]
        else:
            topics = ["weather", "general"]
        
        print("\nChat topics:")
        for i, topic in enumerate(topics, 1):
            print(f"{i}. {topic.capitalize()}")
        
        choice = input("What would you like to chat about? ")
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(topics):
                topic = topics[index]
                self.discuss_topic(topic, player)
            else:
                print("Invalid topic.")
        except ValueError:
            print("Please enter a number.")
    
    def discuss_topic(self, topic, player):
        """Discuss a specific topic with the NPC."""
        # Get topic-specific dialogue or use default
        topic_key = f"topic_{topic}"
        response = self.dialogue.get(topic_key, f"Let's talk about {topic}.")
        print(f"{self.name}: {response}")
        
        # Small relationship boost for chatting
        self.adjust_relationship(player, 2)
        print(f"{self.name} appreciates the conversation.")
    
    def trade(self, player):
        """Trade items with the NPC."""
        if not self.inventory and player.money < 10:
            print(f"{self.name} doesn't have anything to trade, and you don't have enough money.")
            return
        
        print("\nTrading options:")
        print("1. Buy from NPC")
        print("2. Sell to NPC")
        print("3. Cancel")
        
        choice = input("What would you like to do? ")
        
        if choice == "1":
            self.buy_from_npc(player)
        elif choice == "2":
            self.sell_to_npc(player)
        elif choice == "3":
            print("You decide not to trade.")
        else:
            print("Invalid choice.")
    
    def buy_from_npc(self, player):
        """Buy items from the NPC."""
        if not self.inventory:
            print(f"{self.name} doesn't have anything to sell.")
            return
        
        print(f"\n{self.name}'s inventory:")
        for i, item in enumerate(self.inventory, 1):
            price = item.value * 1.5  # NPCs sell at a markup
            print(f"{i}. {item.name}: ${price}")
        print(f"{len(self.inventory) + 1}. Cancel")
        
        choice = input("What would you like to buy? ")
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(self.inventory):
                item = self.inventory[index]
                price = item.value * 1.5
                
                if player.money >= price:
                    player.money -= price
                    self.money += price
                    self.inventory.remove(item)
                    player.add_item(item)
                    print(f"You bought {item.name} for ${price}.")
                    
                    # Small relationship boost for trading
                    self.adjust_relationship(player, 3)
                else:
                    print(f"You don't have enough money. {item.name} costs ${price}.")
            elif index == len(self.inventory):
                print("You decide not to buy anything.")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")
    
    def sell_to_npc(self, player):
        """Sell items to the NPC."""
        if not player.inventory:
            print("You don't have anything to sell.")
            return
        
        print("\nYour inventory:")
        for i, item in enumerate(player.inventory, 1):
            price = item.value * 0.7  # NPCs buy at a discount
            print(f"{i}. {item.name}: ${price}")
        print(f"{len(player.inventory) + 1}. Cancel")
        
        choice = input("What would you like to sell? ")
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(player.inventory):
                item = player.inventory[index]
                price = item.value * 0.7
                
                if self.money >= price:
                    self.money -= price
                    player.money += price
                    player.inventory.remove(item)
                    self.inventory.append(item)
                    print(f"You sold {item.name} for ${price}.")
                    
                    # Small relationship boost for trading
                    self.adjust_relationship(player, 2)
                else:
                    print(f"{self.name} doesn't have enough money to buy {item.name}.")
            elif index == len(player.inventory):
                print("You decide not to sell anything.")
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")
    
    def attempt_influence(self, player):
        """Player attempts to influence the NPC."""
        relationship = self.get_relationship(player)
        street_cred = player.street_cred
        
        # Calculate influence chance based on relationship and street cred
        influence_chance = 20 + relationship / 2 + street_cred / 10
        influence_chance = max(5, min(95, influence_chance))  # Cap between 5% and 95%
        
        print(f"You try to influence {self.name}...")
        
        if random.randint(1, 100) <= influence_chance:
            self.influence_level += 1
            print(f"Success! {self.name} is now more likely to do what you want.")
            
            # Show influence options
            self.show_influence_options(player)
        else:
            print(f"Failed. {self.name} isn't convinced by your persuasion.")
            
            # Relationship penalty for failed influence
            self.adjust_relationship(player, -5)
    
    def show_influence_options(self, player):
        """Show options for what the player can influence the NPC to do."""
        print("\nWhat would you like to influence the NPC to do?")
        print("1. Spend money at a specific location")
        print("2. Create a distraction")
        print("3. Follow you")
        print("4. Nothing for now")
        
        choice = input("Your choice: ")
        
        if choice == "1":
            self.influence_spending(player)
        elif choice == "2":
            self.create_distraction(player)
        elif choice == "3":
            self.follow_player(player)
        elif choice == "4":
            print("You decide not to influence the NPC right now.")
        else:
            print("Invalid choice.")
    
    def influence_spending(self, player):
        """
        Influence the NPC to spend money at a specific location.
        
        # VITA'S INFLUENCE: This method allows Vita to influence NPCs to spend money
        """
        # Set the NPC as influenced by the player
        self.influence_level += 1
        self.set_property("likes_shopping", True)
        
        # If NPC is in a location with items, they'll consider purchasing them
        if self.location and hasattr(self.location, 'items') and self.location.items:
            print(f"You convince {self.name} to shop at {self.location.name}.")
            # Increased chance of purchase when influenced
            self.check_nearby_items(self.location, player, purchase_chance=70)
        else:
            print(f"You convince {self.name} to spend money at a business of your choice.")
            print("They'll be more likely to purchase items when they're near a shop.")
        
        # Relationship adjustment
        self.adjust_relationship(player, -2)  # Slight negative for manipulation
    
    def create_distraction(self, player):
        """Influence the NPC to create a distraction."""
        print(f"{self.name} creates a commotion, distracting everyone in the area!")
        print("(This would affect NPC behaviors in a full implementation)")
        
        # Relationship adjustment
        self.adjust_relationship(player, -3)  # Negative for manipulation
    
    def follow_player(self, player):
        """Influence the NPC to follow the player."""
        print(f"{self.name} agrees to follow you for a while.")
        self.set_property("following_player", True)
        
        # Relationship adjustment
        self.adjust_relationship(player, -1)  # Slight negative for manipulation
    
    def add_to_inventory(self, item):
        """Add an item to the NPC's inventory."""
        self.inventory.append(item)
        
    def remove_from_inventory(self, item_name):
        """Remove an item from the NPC's inventory."""
        item = next((i for i in self.inventory if i.name.lower() == item_name.lower()), None)
        if item:
            self.inventory.remove(item)
            return item
        return None
        
    def consider_purchase(self, item, player=None, chance=40):
        """
        NPC considers purchasing an item based on a chance percentage.
        
        # NPC PURCHASING: This method handles NPCs buying items
        
        Args:
            item: The item to consider purchasing
            player: The player who will receive money if influenced
            chance: Percentage chance (0-100) that NPC will purchase
            
        Returns:
            bool: True if purchase was made, False otherwise
        """
        # Check if NPC has enough money
        if self.money < item.value:
            return False
            
        # Determine if NPC will purchase based on chance
        if random.randint(1, 100) <= chance:
            # Purchase the item
            self.money -= item.value
            self.add_to_inventory(item)
            
            # If player is influencing this purchase, they get the money
            if player and self.influence_level > 0:
                player.money += item.value
                print(f"{self.name} purchased {item.name} for ${item.value}. The money goes to you!")
                return True
            else:
                print(f"{self.name} purchased {item.name} for ${item.value}.")
                return True
                
        return False
        
    def check_nearby_items(self, area, player=None, purchase_chance=40):
        """
        Check for items in the NPC's current area and consider purchasing them.
        
        Args:
            area: The area to check for items
            player: The player who will receive money if influenced
            purchase_chance: Chance of purchasing an item
        """
        if not area or not hasattr(area, 'items') or not area.items:
            return
            
        # Get the NPC's position in the area
        if hasattr(self, 'coordinates') and hasattr(area, 'get_relative_coordinates'):
            rel_x, rel_y, rel_z = area.get_relative_coordinates(self.coordinates)
        else:
            # If coordinates aren't available, assume NPC can see all items
            rel_x, rel_y, rel_z = None, None, None
            
        # Check each item in the area
        for item in list(area.items):  # Create a copy of the list to avoid modification issues
            # If we have coordinates, only consider items that are nearby (within 2 grid spaces)
            if rel_x is not None and hasattr(item, 'coordinates'):
                item_rel_x, item_rel_y, item_rel_z = area.get_relative_coordinates(item.coordinates)
                distance = ((rel_x - item_rel_x) ** 2 + (rel_y - item_rel_y) ** 2) ** 0.5
                if distance > 2:  # Only consider items within 2 grid spaces
                    continue
                    
            # Check if the item is clothing and the NPC is interested
            if hasattr(item, 'type') and item.type == "Clothing" and self.get_property("likes_shopping", False):
                # Try to purchase the item
                if self.consider_purchase(item, player, purchase_chance):
                    # If purchased, remove from area
                    area.remove_item(item.name)
                    # Only purchase one item at a time
                    break
    
    def set_relationship(self, entity, value):
        """Set relationship value with another entity (NPC or player)."""
        self.relationships[entity.name] = value
    
    def adjust_relationship(self, entity, amount):
        """Adjust relationship value with another entity."""
        current = self.get_relationship(entity)
        self.relationships[entity.name] = max(-100, min(100, current + amount))
        
    def get_relationship(self, entity):
        """Get relationship value with another entity."""
        return self.relationships.get(entity.name, 0)
    
    def set_schedule(self, time, activity, location=None):
        """Set the NPC's schedule for a specific time."""
        self.schedule[time] = (activity, location)
    
    def update_activity(self, current_time, player=None):
        """Update the NPC's activity based on the current time."""
        # Find the closest scheduled time
        scheduled_times = sorted(self.schedule.keys())
        current_activity = "idle"
        current_location = None
        
        for time in scheduled_times:
            if current_time >= time:
                current_activity, current_location = self.schedule[time]
            else:
                break
        
        self.current_activity = current_activity
        if current_location and current_location != self.location:
            self.set_location(current_location)
            
        # If NPC likes shopping and is in a location with items, consider purchasing
        if self.get_property("likes_shopping", False) and self.location:
            # NPCs influenced by the player have a higher chance of purchasing
            purchase_chance = 70 if self.influence_level > 0 else 40
            self.check_nearby_items(self.location, player, purchase_chance)
    
    def set_property(self, key, value):
        """Set a custom property for this NPC."""
        self.properties[key] = value
    
    def get_property(self, key, default=None):
        """Get a custom property for this NPC."""
        return self.properties.get(key, default)
    
    def to_dict(self):
        """Convert NPC to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "dialogue": self.dialogue,
            "personality": self.personality,
            "relationships": self.relationships,
            "money": self.money,
            "properties": self.properties,
            "influence_level": self.influence_level,
            "schedule": {k: (v[0], v[1].id if v[1] else None) for k, v in self.schedule.items()},
            "inventory": [item.id for item in self.inventory]
        }
    
    @classmethod
    def from_dict(cls, data, location_resolver=None, item_resolver=None):
        """Create NPC from dictionary."""
        npc = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data["dialogue"],
            data["personality"],
            data["money"],
            data["relationships"],
            data["properties"]
        )
        npc.id = data.get("id", npc.id)
        npc.influence_level = data.get("influence_level", 0)
        
        # Resolve schedule if location_resolver is provided
        if location_resolver and "schedule" in data:
            for time, (activity, location_id) in data["schedule"].items():
                if location_id:
                    location = location_resolver(location_id)
                    if location:
                        npc.schedule[time] = (activity, location)
        
        # Resolve inventory if item_resolver is provided
        if item_resolver and "inventory" in data:
            for item_id in data["inventory"]:
                item = item_resolver(item_id)
                if item:
                    npc.inventory.append(item)
        
        return npc


class NPCManager:
    """Manages all NPCs in the game."""
    def __init__(self):
        self.npcs = {}  # Dictionary mapping NPC IDs to NPC objects
        self.templates = {}  # Dictionary of NPC templates
    
    def add_npc(self, npc):
        """Add an NPC to the manager."""
        self.npcs[npc.id] = npc
    
    def get_npc(self, npc_id):
        """Get an NPC by ID."""
        return self.npcs.get(npc_id)
    
    def add_template(self, template_id, template_data):
        """Add an NPC template."""
        self.templates[template_id] = template_data
    
    def create_from_template(self, template_id, **kwargs):
        """Create an NPC from a template."""
        if template_id not in self.templates:
            raise ValueError(f"Unknown NPC template: {template_id}")
        
        template = self.templates[template_id].copy()
        
        # Generate a unique name if needed
        if "name_suffix" in kwargs:
            suffix = kwargs.pop("name_suffix")
            template["name"] = f"{template['name']} {suffix}"
        
        # Override template values with provided kwargs
        template.update(kwargs)
        
        npc = NPC(**template)
        
        # Generate a unique ID if needed
        if "id" in kwargs:
            npc.id = kwargs["id"]
        
        return npc
    
    def update_all_npcs(self, current_time, player=None):
        """Update all NPCs based on the current time."""
        for npc in self.npcs.values():
            npc.update_activity(current_time, player)
    
    def save_to_json(self, filename):
        """Save all NPCs to a JSON file."""
        data = {
            "npcs": {npc_id: npc.to_dict() for npc_id, npc in self.npcs.items()},
            "templates": self.templates
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_json(self, filename, location_resolver=None, item_resolver=None):
        """Load NPCs from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # Load templates
        self.templates = data.get("templates", {})
        
        # Load NPCs
        for npc_id, npc_data in data.get("npcs", {}).items():
            npc = NPC.from_dict(npc_data, location_resolver, item_resolver)
            self.add_npc(npc)