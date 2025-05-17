"""
Simplified Game Objects module for VitaGame_Hustle.
Handles interactive objects, focusing on the Computer for now.
"""
import random
from .coordinates import Coordinates # Assuming this is in VitaGame_Hustle/modules/

class GameObject:
    """Base class for all game objects that can be interacted with."""
    def __init__(self, name, description, coordinates=None, properties=None):
        self.name = name
        self.description = description
        self.coordinates = coordinates if coordinates else Coordinates(0, 0, 0)
        self.properties = properties or {}  # Custom properties
        self.id = f"obj_{name.lower().replace(' ', '_')}_{random.randint(1000,9999)}" # Unique ID
    
    def interact(self, player):
        """Base interaction method."""
        print(f"You interact with the {self.name}. Nothing specific happens.")
        return None # Return a message or None
    
    def set_property(self, key, value):
        self.properties[key] = value
    
    def get_property(self, key, default=None):
        return self.properties.get(key, default)

    def __str__(self):
        return self.name

class Computer(GameObject):
    """Computer class for interactive terminals, focused on stock market."""
    def __init__(self, name="Computer", description="A computer terminal.", coordinates=None, password=None, properties=None):
        super().__init__(name, description, coordinates, properties)
        self.password = password # Not used for now, but can be added
        self.logged_in = True # Auto-login for simplicity
        self.stock_market = {}
        self.initialize_stock_market()
        
    def initialize_stock_market(self):
        """Initialize the stock market with some default stocks."""
        self.stock_market = {
            "TECH": {"name": "BunnyTech Inc.", "price": 150.00, "volatility": 0.05, "recent_sales_value": 0.0},
            "BANK": {"name": "First National Bank", "price": 200.00, "volatility": 0.02, "recent_sales_value": 0.0},
            "MALL": {"name": "Vita Mall Corp", "price": 75.00, "volatility": 0.03, "recent_sales_value": 0.0},
            "FUEL": {"name": "Carrot Energy", "price": 85.00, "volatility": 0.06, "recent_sales_value": 0.0},
        }
        print(f"{self.name}: Stock market initialized.")
            
    def update_stock_prices(self):
        """Update stock prices based on volatility and recent sales."""
        print(f"\n--- {self.name}: Stock Market Update (Turn {self.properties.get('game_turn', 0)}) ---")
 
        for symbol, stock_data in self.stock_market.items():
            change_percent = random.uniform(-stock_data["volatility"], stock_data["volatility"])
 
            # Incorporate recent sales (positive influence)
            # This is a simple model; could be more complex (e.g., diminishing returns, scaling factor)
            if stock_data.get("recent_sales_value", 0.0) > 0:
                # Add a positive bias based on sales; 0.5% to change_percent for every $100 in sales
                sales_bonus_factor = (stock_data["recent_sales_value"] / 100.00) * 0.005
                change_percent += sales_bonus_factor
                print(f"  INFO: {symbol} sales activity (${stock_data['recent_sales_value']:.2f}) influencing price.")
            
            price_change = stock_data["price"] * change_percent # Calculate the actual price change amount
            new_price = max(1.0, stock_data["price"] + price_change) # Ensure price doesn't go below $1.00
            old_price = stock_data["price"]
            
            self.stock_market[symbol]["price"] = round(new_price, 2)
            self.stock_market[symbol]["recent_sales_value"] = 0.0 # Reset sales tracker for this turn
            
            if new_price > old_price:
                print(f"  {symbol} ({stock_data['name']}) rose to ${new_price:.2f}")
            elif new_price < old_price:
                print(f"  {symbol} ({stock_data['name']}) fell to ${new_price:.2f}")
            # If new_price == old_price, no message is printed, which is fine.

    def display_stock_prices(self):
        print("\nCurrent Stock Prices:")
        print("---------------------")
        for symbol, data in self.stock_market.items():
            print(f"  {symbol} ({data['name']}): ${data['price']:.2f}")
        print("---------------------")
            
    def buy_stocks_interface(self, player):
        self.display_stock_prices()
        print(f"\nYour current balance: ${player.money:.2f}")
        
        symbol = input("Enter stock symbol to buy (or 'cancel'): ").upper()
        if symbol.lower() == 'cancel':
            return
            
        if symbol not in self.stock_market:
            print(f"Stock symbol '{symbol}' not found.")
            return
            
        try:
            shares_str = input(f"How many shares of {symbol} do you want to buy? ")
            if shares_str.lower() == 'cancel': return
            shares = int(shares_str)

            if shares <= 0:
                print("Number of shares must be positive.")
                return
                
            price_per_share = self.stock_market[symbol]["price"]
            total_cost = shares * price_per_share
            
            if total_cost > player.money:
                print(f"You don't have enough money. Total cost: ${total_cost:.2f}, You have: ${player.money:.2f}")
                return
                
            player.buy_stock(symbol, shares, price_per_share) # Player handles own money and portfolio
            
        except ValueError:
            print("Please enter a valid number of shares.")
            
    def sell_stocks_interface(self, player):
        if not player.stock_portfolio:
            print("You don't own any stocks to sell.")
            return
            
        player.view_portfolio() # Player method to show their stocks
        self.display_stock_prices() # Show current market prices
        print(f"\nYour current balance: ${player.money:.2f}")
        
        symbol = input("Enter stock symbol to sell (or 'cancel'): ").upper()
        if symbol.lower() == 'cancel': return
            
        if symbol not in player.stock_portfolio:
            print(f"You don't own any shares of '{symbol}'.")
            return
            
        try:
            max_shares = player.stock_portfolio[symbol]["shares"]
            shares_str = input(f"How many shares of {symbol} do you want to sell? (max: {max_shares}, or 'cancel') ")
            if shares_str.lower() == 'cancel': return
            shares_to_sell = int(shares_str)
            
            if shares_to_sell <= 0:
                print("Number of shares must be positive.")
                return
                
            if shares_to_sell > max_shares:
                print(f"You only have {max_shares} shares of {symbol}.")
                return
                
            price_per_share = self.stock_market[symbol]["price"]
            player.sell_stock(symbol, shares_to_sell, price_per_share) # Player handles own money and portfolio
            
        except ValueError:
            print("Please enter a valid number of shares.")

    def interact(self, player):
        """Interact with the computer to access stock market."""
        print(f"\nYou access the {self.name}.")
        # Prices are now updated globally each turn by GameManager.
        # We can pass the game turn to the computer if it needs it for display or other logic
        # self.set_property('game_turn', player.current_area.game_manager_ref.game_turn) # Example if needed

        while True:
            print("\n=== Stock Market Terminal ===")
            print("Player Money: $", player.money) # Consider using f-string for consistency: f"${player.money:.2f}"
            print("1. View Stock Prices")
            print("2. View Your Portfolio")
            print("3. Buy Stocks")
            print("4. Sell Stocks")
            print("5. Exit Terminal")
            
            choice = input("Enter your choice (1-5): ")
            
            if choice == "1":
                self.display_stock_prices()
            elif choice == "2":
                player.view_portfolio()
            elif choice == "3":
                self.buy_stocks_interface(player)
            elif choice == "4":
                self.sell_stocks_interface(player)
            elif choice == "5":
                print("Exiting Stock Market Terminal.")
                break
            else:
                print("Invalid choice. Please try again.")
        return None # No specific message to return to game manager loop
    
    def record_sale_for_stock(self, symbol, sale_value):
        """Records a sale amount for a given stock symbol to influence next price update."""
        if symbol in self.stock_market:
            self.stock_market[symbol]["recent_sales_value"] = self.stock_market[symbol].get("recent_sales_value", 0.0) + sale_value
            print(f"Debug: Recorded ${sale_value:.2f} sales for {symbol}.") # Debug message
        else:
            print(f"Debug: Attempted to record sale for unknown stock symbol: {symbol}")

# Simplified GameObjectManager - not strictly necessary if we create objects directly
# but can be useful for consistency or future expansion.
class GameObjectManager:
    """Manages all game objects in the game (Simplified)."""
    def __init__(self):
        self.objects = {}  # object_id -> GameObject instance
        self.templates = {} # For future use: template_id -> template_data

    def add_object(self, obj):
        if obj.id in self.objects:
            print(f"Warning: GameObject with ID '{obj.id}' already exists. Overwriting.")
        self.objects[obj.id] = obj

    def get_object(self, obj_id):
        return self.objects.get(obj_id)

    # create_from_template and load/save JSON can be added later if needed
