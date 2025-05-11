"""
Quests module for Vita Game.
This module provides classes for creating and managing quests.
"""

class Quest:
    """Base class for all quests in the game."""
    def __init__(self, name, description, reward=None, giver=None):
        self.name = name
        self.description = description
        self.reward = reward or {}
        self.giver = giver
        self.completed = False
        self.active = False
        
    def start(self, player):
        """Start the quest."""
        self.active = True
        print(f"Quest started: {self.name}")
        print(self.description)
        
    def complete(self, player):
        """Complete the quest and give rewards."""
        if not self.active:
            print("This quest hasn't been started yet.")
            return False
            
        if self.completed:
            print("This quest has already been completed.")
            return False
            
        self.completed = True
        self.active = False
        print(f"Quest completed: {self.name}")
        
        # Apply rewards
        self._apply_rewards(player)
        
        return True
        
    def _apply_rewards(self, player):
        """Apply quest rewards to the player."""
        if 'street_cred' in self.reward:
            player.street_cred += self.reward['street_cred']
            print(f"You gained {self.reward['street_cred']} street cred!")
            
        if 'items' in self.reward:
            for item in self.reward['items']:
                player.add_item(item)
                print(f"You received: {item.name}")
                
        if 'energy' in self.reward:
            player.energy = min(player.max_energy, player.energy + self.reward['energy'])
            print(f"You gained {self.reward['energy']} energy!")
            
    def check_progress(self, player):
        """Check the progress of the quest."""
        if not self.active:
            return "Not started"
        elif self.completed:
            return "Completed"
        else:
            return "In progress"
            
    def __str__(self):
        status = "Completed" if self.completed else "Active" if self.active else "Not started"
        return f"{self.name} ({status}): {self.description}"


class ItemRequestQuest(Quest):
    """Quest that requires the player to bring specific items to an NPC."""
    def __init__(self, name, description, required_item, quantity=1, reward=None, giver=None):
        super().__init__(name, description, reward, giver)
        self.required_item = required_item
        self.quantity = quantity
        self.current_quantity = 0
        
    def check_progress(self, player):
        """Check if the player has the required items."""
        if self.completed:
            return "Completed"
            
        if not self.active:
            return "Not started"
            
        # Count matching items in inventory
        matching_items = [item for item in player.inventory 
                         if item.name.lower() == self.required_item.lower()]
        self.current_quantity = len(matching_items)
        
        if self.current_quantity >= self.quantity:
            return f"Ready to complete! ({self.current_quantity}/{self.quantity} {self.required_item}s)"
        else:
            return f"In progress: {self.current_quantity}/{self.quantity} {self.required_item}s"
            
    def attempt_complete(self, player):
        """Try to complete the quest by checking for required items."""
        if self.completed:
            print("This quest has already been completed.")
            return False
            
        if not self.active:
            print("This quest hasn't been started yet.")
            return False
            
        # Check if player has enough of the required item
        matching_items = [item for item in player.inventory 
                         if item.name.lower() == self.required_item.lower()]
        
        if len(matching_items) >= self.quantity:
            # Remove the items from inventory
            for _ in range(self.quantity):
                item = next(item for item in player.inventory 
                           if item.name.lower() == self.required_item.lower())
                player.inventory.remove(item)
                
            # Complete the quest
            return self.complete(player)
        else:
            print(f"You don't have enough {self.required_item}s. " 
                 f"You need {self.quantity}, but you only have {len(matching_items)}.")
            return False


class LocationQuest(Quest):
    """Quest that requires the player to visit a specific location."""
    def __init__(self, name, description, target_area, target_coords=None, reward=None, giver=None):
        super().__init__(name, description, reward, giver)
        self.target_area = target_area
        self.target_coords = target_coords  # Optional specific coordinates within the area
        
    def check_location(self, player):
        """Check if the player is at the target location."""
        if not self.active or self.completed:
            return False
            
        # Check if player is in the right area
        if player.current_area != self.target_area:
            return False
            
        # If target coordinates are specified, check those too
        if self.target_coords:
            grid_x, grid_y, grid_z = player.get_grid_position()
            target_x, target_y, target_z = self.target_coords
            
            if grid_x != target_x or grid_y != target_y or grid_z != target_z:
                return False
                
        return True
        
    def check_progress(self, player):
        """Check the progress of the quest."""
        if self.completed:
            return "Completed"
            
        if not self.active:
            return "Not started"
            
        if self.check_location(player):
            return "You've reached the destination!"
        else:
            area_name = self.target_area.name
            if self.target_coords:
                x, y, z = self.target_coords
                return f"In progress: Find location at coordinates ({x}, {y}, {z}) in {area_name}"
            else:
                return f"In progress: Find {area_name}"


class MultiStepQuest(Quest):
    """Quest with multiple steps that must be completed in sequence."""
    def __init__(self, name, description, steps=None, reward=None, giver=None):
        super().__init__(name, description, reward, giver)
        self.steps = steps or []
        self.current_step = 0
        
    def add_step(self, step_description, step_quest):
        """Add a step to the quest."""
        self.steps.append((step_description, step_quest))
        
    def start(self, player):
        """Start the quest and the first step."""
        super().start(player)
        if self.steps:
            _, first_quest = self.steps[0]
            first_quest.start(player)
            
    def check_progress(self, player):
        """Check the progress of the current step."""
        if self.completed:
            return "Completed"
            
        if not self.active:
            return "Not started"
            
        if self.current_step >= len(self.steps):
            return "Ready to complete!"
            
        step_desc, step_quest = self.steps[self.current_step]
        step_progress = step_quest.check_progress(player)
        
        return f"Step {self.current_step + 1}/{len(self.steps)}: {step_desc} - {step_progress}"
        
    def advance_step(self, player):
        """Advance to the next step of the quest."""
        if self.current_step >= len(self.steps):
            return self.complete(player)
            
        self.current_step += 1
        print(f"Quest step completed: {self.steps[self.current_step-1][0]}")
        
        if self.current_step < len(self.steps):
            _, next_quest = self.steps[self.current_step]
            next_quest.start(player)
            print(f"New objective: {self.steps[self.current_step][0]}")
        else:
            return self.complete(player)
            
        return True