class Quest:
    """Base Quest class for side missions."""
    def __init__(self, name, description, objective=None, reward=None):
        self.name = name
        self.description = description
        self.objective = objective  # Function that checks if quest is completed
        self.reward = reward  # Function that gives rewards
        self.active = False
        self.completed = False
        self.giver = None  # NPC who gave the quest
        self.progress = 0  # Progress from 0 to 100
    
    def start(self, player):
        """Start the quest."""
        self.active = True
        print(f"Quest started: {self.name}")
        print(self.description)
    
    def check_progress(self, player):
        """Check the current progress of the quest."""
        return f"Progress: {self.progress}%"
    
    def attempt_complete(self, player):
        """Check if the quest is completed and complete it if so."""
        if self.objective and self.objective(player):
            self.complete(player)
            return True
        return False
    
    def complete(self, player):
        """Complete the quest and give rewards."""
        self.completed = True
        self.active = False
        print(f"Quest completed: {self.name}")
        if self.reward:
            self.reward(player)
    
    def to_dict(self):
        """Convert quest to dictionary for serialization."""
        return {
            "type": self.__class__.__name__,
            "name": self.name,
            "description": self.description,
            "active": self.active,
            "completed": self.completed,
            "progress": self.progress,
            "giver": self.giver.name if self.giver else None
        }


class ItemCollectionQuest(Quest):
    """Quest to collect a certain number of items."""
    def __init__(self, name, description, item_name, quantity=1, reward=None):
        super().__init__(name, description, reward=reward)
        self.item_name = item_name
        self.quantity = quantity
    
    def check_progress(self, player):
        """Check how many items the player has collected."""
        count = sum(1 for item in player.inventory if item.name.lower() == self.item_name.lower())
        self.progress = min(100, int((count / self.quantity) * 100))
        return f"Collected: {count}/{self.quantity} {self.item_name}s ({self.progress}%)"
    
    def attempt_complete(self, player):
        """Check if the player has collected enough items."""
        count = sum(1 for item in player.inventory if item.name.lower() == self.item_name.lower())
        if count >= self.quantity:
            # Remove the items from inventory
            items_to_remove = []
            for item in player.inventory:
                if item.name.lower() == self.item_name.lower() and len(items_to_remove) < self.quantity:
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                player.inventory.remove(item)
            
            self.complete(player)
            return True
        return False
    
    def to_dict(self):
        """Convert quest to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "item_name": self.item_name,
            "quantity": self.quantity
        })
        return data


class DeliveryQuest(Quest):
    """Quest to deliver an item to an NPC."""
    def __init__(self, name, description, item_name, target_npc, reward=None):
        super().__init__(name, description, reward=reward)
        self.item_name = item_name
        self.target_npc = target_npc
    
    def check_progress(self, player):
        """Check if the player has the item to deliver."""
        has_item = any(item.name.lower() == self.item_name.lower() for item in player.inventory)
        self.progress = 50 if has_item else 0
        return f"{'Item acquired' if has_item else 'Need to find ' + self.item_name}, deliver to {self.target_npc.name}"
    
    def attempt_complete(self, player):
        """Check if the player is talking to the target NPC with the item."""
        if player.current_area != self.target_npc.location:
            return False
            
        item = next((i for i in player.inventory if i.name.lower() == self.item_name.lower()), None)
        if item:
            player.inventory.remove(item)
            self.complete(player)
            return True
        return False
    
    def to_dict(self):
        """Convert quest to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "item_name": self.item_name,
            "target_npc": self.target_npc.name if self.target_npc else None
        })
        return data


class ExplorationQuest(Quest):
    """Quest to explore a specific area."""
    def __init__(self, name, description, target_area, reward=None):
        super().__init__(name, description, reward=reward)
        self.target_area = target_area
        self.visited = False
    
    def check_progress(self, player):
        """Check if the player has visited the target area."""
        if player.current_area == self.target_area:
            self.visited = True
            self.progress = 100
            return f"You've found {self.target_area.name}!"
        else:
            return f"Need to find and explore {self.target_area.name}"
    
    def attempt_complete(self, player):
        """Check if the player has visited the target area."""
        if self.visited or player.current_area == self.target_area:
            self.complete(player)
            return True
        return False
    
    def to_dict(self):
        """Convert quest to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "target_area": self.target_area.name if self.target_area else None,
            "visited": self.visited
        })
        return data


class MischiefQuest(Quest):
    """Quest to cause a specific type of mischief."""
    def __init__(self, name, description, mischief_type, target=None, quantity=1, reward=None):
        super().__init__(name, description, reward=reward)
        self.mischief_type = mischief_type  # e.g., "steal", "prank", "confuse"
        self.target = target  # NPC or area
        self.quantity = quantity
        self.progress_count = 0
    
    def record_mischief(self, mischief_type, target=None):
        """Record a mischief action by the player."""
        if mischief_type == self.mischief_type and (not self.target or target == self.target):
            self.progress_count += 1
            self.progress = min(100, int((self.progress_count / self.quantity) * 100))
            print(f"Mischief recorded! Progress: {self.progress_count}/{self.quantity}")
            
            if self.progress_count >= self.quantity:
                return True
        return False
    
    def check_progress(self, player):
        """Check the progress of the mischief quest."""
        target_name = self.target.name if self.target else "anyone"
        return f"{self.mischief_type.capitalize()} {target_name}: {self.progress_count}/{self.quantity} ({self.progress}%)"
    
    def to_dict(self):
        """Convert quest to dictionary for serialization."""
        data = super().to_dict()
        data.update({
            "mischief_type": self.mischief_type,
            "target": self.target.name if self.target else None,
            "quantity": self.quantity,
            "progress_count": self.progress_count
        })
        return data


# Factory function to create quests from templates
def create_quest_from_template(template_name, **kwargs):
    """Create a quest from a predefined template with optional overrides."""
    templates = {
        "acorn_collection": {
            "class": ItemCollectionQuest,
            "name": "Acorn Collector",
            "description": "Find 10 acorns for the squirrels. Golden acorns count as 2!",
            "item_name": "Acorn",
            "quantity": 10
        },
        "carrot_delivery": {
            "class": DeliveryQuest,
            "name": "Carrot Courier",
            "description": "Deliver a fresh carrot to the farmer.",
            "item_name": "Carrot"
            # target_npc needs to be provided
        },
        "skyscraper_exploration": {
            "class": ExplorationQuest,
            "name": "Sky High",
            "description": "Explore the top of the skyscraper for a great view."
            # target_area needs to be provided
        },
        "store_mischief": {
            "class": MischiefQuest,
            "name": "Retail Chaos",
            "description": "Cause confusion by moving items between stores in the mall.",
            "mischief_type": "move_items",
            "quantity": 5
        },
        "airport_trespass": {
            "class": MischiefQuest,
            "name": "Runway Rabbit",
            "description": "Trespass into the restricted areas of the airport.",
            "mischief_type": "trespass",
            "quantity": 1
        }
    }
    
    if template_name not in templates:
        raise ValueError(f"Unknown quest template: {template_name}")
    
    template = templates[template_name].copy()
    quest_class = template.pop("class")
    
    # Override template values with provided kwargs
    template.update(kwargs)
    
    return quest_class(**template)