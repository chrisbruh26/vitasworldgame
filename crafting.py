"""
Crafting module for Vita Game.
Handles crafting recipes and item creation.
"""

import json

class Recipe:
    """Recipe class for crafting items."""
    def __init__(self, name, description, ingredients, result, skill_requirements=None):
        self.name = name
        self.description = description
        self.ingredients = ingredients  # Dictionary mapping item names to quantities
        self.result = result  # The item that will be created
        self.skill_requirements = skill_requirements or {}  # Dictionary mapping skill names to required levels
        self.id = f"recipe_{name.lower().replace(' ', '_')}"
    
    def can_craft(self, player):
        """Check if the player has the required ingredients and skills."""
        # Check skills
        for skill, level in self.skill_requirements.items():
            if player.skills.get(skill, 0) < level:
                return False, f"You need {skill} level {level} to craft this."
        
        # Check ingredients
        for ingredient, quantity in self.ingredients.items():
            count = sum(1 for item in player.inventory if item.name.lower() == ingredient.lower())
            if count < quantity:
                return False, f"You need {quantity} {ingredient}(s), but you only have {count}."
        
        return True, "You have all the required ingredients and skills."
    
    def craft(self, player, item_manager):
        """Craft the item if the player has the required ingredients and skills."""
        can_craft, message = self.can_craft(player)
        if not can_craft:
            print(message)
            return None
        
        # Remove ingredients from inventory
        for ingredient, quantity in self.ingredients.items():
            for _ in range(quantity):
                # Find and remove the ingredient
                item = next((i for i in player.inventory if i.name.lower() == ingredient.lower()), None)
                if item:
                    player.inventory.remove(item)
        
        # Create the result item
        if isinstance(self.result, dict):
            # Create from template
            template_id = self.result.get("template")
            if template_id:
                result_item = item_manager.create_from_template(template_id, **self.result.get("overrides", {}))
            else:
                # Create directly from parameters
                item_type = self.result.get("type", "Item")
                if item_type == "Food":
                    from .items import Food
                    result_item = Food(**self.result)
                elif item_type == "Jetpack":
                    from .items import Jetpack
                    result_item = Jetpack(**self.result)
                else:
                    from .items import Item
                    result_item = Item(**self.result)
        else:
            # Result is already an item instance
            result_item = self.result
        
        print(f"You crafted {result_item.name}!")
        player.add_item(result_item)
        
        # Award skill experience
        for skill in self.skill_requirements:
            player.skills[skill] = player.skills.get(skill, 0) + 1
            print(f"Your {skill} skill increased to {player.skills[skill]}!")
        
        return result_item
    
    def to_dict(self):
        """Convert recipe to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "ingredients": self.ingredients,
            "result": self.result.id if hasattr(self.result, 'id') else self.result,
            "skill_requirements": self.skill_requirements
        }


class CraftingSystem:
    """System for managing crafting recipes."""
    def __init__(self, item_manager):
        self.recipes = {}  # Dictionary mapping recipe IDs to Recipe objects
        self.item_manager = item_manager
    
    def add_recipe(self, recipe):
        """Add a recipe to the system."""
        self.recipes[recipe.id] = recipe
    
    def get_recipe(self, recipe_id):
        """Get a recipe by ID."""
        return self.recipes.get(recipe_id)
    
    def get_recipe_by_name(self, recipe_name):
        """Get a recipe by name."""
        return next((r for r in self.recipes.values() if r.name.lower() == recipe_name.lower()), None)
    
    def list_available_recipes(self, player):
        """List recipes that the player can craft."""
        available_recipes = []
        for recipe in self.recipes.values():
            can_craft, _ = recipe.can_craft(player)
            if can_craft:
                available_recipes.append(recipe)
        return available_recipes
    
    def craft_item(self, recipe_name, player):
        """Craft an item using a recipe."""
        recipe = self.get_recipe_by_name(recipe_name)
        if recipe:
            return recipe.craft(player, self.item_manager)
        else:
            print(f"Recipe '{recipe_name}' not found.")
            return None
    
    def save_to_json(self, filename):
        """Save all recipes to a JSON file."""
        data = {recipe_id: recipe.to_dict() for recipe_id, recipe in self.recipes.items()}
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_from_json(self, filename, item_resolver=None):
        """Load recipes from a JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        for recipe_id, recipe_data in data.items():
            # Resolve result item if it's an ID and item_resolver is provided
            result = recipe_data["result"]
            if isinstance(result, str) and item_resolver:
                result = item_resolver(result)
            elif isinstance(result, dict) and "template" in result:
                # Keep as is, will be resolved during crafting
                pass
            
            recipe = Recipe(
                recipe_data["name"],
                recipe_data["description"],
                recipe_data["ingredients"],
                result,
                recipe_data.get("skill_requirements", {})
            )
            recipe.id = recipe_data.get("id", recipe.id)
            self.add_recipe(recipe)