"""
Player module for the game.
Handles the player character and their interactions with the game world.
"""

from .coordinates import Coordinates
from .item import Item
from .npc import NPC # Moved import here

class Player:
    """Player class for the game."""
    def __init__(self, name="Vita", start_money=100):
        self.name = name
        self.inventory = []
        self.current_area = None
        self.coordinates = Coordinates(0, 0, 0) # Global coordinates
        self.money = start_money
        self.stock_portfolio = {} # symbol -> {'shares': int, 'avg_price': float}

    def set_current_area(self, area, grid_x=None, grid_y=None):
        """Set the current area for the player and position them on its grid."""
        self.current_area = area
        if area:
            if grid_x is None:
                grid_x = area.grid_width // 2
            if grid_y is None:
                grid_y = area.grid_length // 2
            
            # Ensure player is within bounds
            grid_x = max(0, min(grid_x, area.grid_width - 1))
            grid_y = max(0, min(grid_y, area.grid_length - 1))

            self.coordinates = area.get_global_coordinates(grid_x, grid_y)
            print(f"You are now in {area.name}. {area.description}")
            self.look_around()
        else:
            print("Error: Tried to move to a null area.")

    def get_grid_position(self):
        """Get the player's position relative to the current area's grid."""
        if not self.current_area:
            return None, None
        rel_coords = self.current_area.get_relative_coordinates(self.coordinates)
        return int(rel_coords[0]), int(rel_coords[1])

    def look_around(self):
        """Look around the current area."""
        if not self.current_area:
            print("You are floating in the void...")
            return

        grid_x, grid_y = self.get_grid_position()
        print(f"\n--- {self.current_area.name} ---")
        print(self.current_area.description)
        print(f"You are at grid position ({grid_x}, {grid_y}).")

        # Display items at current position
        objects_here = self.current_area.get_objects_at_grid_cell(grid_x, grid_y)
        items_here = [obj for obj in objects_here if isinstance(obj, Item)]
        if items_here:
            print("Items at your feet:")
            for item in items_here:
                print(f"  - {item.name}: {item.description}")
        
        other_game_objects_here = [obj for obj in objects_here if not isinstance(obj, Item) and not isinstance(obj, NPC)]
        if other_game_objects_here:
            print("Objects here:")
            for obj in other_game_objects_here: # Corrected to iterate over other_game_objects_here
                print(f"  - {obj.name}: {obj.description}")
        
        # Display NPCs at current position
        npcs_here = [obj for obj in objects_here if isinstance(obj, NPC)] # NPC is now known
        if npcs_here:
            print("People here:")
            for npc in npcs_here:
                print(f"  - {npc.name}")

        # Display other items and NPCs in the area (simplified for now)
        # This could be expanded to show relative directions
        if self.current_area.items:
            print("Other items in the area:")
            for item in self.current_area.items:
                if item not in items_here: # Don't list items at feet again
                    item_gx, item_gy = self.current_area.get_relative_coordinates(item.coordinates)[:2]
                    print(f"  - {item.name} at ({int(item_gx)}, {int(item_gy)})")

        if self.current_area.npcs:
            print("Other people in the area:")
            for npc in self.current_area.npcs:
                if npc not in npcs_here:
                    npc_gx, npc_gy = self.current_area.get_relative_coordinates(npc.coordinates)[:2]
                    print(f"  - {npc.name} at ({int(npc_gx)}, {int(npc_gy)})")

        # Display area connections
        if self.current_area.connections:
            print("Exits:")
            for direction, area in self.current_area.connections.items():
                print(f"  - {direction.capitalize()}: to {area.name}")
        print("---")

        # Display items for sale if this area is a shop
        if hasattr(self.current_area, 'shop_stock') and self.current_area.shop_stock:
            print("Items for sale here:")
            for line in self.current_area.get_shop_listing():
                print(f"  {line}")

    def move(self, direction):
        """Move the player one step in a direction or through a connection."""
        if not self.current_area:
            print("You can't move, you're not in any area.")
            return

        grid_x, grid_y = self.get_grid_position()
        new_grid_x, new_grid_y = grid_x, grid_y

        if direction == "north": new_grid_y += 1
        elif direction == "south": new_grid_y -= 1
        elif direction == "east": new_grid_x += 1
        elif direction == "west": new_grid_x -= 1
        else: # Check for area connection by direction name
            if direction in self.current_area.connections:
                self.set_current_area(self.current_area.connections[direction])
                return
            print(f"Unknown direction: {direction}. Try north, south, east, west, or an exit name.")
            return

        if self.current_area.is_valid_grid_position(new_grid_x, new_grid_y):
            self.coordinates = self.current_area.get_global_coordinates(new_grid_x, new_grid_y)
            print(f"You move {direction}.")
            self.look_around() # Show what's at the new position
        elif direction in self.current_area.connections: # Edge of grid, try to use connection
             self.set_current_area(self.current_area.connections[direction])
        else:
            print("You can't go that way.")

    def teleport(self, target_area, grid_x=None, grid_y=None):
        """Teleport to a specific area, optionally to specific grid coordinates."""
        if not target_area:
            print("Teleport target area not found.")
            return
        self.set_current_area(target_area, grid_x, grid_y)
        print(f"You teleport to {target_area.name}.")

    def add_item(self, item):
        """Add an item to the player's inventory."""
        self.inventory.append(item)
        item.coordinates = None # Item is no longer in the world
        print(f"You picked up {item.name}.")

    def remove_item(self, item_name):
        """Remove an item from inventory and drop it in the current area."""
        item_to_drop = None
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                item_to_drop = item
                break
        
        if item_to_drop:
            self.inventory.remove(item_to_drop)
            print(f"You dropped {item_to_drop.name}.")
            if self.current_area:
                player_gx, player_gy = self.get_grid_position()
                self.current_area.add_object_to_grid(item_to_drop, player_gx, player_gy)
        else:
            print(f"You don't have '{item_name}' in your inventory.")

    def pick_up(self, item_name):
        """Pick up an item from the current area."""
        if not self.current_area:
            print("You are not in an area to pick up items from.")
            return

        player_gx, player_gy = self.get_grid_position()
        objects_at_player = self.current_area.get_objects_at_grid_cell(player_gx, player_gy)
        
        item_to_pickup = None
        for obj in objects_at_player:
            if isinstance(obj, Item) and obj.name.lower() == item_name.lower():
                if obj.pickupable:
                    item_to_pickup = obj
                    break
                else:
                    print(f"You can't pick up {obj.name}.")
                    return
        
        if item_to_pickup:
            self.current_area.remove_object_from_grid(item_to_pickup, player_gx, player_gy)
            self.add_item(item_to_pickup)
        else:
            print(f"You don't see '{item_name}' here to pick up.")

    def show_inventory(self):
        if not self.inventory:
            print("Your inventory is empty.")
        else:
            print("\nInventory:")
            for item in self.inventory:
                print(f"  - {item.name}")
        print(f"Money: ${self.money}")

    def buy_item(self, item_name_query):
        """Attempt to buy an item from the current area's shop."""
        if not self.current_area:
            print("You are not in any area to buy from.")
            return
        if not hasattr(self.current_area, 'shop_stock') or not self.current_area.shop_stock:
            print("This place doesn't seem to be selling anything.")
            return

        item_instance, price = self.current_area.process_purchase(item_name_query, self.money)

        if item_instance:
            self.money -= price
            self.add_item(item_instance) # add_item already prints a message
            print(f"You paid ${price:.2f}. Your money: ${self.money:.2f}")
        else:
            # More specific feedback could come from process_purchase if we enhance it
            # For now, a general failure message.
            details = self.current_area.shop_stock.get(item_name_query.lower())
            if not details: print(f"The shop doesn't have '{item_name_query}'.")
            elif details['stock'] <= 0: print(f"'{item_name_query}' is out of stock.")
            elif self.money < details['price']: print(f"You can't afford '{item_name_query}'. It costs ${details['price']:.2f}, you have ${self.money:.2f}.")

    def view_portfolio(self):
        if not self.stock_portfolio:
            print("Your stock portfolio is empty.")
            return
        print("\n--- Your Stock Portfolio ---")
        # In a real scenario, you'd want to fetch current prices from the Computer/StockMarket
        # to calculate current total value. For now, just display holdings.
        for symbol, data in self.stock_portfolio.items():
            print(f"  {symbol}: {data['shares']} shares, Avg. Buy Price: ${data['avg_price']:.2f}")
        print("--------------------------")

    def buy_stock(self, symbol, shares, price_per_share):
        # Money check should ideally happen before calling this, or here.
        # For now, assuming Computer interface checks affordability.
        
        self.money -= shares * price_per_share # Deduct money
        if symbol in self.stock_portfolio:
            current_shares = self.stock_portfolio[symbol]['shares']
            current_avg_price = self.stock_portfolio[symbol]['avg_price']
            total_cost_old = current_shares * current_avg_price
            total_cost_new_batch = shares * price_per_share
            
            new_total_shares = current_shares + shares
            new_avg_price = (total_cost_old + total_cost_new_batch) / new_total_shares
            
            self.stock_portfolio[symbol]['shares'] = new_total_shares
            self.stock_portfolio[symbol]['avg_price'] = new_avg_price
        else:
            self.stock_portfolio[symbol] = {'shares': shares, 'avg_price': price_per_share}
        print(f"Successfully bought {shares} shares of {symbol} at ${price_per_share:.2f} each.")
        print(f"Remaining money: ${self.money:.2f}")
        return True

    def sell_stock(self, symbol, shares_to_sell, price_per_share):
        # Affordability/ownership check should happen before calling this.

        self.money += shares_to_sell * price_per_share # Add money
        
        avg_buy_price = self.stock_portfolio[symbol]['avg_price']
        profit_loss_per_share = price_per_share - avg_buy_price
        total_profit_loss = profit_loss_per_share * shares_to_sell
        
        self.stock_portfolio[symbol]['shares'] -= shares_to_sell
        if self.stock_portfolio[symbol]['shares'] == 0:
            del self.stock_portfolio[symbol]
            
        print(f"Successfully sold {shares_to_sell} shares of {symbol} at ${price_per_share:.2f} each.")
        print(f"Profit/Loss for this transaction: ${total_profit_loss:.2f}")
        print(f"Remaining money: ${self.money:.2f}")
        return True