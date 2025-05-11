"""
Templates module for Vita Game.
This module provides template classes for creating game entities efficiently.
"""

from quests import ItemRequestQuest

class EntityTemplate:
    """Base template class for all game entities."""
    def __init__(self, entity_type, default_attributes=None):
        self.entity_type = entity_type
        self.default_attributes = default_attributes or {}
        
    def create(self, **kwargs):
        """
        Create an instance of the entity with the specified attributes.
        Any attributes not specified will use the default values.
        """
        # Combine default attributes with provided kwargs (kwargs take precedence)
        attributes = self.default_attributes.copy()
        attributes.update(kwargs)
        
        # Create and return the entity
        return self.entity_type(**attributes)


class ItemTemplate(EntityTemplate):
    """Template for creating items."""
    def __init__(self, item_class, name, description, **default_attributes):
        super().__init__(item_class, default_attributes)
        self.default_attributes['name'] = name
        self.default_attributes['description'] = description


class NPCTemplate(EntityTemplate):
    """Template for creating NPCs."""
    def __init__(self, npc_class, name, description, dialogue=None, **default_attributes):
        super().__init__(npc_class, default_attributes)
        self.default_attributes['name'] = name
        self.default_attributes['description'] = description
        self.default_attributes['dialogue'] = dialogue or {"default": "Hello!"}


class GameObjectTemplate(EntityTemplate):
    """Template for creating game objects."""
    def __init__(self, object_class, name, description, **default_attributes):
        super().__init__(object_class, default_attributes)
        self.default_attributes['name'] = name
        self.default_attributes['description'] = description


class AreaTemplate(EntityTemplate):
    """Template for creating areas."""
    def __init__(self, area_class, name, description, grid_width=10, grid_length=10, height=1, **default_attributes):
        super().__init__(area_class, default_attributes)
        self.default_attributes['name'] = name
        self.default_attributes['description'] = description
        self.default_attributes['grid_width'] = grid_width
        self.default_attributes['grid_length'] = grid_length
        self.default_attributes['height'] = height
        
    def create_with_objects(self, coordinates=None, objects=None, npcs=None, items=None, **kwargs):
        """
        Create an area and populate it with objects, NPCs, and items.
        
        Args:
            coordinates: The coordinates for the area
            objects: List of (object, x, y, z) tuples
            npcs: List of (npc, x, y, z) tuples
            items: List of (item, x, y, z) tuples
            **kwargs: Additional attributes for the area
            
        Returns:
            The created area with all objects placed
        """
        # Create the area
        area = self.create(coordinates=coordinates, **kwargs)
        
        # Place objects
        if objects:
            for obj, x, y, z in objects:
                area.place_object_at(obj, x, y, z)
                
        # Place NPCs
        if npcs:
            for npc, x, y, z in npcs:
                area.place_object_at(npc, x, y, z)
                
        # Place items
        if items:
            for item, x, y, z in items:
                area.place_object_at(item, x, y, z)
                
        return area


class QuestTemplate:
    """Template for creating quests."""
    def __init__(self, quest_type, name, description, reward=None, **default_attributes):
        self.quest_type = quest_type
        self.name = name
        self.description = description
        self.reward = reward
        self.default_attributes = default_attributes
        
    def create(self, npc, **kwargs):
        """Create a quest instance and assign it to an NPC."""
        # Combine default attributes with provided kwargs
        attributes = self.default_attributes.copy()
        attributes.update(kwargs)
        
        # Create the quest
        quest = self.quest_type(
            name=self.name,
            description=self.description,
            reward=self.reward,
            giver=npc,
            **attributes
        )
        
        # Assign the quest to the NPC
        if not hasattr(npc, 'quests'):
            npc.quests = []
        npc.quests.append(quest)
        
        return quest


class ItemRequestQuestTemplate(QuestTemplate):
    """Template for creating item request quests."""
    def __init__(self, name, description, required_item, quantity=1, reward=None, **default_attributes):
        super().__init__(
            ItemRequestQuest,  # This will be defined in the quest module
            name,
            description,
            reward,
            required_item=required_item,
            quantity=quantity,
            **default_attributes
        )


# Example templates (these would be defined elsewhere and imported)
"""
# Item Templates
CARROT_TEMPLATE = ItemTemplate(
    Food,
    "Carrot",
    "A fresh orange carrot.",
    nutrition=15
)

# NPC Templates
SQUIRREL_TEMPLATE = NPCTemplate(
    NPC,
    "Squirrel",
    "A bushy-tailed squirrel looking for acorns.",
    dialogue={"default": "Squeak! (He seems to be looking for acorns.)"}
)

# GameObject Templates
TREE_TEMPLATE = GameObjectTemplate(
    GameObject,
    "Tree",
    "A tall oak tree with branches perfect for climbing."
)

# Quest Templates
ACORN_QUEST_TEMPLATE = ItemRequestQuestTemplate(
    "Acorn Collector",
    "Collect 10 acorns for the hungry squirrel.",
    required_item="Acorn",
    quantity=10,
    reward={"street_cred": 5}
)
"""
