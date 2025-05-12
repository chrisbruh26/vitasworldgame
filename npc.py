from .coordinates import Coordinates
from .items import Item

class NPC:
    """NPC class representing non-player characters in the game world."""
    def __init__(self, name, description, coordinates=None, dialogue=None, personality=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.location = None
        self.dialogue = dialogue if dialogue else {"default": "Hello there!"}
        self.quests = []   # Multi-quest support
        self.inventory = []  # NPC's inventory
        self.personality = personality or {}  # Personality traits
        self.relationships = {}  # Relationships with other NPCs and the player
        self.schedule = {}  # Daily schedule
        self.current_activity = "idle"
        self.money = 0
        self.properties = {}  # Custom properties

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
        # First check for new quest system
        active_quests = [q for q in self.quests if hasattr(q, 'active') and q.active and q.giver == self]
        completed_quests = [q for q in self.quests if hasattr(q, 'completed') and q.completed and q.giver == self]
        available_quests = [q for q in self.quests if not hasattr(q, 'active') or (not q.active and not q.completed) and q.giver == self]
        
        # Check relationship with player
        relationship = self.get_relationship(player)
        
        # Determine dialogue based on relationship and quests
        if relationship < -50:
            print(f"{self.name}: {self.dialogue.get('hostile', 'Go away! I don\'t want to talk to you.')}")
            return
        
        if active_quests and "quest_active" in self.dialogue:
            print(f"{self.name}: {self.dialogue['quest_active']}")
            for quest in active_quests:
                print(f"Quest: {quest.name} - {quest.check_progress(player)}")
                
                # Check if the quest can be completed
                if hasattr(quest, 'attempt_complete'):
                    quest.attempt_complete(player)
                    if quest.completed and "quest_complete" in self.dialogue:
                        print(f"{self.name}: {self.dialogue['quest_complete']}")
        
        elif completed_quests and "quest_complete" in self.dialogue:
            print(f"{self.name}: {self.dialogue['quest_complete']}")
        
        elif available_quests:
            if "quest_available" in self.dialogue:
                print(f"{self.name}: {self.dialogue['quest_available']}")
            else:
                print(f"{self.name}: {self.dialogue['default']}")
                
            print(f"{self.name} has a quest for you:")
            for i, quest in enumerate(available_quests):
                print(f"{i+1}. {quest.name}: {quest.description}")
                
            # In a real game, you would handle quest acceptance here
            print("(You can accept a quest by typing 'accept quest [number]')")
        
        else:
            # No quests, just regular dialogue
            if relationship > 50:
                print(f"{self.name}: {self.dialogue.get('friendly', self.dialogue['default'])}")
            else:
                print(f"{self.name}: {self.dialogue['default']}")
    
    def give_quest(self, player, quest_index=0):
        """Give a quest to the player."""
        if not self.quests or quest_index >= len(self.quests):
            print(f"{self.name} doesn't have that quest to give.")
            return
            
        quest = self.quests[quest_index]
        if hasattr(quest, 'active') and quest.active:
            print(f"You've already accepted the quest '{quest.name}'.")
            print(quest.check_progress(player))
            return
            
        if hasattr(quest, 'completed') and quest.completed:
            print(f"You've already completed the quest '{quest.name}'.")
            return
            
        quest.start(player)
    
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
    
    def update_activity(self, current_time):
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
    
    def set_property(self, key, value):
        """Set a custom property for this NPC."""
        self.properties[key] = value
    
    def get_property(self, key, default=None):
        """Get a custom property for this NPC."""
        return self.properties.get(key, default)
    
    def to_dict(self):
        """Convert NPC to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates.to_dict(),
            "dialogue": self.dialogue,
            "personality": self.personality,
            "relationships": self.relationships,
            "money": self.money,
            "properties": self.properties,
            "schedule": {k: (v[0], v[1].name if v[1] else None) for k, v in self.schedule.items()}
        }
    
    @classmethod
    def from_dict(cls, data, location_resolver=None):
        """Create NPC from dictionary."""
        npc = cls(
            data["name"],
            data["description"],
            Coordinates.from_dict(data["coordinates"]),
            data["dialogue"],
            data["personality"]
        )
        npc.relationships = data["relationships"]
        npc.money = data["money"]
        npc.properties = data["properties"]
        
        # Schedule needs to be resolved after all areas are created
        # This would be handled by a game loader
        
        return npc


# Factory function to create NPCs from templates
def create_npc_from_template(template_name, **kwargs):
    """Create an NPC from a predefined template with optional overrides."""
    templates = {
        "squirrel": {
            "name": "Squirrel",
            "description": "A bushy-tailed squirrel with a worried expression.",
            "dialogue": {
                "default": "I've lost my acorns! Can you help me find some acorns?",
                "quest_active": "Have you found my acorns yet?",
                "quest_complete": "Thank you for finding my acorns! Now I can survive the winter."
            },
            "personality": {
                "nervousness": 70,
                "friendliness": 50
            }
        },
        "shopkeeper": {
            "name": "Shopkeeper",
            "description": "A friendly shopkeeper who sells various items.",
            "dialogue": {
                "default": "Welcome to my shop! What would you like to buy?",
                "friendly": "Ah, my favorite customer! What can I get for you today?",
                "hostile": "I don't serve troublemakers. Leave my shop!"
            },
            "personality": {
                "friendliness": 60,
                "greed": 40
            },
            "money": 500
        },
        "police_officer": {
            "name": "Police Officer",
            "description": "A stern-looking police officer keeping the peace.",
            "dialogue": {
                "default": "Move along, citizen. Nothing to see here.",
                "hostile": "You're causing trouble. I'm keeping my eye on you!"
            },
            "personality": {
                "strictness": 80,
                "suspicion": 60
            }
        },
        "pilot": {
            "name": "Pilot",
            "description": "A professional pilot who flies planes and helicopters.",
            "dialogue": {
                "default": "The skies are clear today. Perfect for flying!",
                "quest_available": "I need someone to help me with a delivery. Interested?"
            },
            "personality": {
                "adventurousness": 90,
                "professionalism": 70
            }
        },
        "farmer": {
            "name": "Farmer",
            "description": "A hardworking farmer tending to crops and animals.",
            "dialogue": {
                "default": "It's honest work, farming. But those pesky rabbits keep eating my crops!",
                "hostile": "Hey! Stay away from my crops, you varmint!"
            },
            "personality": {
                "hardworking": 85,
                "patience": 60
            }
        },
        "casino_dealer": {
            "name": "Casino Dealer",
            "description": "A professional dealer running games at the casino.",
            "dialogue": {
                "default": "Place your bets! Who's feeling lucky today?",
                "friendly": "Hey there, high roller! Ready to try your luck again?"
            },
            "personality": {
                "professionalism": 90,
                "poker_face": 95
            },
            "money": 1000
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown NPC template: {template_name}")
    
    template = templates[template_name].copy()
    
    # Generate a unique name if needed
    if "name_suffix" in kwargs:
        suffix = kwargs.pop("name_suffix")
        template["name"] = f"{template['name']} {suffix}"
    
    # Override template values with provided kwargs
    template.update(kwargs)
    
    return NPC(**template)