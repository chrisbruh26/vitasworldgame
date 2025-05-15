"""
Player module for Vita Game.
Handles the player character and their interactions with the game world.
"""

from .coordinates import Coordinates

class Player:
    """Player class for the Vita game."""
    def __init__(self, name="Vita"):
        self.name = name
        self.street_cred = 0
        self.inventory = []
        self.current_area = None
        self.coordinates = Coordinates(0, 0, 0)
        self.jetpack = None
        self.is_flying = False
        self.energy = 100
        self.max_energy = 100
        self.hunger = 0
        self.max_hunger = 100
        self.money = 0
        self.skills = {}  # Dictionary of skills and their levels
        self.relationships = {}  # Relationships with NPCs
        self.properties = {}  # Custom properties
        self.current_vehicle = None  # Vehicle the player is currently in
        self.investments = {}  # Dictionary mapping business IDs to investment amounts
        self.owned_properties = {}  # Dictionary mapping area IDs to property details
        self.stock_portfolio = {}  # Dictionary mapping stock symbols to shares owned
        self.can_teleport = True  # Whether the player can teleport (enabled by default)
        
    def set_current_area(self, area, grid_x=0, grid_y=0):
        """Set the current area for the player."""
        self.current_area = area
        # Update player coordinates to match area entrance coordinates plus grid position
        self.coordinates = Coordinates(
            area.coordinates.x + grid_x,
            area.coordinates.y + grid_y,
            area.coordinates.z
        )
        print(f"You are now in {area.name}. {area.description}")
        self.look_around()
    
    def look_around(self):
        """Look around the current area."""
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        print(f"You are at position ({grid_x}, {grid_y}) in {self.current_area.name}.")
        
        # Display available directions for movement within the grid
        print("You can move:")
        if grid_y < self.current_area.grid_length - 1:
            print("- north/forward")
        if grid_y > 0:
            print("- south/backward")
        if grid_x < self.current_area.grid_width - 1:
            print("- east/right")
        if grid_x > 0:
            print("- west/left")
        
        # Display area connections (exits to other areas)
        if self.current_area.connections:
            print("Area exits:")
            for direction, area in self.current_area.connections.items():
                print(f"- {direction} to {area.name}")
        
        # Display objects at the current position
        objects_here = self.current_area.get_objects_at(grid_x, grid_y, grid_z)
        if objects_here:
            items_here = [obj for obj in objects_here if hasattr(obj, 'pickupable') and obj.pickupable]
            other_objects = [obj for obj in objects_here if not hasattr(obj, 'pickupable') or not obj.pickupable]
            
            if items_here:
                print("Items at your position (can be picked up):")
                for obj in items_here:
                    print(f"- {obj.name}: {obj.description}")
                    
            if other_objects:
                print("Objects at your position:")
                for obj in other_objects:
                    print(f"- {obj.name}: {obj.description}")
        
        # Display items in the area
        if self.current_area.items:
            print("Items in this area:")
            for item in self.current_area.items:
                # Get the relative position of the item
                item_rel_x = item.coordinates.x - self.current_area.coordinates.x
                item_rel_y = item.coordinates.y - self.current_area.coordinates.y
                # Only show items that are visible (in the same area)
                if 0 <= item_rel_x < self.current_area.grid_width and 0 <= item_rel_y < self.current_area.grid_length:
                    direction = self.get_relative_direction(grid_x, grid_y, item_rel_x, item_rel_y)
                    print(f"- {item.name}: {item.description} ({direction})")
        
        # Display NPCs in the area
        if self.current_area.npcs:
            print("People in this area:")
            for npc in self.current_area.npcs:
                # Get the relative position of the NPC
                npc_rel_x = npc.coordinates.x - self.current_area.coordinates.x
                npc_rel_y = npc.coordinates.y - self.current_area.coordinates.y
                # Only show NPCs that are visible (in the same area)
                if 0 <= npc_rel_x < self.current_area.grid_width and 0 <= npc_rel_y < self.current_area.grid_length:
                    direction = self.get_relative_direction(grid_x, grid_y, npc_rel_x, npc_rel_y)
                    print(f"- {npc.name}: {npc.description} ({direction})")
        
        # Display objects in the area
        if self.current_area.objects:
            print("Objects in this area:")
            for obj in self.current_area.objects:
                # Get the relative position of the object
                obj_rel_x = obj.coordinates.x - self.current_area.coordinates.x
                obj_rel_y = obj.coordinates.y - self.current_area.coordinates.y
                # Only show objects that are visible (in the same area)
                if 0 <= obj_rel_x < self.current_area.grid_width and 0 <= obj_rel_y < self.current_area.grid_length:
                    # Skip objects at the current position (already displayed above)
                    if obj_rel_x == grid_x and obj_rel_y == grid_y:
                        continue
                    direction = self.get_relative_direction(grid_x, grid_y, obj_rel_x, obj_rel_y)
                    print(f"- {obj.name}: {obj.description} ({direction})")
    
    def get_relative_direction(self, from_x, from_y, to_x, to_y):
        """Get the relative direction from one position to another."""
        if from_x == to_x and from_y == to_y:
            return "here"
            
        directions = []
        if to_y > from_y:
            directions.append("north")
        elif to_y < from_y:
            directions.append("south")
            
        if to_x > from_x:
            directions.append("east")
        elif to_x < from_x:
            directions.append("west")
            
        distance = int(((to_x - from_x) ** 2 + (to_y - from_y) ** 2) ** 0.5)
        if distance == 1:
            proximity = "adjacent"
        elif distance <= 3:
            proximity = "nearby"
        else:
            proximity = "in the distance"
            
        return f"{' '.join(directions)} {proximity}"

    def add_item(self, item):
        """Add an item to the player's inventory."""
        self.inventory.append(item)
        print(f"You have picked up {item.name}.")
        
        # Special handling for jetpack
        if item.__class__.__name__ == "Jetpack":
            self.jetpack = item
            print("You can now fly by activating your jetpack!")

    def remove_item(self, item_name):
        """Remove an item from the player's inventory."""
        item = next((i for i in self.inventory if i.name.lower() == item_name.lower()), None)
        if item:
            self.inventory.remove(item)
            print(f"You have dropped {item.name}.")
            
            # Special handling for jetpack
            if item.__class__.__name__ == "Jetpack" and self.jetpack == item:
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
            return False
        
        if self.jetpack.fuel <= 0:
            print("Your jetpack runs out of fuel!")
            self.is_flying = False
            return False
        
        # Consume fuel based on efficiency
        fuel_used = distance * self.jetpack.fuel_efficiency
        self.jetpack.fuel -= fuel_used
        if self.jetpack.fuel < 0:
            self.jetpack.fuel = 0
        
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        new_x, new_y, new_z = grid_x, grid_y, grid_z
        
        # Move in the specified direction
        if direction.lower() == "up":
            new_z += distance
            print(f"You fly upward to elevation {self.current_area.coordinates.z + new_z}.")
        elif direction.lower() == "down":
            if grid_z - distance < 0:
                # Don't go below ground level
                new_z = 0
                print("You descend to ground level.")
            else:
                new_z -= distance
                print(f"You fly downward to elevation {self.current_area.coordinates.z + new_z}.")
        elif direction.lower() in ["north", "forward"]:
            new_y += distance
            print(f"You fly north.")
        elif direction.lower() in ["south", "backward"]:
            new_y -= distance
            print(f"You fly south.")
        elif direction.lower() in ["east", "right"]:
            new_x += distance
            print(f"You fly east.")
        elif direction.lower() in ["west", "left"]:
            new_x -= distance
            print(f"You fly west.")
        else:
            print(f"Unknown direction: {direction}")
            return False
        
        # Check if new position is within area bounds
        if 0 <= new_x < self.current_area.grid_width and 0 <= new_y < self.current_area.grid_length:
            # Update player coordinates
            self.coordinates.x = self.current_area.coordinates.x + new_x
            self.coordinates.y = self.current_area.coordinates.y + new_y
            self.coordinates.z = self.current_area.coordinates.z + new_z
            
            # Check for objects at the new position
            objects_here = self.current_area.get_objects_at(new_x, new_y, new_z)
            if objects_here:
                print("You see:")
                for obj in objects_here:
                    print(f"- {obj.name}: {obj.description}")
                    
            return True
        else:
            # Check if there's a connection in this direction
            if direction.lower() in self.current_area.connections:
                connected_area = self.current_area.connections[direction.lower()]
                # Determine entry point on the other side
                entry_x, entry_y = 0, 0
                if direction.lower() == "north":
                    entry_y = 0  # Enter from the south side
                    entry_x = grid_x  # Keep the same x-coordinate
                elif direction.lower() == "south":
                    entry_y = connected_area.grid_length - 1  # Enter from the north side
                    entry_x = grid_x  # Keep the same x-coordinate
                elif direction.lower() == "east":
                    entry_x = 0  # Enter from the west side
                    entry_y = grid_y  # Keep the same y-coordinate
                elif direction.lower() == "west":
                    entry_x = connected_area.grid_width - 1  # Enter from the east side
                    entry_y = grid_y  # Keep the same y-coordinate
                
                # Move to the connected area
                self.set_current_area(connected_area, entry_x, entry_y)
                # Maintain flying elevation
                self.coordinates.z = connected_area.coordinates.z + grid_z
                return True
            else:
                print(f"You can't fly {direction} from here. You've reached the edge of {self.current_area.name}.")
                return False
    
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
            
    def get_grid_position(self):
        """Get the player's position relative to the current area's grid."""
        if not self.current_area:
            return None
        
        rel_x = self.coordinates.x - self.current_area.coordinates.x
        rel_y = self.coordinates.y - self.current_area.coordinates.y
        rel_z = self.coordinates.z - self.current_area.coordinates.z
        
        return (rel_x, rel_y, rel_z)
    
    def move(self, direction, distance=1):
        """Move the player in a direction within the current area's grid."""
        if not self.current_area:
            print("You're not in any area.")
            return False
            
        # If player is in a vehicle, use the vehicle's movement
        if self.current_vehicle:
            return self.current_vehicle.drive(self, direction, distance)
            
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        new_x, new_y = grid_x, grid_y
        
        # Calculate new position based on direction
        if direction.lower() in ["north", "forward"]:
            new_y += distance
        elif direction.lower() in ["south", "backward"]:
            new_y -= distance
        elif direction.lower() in ["east", "right"]:
            new_x += distance
        elif direction.lower() in ["west", "left"]:
            new_x -= distance
        else:
            print(f"Unknown direction: {direction}")
            return False
        
        # Check if new position is within area bounds
        if 0 <= new_x < self.current_area.grid_width and 0 <= new_y < self.current_area.grid_length:
            # Update player coordinates
            self.coordinates.x = self.current_area.coordinates.x + new_x
            self.coordinates.y = self.current_area.coordinates.y + new_y
            
            print(f"You move {direction}.")
            
            # Check for objects at the new position
            objects_here = self.current_area.get_objects_at(new_x, new_y, grid_z)
            if objects_here:
                print("You see:")
                for obj in objects_here:
                    print(f"- {obj.name}: {obj.description}")
                    
            return True
        else:
            # Check if there's a connection in this direction
            if direction.lower() in self.current_area.connections:
                connected_area = self.current_area.connections[direction.lower()]
                # Determine entry point on the other side
                entry_x, entry_y = 0, 0
                if direction.lower() == "north":
                    entry_y = 0  # Enter from the south side
                    entry_x = grid_x  # Keep the same x-coordinate
                elif direction.lower() == "south":
                    entry_y = connected_area.grid_length - 1  # Enter from the north side
                    entry_x = grid_x  # Keep the same x-coordinate
                elif direction.lower() == "east":
                    entry_x = 0  # Enter from the west side
                    entry_y = grid_y  # Keep the same y-coordinate
                elif direction.lower() == "west":
                    entry_x = connected_area.grid_width - 1  # Enter from the east side
                    entry_y = grid_y  # Keep the same y-coordinate
                
                # Move to the connected area
                self.set_current_area(connected_area, entry_x, entry_y)
                return True
            else:
                print(f"You can't go {direction} from here. You've reached the edge of {self.current_area.name}.")
                return False
    
    def interact_with(self, object_name):
        """Interact with an object in the current area."""
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        
        # Check for objects at the current position
        objects_here = self.current_area.get_objects_at(grid_x, grid_y, grid_z)
        obj = next((o for o in objects_here if o.name.lower() == object_name.lower()), None)
        
        if obj:
            obj.interact(self)
        else:
            # Check for objects in adjacent positions
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue  # Skip current position (already checked)
                    
                    check_x, check_y = grid_x + dx, grid_y + dy
                    if 0 <= check_x < self.current_area.grid_width and 0 <= check_y < self.current_area.grid_length:
                        objects_nearby = self.current_area.get_objects_at(check_x, check_y, grid_z)
                        obj = next((o for o in objects_nearby if o.name.lower() == object_name.lower()), None)
                        if obj:
                            print(f"You move closer to the {obj.name}.")
                            obj.interact(self)
                            return
            
            print(f"You don't see a {object_name} nearby.")
    
    def talk_to(self, npc_name):
        """Talk to an NPC in the current area."""
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        
        # Find the NPC in the current area
        npc = next((n for n in self.current_area.npcs if n.name.lower() == npc_name.lower()), None)
        
        if npc:
            # Check if the NPC is nearby
            npc_rel_x = npc.coordinates.x - self.current_area.coordinates.x
            npc_rel_y = npc.coordinates.y - self.current_area.coordinates.y
            
            # Calculate distance
            distance = ((grid_x - npc_rel_x) ** 2 + (grid_y - npc_rel_y) ** 2) ** 0.5
            
            if distance <= 1.5:  # Close enough to talk
                npc.talk(self)
            else:
                print(f"{npc.name} is too far away. Move closer to talk.")
        else:
            print(f"You don't see {npc_name} here.")
    
    def pick_up(self, item_name):
        """Pick up an item from the current area."""
        # Get current grid position
        grid_x, grid_y, grid_z = self.get_grid_position()
        
        # Normalize the item name for case-insensitive comparison
        normalized_item_name = item_name.lower()
        
        # First check if the item is at the player's current position
        objects_here = self.current_area.get_objects_at(grid_x, grid_y, grid_z)
        item_at_position = None
        
        for obj in objects_here:
            if hasattr(obj, 'pickupable') and obj.pickupable and normalized_item_name in obj.name.lower():
                item_at_position = obj
                break
        
        if item_at_position:
            # Item is at player's position, pick it up
            if item_at_position in self.current_area.items:
                self.current_area.remove_item(item_at_position.name)
            # Also remove from grid_objects
            self.current_area.remove_object_from_grid(item_at_position, grid_x, grid_y, grid_z)
            self.add_item(item_at_position)
            return
        
        # If not at position, look in the area
        item = None
        for i in self.current_area.items:
            if normalized_item_name in i.name.lower():
                item = i
                break
        
        if item:
            # Check if the item is nearby
            item_rel_x = item.coordinates.x - self.current_area.coordinates.x
            item_rel_y = item.coordinates.y - self.current_area.coordinates.y
            
            # Calculate distance
            distance = ((grid_x - item_rel_x) ** 2 + (grid_y - item_rel_y) ** 2) ** 0.5
            
            if distance <= 1.5:  # Close enough to pick up
                if item.pickupable:
                    self.current_area.remove_item(item.name)
                    # Also remove from grid_objects
                    self.current_area.remove_object_from_grid(item, item_rel_x, item_rel_y, 0)
                    self.add_item(item)
                else:
                    print(f"You can't pick up the {item.name}.")
            else:
                print(f"The {item.name} is too far away. Move closer to pick it up.")
                # Show direction to the item
                direction = self.get_relative_direction(grid_x, grid_y, item_rel_x, item_rel_y)
                print(f"It's {direction}.")
        else:
            # Check for items at the player's position again with a more detailed message
            pickupable_items_here = [obj for obj in objects_here if hasattr(obj, 'pickupable') and obj.pickupable]
            if pickupable_items_here:
                print(f"You don't see '{item_name}' here. Items at your position that you can pick up:")
                for obj in pickupable_items_here:
                    print(f"- {obj.name}")
            else:
                # List available items in the area to help the player
                available_items = [i.name for i in self.current_area.items]
                if available_items:
                    print(f"You don't see '{item_name}' here. Available items in this area:")
                    for name in available_items:
                        print(f"- {name}")
                else:
                    print(f"You don't see '{item_name}' here. There are no items in this area.")
    
    def drop(self, item_name):
        """Drop an item from inventory."""
        self.remove_item(item_name)
    
    def use(self, item_name):
        """Use an item from inventory."""
        item = next((i for i in self.inventory if i.name.lower() == item_name.lower()), None)
        if item:
            item.use(self)
        else:
            print(f"You don't have {item_name} to use.")
    
    def craft(self, recipe_name, crafting_system):
        """Craft an item using the crafting system."""
        crafting_system.craft_item(recipe_name, self)
    
    def invest(self, business_id, amount):
        """Invest money in a business."""
        if self.money < amount:
            print(f"You don't have enough money. You need ${amount}.")
            return False
        
        self.money -= amount
        if business_id in self.investments:
            self.investments[business_id] += amount
        else:
            self.investments[business_id] = amount
        
        print(f"You invested ${amount} in the business.")
        return True
    
    def check_investments(self):
        """Check the status of investments."""
        if not self.investments:
            print("You don't have any investments.")
            return
        
        print("Your investments:")
        for business_id, amount in self.investments.items():
            print(f"- {business_id}: ${amount}")
    
    def sell_investment(self, business_id, amount=None):
        """Sell an investment in a business."""
        if business_id not in self.investments:
            print(f"You don't have an investment in {business_id}.")
            return False
        
        if amount is None or amount >= self.investments[business_id]:
            amount = self.investments[business_id]
            del self.investments[business_id]
        else:
            self.investments[business_id] -= amount
        
        # In a real game, the return would be calculated based on the business's performance
        return_multiplier = 1.1  # 10% return (placeholder)
        return_amount = amount * return_multiplier
        
        self.money += return_amount
        print(f"You sold your investment for ${return_amount}.")
        return True
    
    def set_relationship(self, entity, value):
        """Set relationship value with another entity (NPC)."""
        self.relationships[entity.name] = value
    
    def adjust_relationship(self, entity, amount):
        """Adjust relationship value with another entity."""
        current = self.get_relationship(entity)
        self.relationships[entity.name] = max(-100, min(100, current + amount))
        
    def get_relationship(self, entity):
        """Get relationship value with another entity."""
        return self.relationships.get(entity.name, 0)
    
    def set_property(self, key, value):
        """Set a custom property for the player."""
        self.properties[key] = value
    
    def get_property(self, key, default=None):
        """Get a custom property for the player."""
        return self.properties.get(key, default)
    
    def buy_property(self, area):
        """Buy a property (area) if it's purchasable."""
        if not area:
            print("Invalid property.")
            return False
            
        # Check if the area is purchasable
        if not area.get_property("purchasable", False):
            print(f"{area.name} is not for sale.")
            return False
            
        # Check if the player already owns this property
        if area.id in self.owned_properties:
            print(f"You already own {area.name}.")
            return False
            
        # Get the purchase price
        purchase_price = area.get_property("purchase_price", 0)
        
        # Check if the player has enough money
        if self.money < purchase_price:
            print(f"You don't have enough money to buy {area.name}. It costs ${purchase_price}.")
            return False
            
        # Purchase the property
        self.money -= purchase_price
        
        # Add to owned properties
        self.owned_properties[area.id] = {
            "name": area.name,
            "purchase_price": purchase_price,
            "purchase_date": "current_date",  # This would be replaced with actual game date
            "rental_income": area.get_property("rental_income", 0),
            "business_income": area.get_property("business_income", 0)
        }
        
        print(f"Congratulations! You now own {area.name}.")
        return True
        
    def sell_property(self, area_id):
        """Sell a property that the player owns."""
        if area_id not in self.owned_properties:
            print(f"You don't own this property.")
            return False
            
        property_data = self.owned_properties[area_id]
        
        # Calculate selling price (could be different from purchase price based on game mechanics)
        selling_price = property_data["purchase_price"]  # Simple implementation
        
        # Sell the property
        self.money += selling_price
        
        # Remove from owned properties
        del self.owned_properties[area_id]
        
        print(f"You have sold {property_data['name']} for ${selling_price}.")
        return True
        
    def collect_property_income(self):
        """Collect income from all owned properties."""
        total_income = 0
        
        for area_id, property_data in self.owned_properties.items():
            rental_income = property_data.get("rental_income", 0)
            business_income = property_data.get("business_income", 0)
            
            total_income += rental_income + business_income
            
        if total_income > 0:
            self.money += total_income
            print(f"You've collected ${total_income} in income from your properties.")
        else:
            print("You don't have any income-generating properties.")
            
        return total_income
        
    def buy_stock(self, stock_symbol, shares, price_per_share):
        """Buy shares of a company's stock."""
        total_cost = shares * price_per_share
        
        # Check if player has enough money
        if self.money < total_cost:
            print(f"You don't have enough money to buy {shares} shares of {stock_symbol} at ${price_per_share} per share.")
            return False
            
        # Deduct money
        self.money -= total_cost
        
        # Add to portfolio
        if stock_symbol in self.stock_portfolio:
            # Calculate new average price
            current_shares = self.stock_portfolio[stock_symbol]["shares"]
            current_price = self.stock_portfolio[stock_symbol]["price_per_share"]
            
            total_shares = current_shares + shares
            total_investment = (current_shares * current_price) + total_cost
            new_average_price = total_investment / total_shares
            
            self.stock_portfolio[stock_symbol] = {
                "shares": total_shares,
                "price_per_share": new_average_price
            }
        else:
            self.stock_portfolio[stock_symbol] = {
                "shares": shares,
                "price_per_share": price_per_share
            }
            
        print(f"You've purchased {shares} shares of {stock_symbol} at ${price_per_share} per share.")
        return True
        
    def sell_stock(self, stock_symbol, shares, price_per_share):
        """Sell shares of a company's stock."""
        if stock_symbol not in self.stock_portfolio:
            print(f"You don't own any shares of {stock_symbol}.")
            return False
            
        if shares > self.stock_portfolio[stock_symbol]["shares"]:
            print(f"You only have {self.stock_portfolio[stock_symbol]['shares']} shares of {stock_symbol}.")
            return False
            
        # Calculate proceeds
        proceeds = shares * price_per_share
        
        # Add money
        self.money += proceeds
        
        # Update portfolio
        remaining_shares = self.stock_portfolio[stock_symbol]["shares"] - shares
        if remaining_shares == 0:
            del self.stock_portfolio[stock_symbol]
        else:
            self.stock_portfolio[stock_symbol]["shares"] = remaining_shares
            
        print(f"You've sold {shares} shares of {stock_symbol} at ${price_per_share} per share for a total of ${proceeds}.")
        return True
        
    def view_portfolio(self):
        """View the player's stock portfolio."""
        if not self.stock_portfolio:
            print("You don't own any stocks.")
            return
            
        print("Your Stock Portfolio:")
        print("---------------------")
        for symbol, data in self.stock_portfolio.items():
            print(f"{symbol}: {data['shares']} shares at ${data['price_per_share']:.2f} per share")
            
    def view_properties(self):
        """View the player's property portfolio."""
        if not self.owned_properties:
            print("You don't own any properties.")
            return
            
        print("Your Property Portfolio:")
        print("-----------------------")
        for area_id, property_data in self.owned_properties.items():
            print(f"{property_data['name']}:")
            print(f"  Purchase Price: ${property_data['purchase_price']}")
            if property_data.get("rental_income", 0) > 0:
                print(f"  Rental Income: ${property_data['rental_income']} per day")
            if property_data.get("business_income", 0) > 0:
                print(f"  Business Income: ${property_data['business_income']} per day")
            print()
    
    def teleport(self, area_name, area_manager):
        """Teleport to a named area.
        
        Args:
            area_name (str): The name of the area to teleport to
            area_manager (AreaManager): The game's area manager to find areas
            
        Returns:
            bool: True if teleportation was successful, False otherwise
        """
        if not self.can_teleport:
            print("You don't have teleportation abilities!")
            return False
            
        area_name_lower = area_name.lower()
        
        # First try exact match (case-insensitive)
        target_area = None
        for area in area_manager.areas.values():
            if area.name.lower() == area_name_lower:
                target_area = area
                break
        
        # If no exact match, try partial match
        if not target_area:
            matching_areas = []
            for area in area_manager.areas.values():
                if area_name_lower in area.name.lower() or area_name_lower in area.id.lower():
                    matching_areas.append(area)
            
            # If we found exactly one match, use it
            if len(matching_areas) == 1:
                target_area = matching_areas[0]
            # If we found multiple matches, let the player choose
            elif len(matching_areas) > 1:
                print(f"Multiple areas match '{area_name}'. Please choose one:")
                for i, area in enumerate(matching_areas, 1):
                    print(f"{i}. {area.name}")
                
                choice = input("Enter number (or 'cancel'): ")
                if choice.lower() == 'cancel':
                    return False
                
                try:
                    index = int(choice) - 1
                    if 0 <= index < len(matching_areas):
                        target_area = matching_areas[index]
                    else:
                        print("Invalid choice.")
                        return False
                except ValueError:
                    print("Please enter a number.")
                    return False
                
        if not target_area:
            print(f"Unknown area: {area_name}")
            return False
            
        # Teleport to the area
        print(f"*ZAP* You teleport to {target_area.name}!")
        self.set_current_area(target_area)
        return True
        
    def to_dict(self):
        """Convert player to dictionary for serialization."""
        return {
            "name": self.name,
            "street_cred": self.street_cred,
            "coordinates": self.coordinates.to_dict(),
            "energy": self.energy,
            "max_energy": self.max_energy,
            "hunger": self.hunger,
            "max_hunger": self.max_hunger,
            "money": self.money,
            "skills": self.skills,
            "relationships": self.relationships,
            "properties": self.properties,
            "investments": self.investments,
            "owned_properties": self.owned_properties,
            "stock_portfolio": self.stock_portfolio,
            "inventory": [item.id for item in self.inventory],
            "current_area": self.current_area.id if self.current_area else None,
            "jetpack": self.jetpack.id if self.jetpack else None,
            "is_flying": self.is_flying,
            "current_vehicle": self.current_vehicle.id if self.current_vehicle else None,
            "can_teleport": self.can_teleport
        }
    
    @classmethod
    def from_dict(cls, data, area_resolver=None, item_resolver=None, object_resolver=None):
        """Create player from dictionary."""
        player = cls(data["name"])
        player.street_cred = data["street_cred"]
        player.coordinates = Coordinates.from_dict(data["coordinates"])
        player.energy = data["energy"]
        player.max_energy = data["max_energy"]
        player.hunger = data["hunger"]
        player.max_hunger = data["max_hunger"]
        player.money = data["money"]
        player.skills = data["skills"]
        player.relationships = data["relationships"]
        player.properties = data["properties"]
        player.investments = data["investments"]
        player.owned_properties = data.get("owned_properties", {})
        player.stock_portfolio = data.get("stock_portfolio", {})
        player.is_flying = data["is_flying"]
        player.can_teleport = data.get("can_teleport", True)  # Default to True if not present
        
        # Resolve current area if area_resolver is provided
        if area_resolver and data.get("current_area"):
            player.current_area = area_resolver(data["current_area"])
        
        # Resolve inventory if item_resolver is provided
        if item_resolver:
            for item_id in data.get("inventory", []):
                item = item_resolver(item_id)
                if item:
                    player.inventory.append(item)
                    # Check if this is the jetpack
                    if data.get("jetpack") == item_id:
                        player.jetpack = item
        
        # Resolve current vehicle if object_resolver is provided
        if object_resolver and data.get("current_vehicle"):
            player.current_vehicle = object_resolver(data["current_vehicle"])
        
        return player