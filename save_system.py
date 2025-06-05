"""
Save/Load System for Vita Game Hustle.
Handles saving and loading game state to/from files.
"""
import os
import json
import time
from datetime import datetime

class SaveSystem:
    """Handles saving and loading game state."""
    
    def __init__(self, game_manager):
        """Initialize the save system with a reference to the game manager."""
        self.game_manager = game_manager
        self.save_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'saves')
        
        # Create saves directory if it doesn't exist
        os.makedirs(self.save_directory, exist_ok=True)
        
    def _serialize_dict(self, dictionary):
        """
        Helper method to serialize dictionaries with non-string keys.
        Converts all keys to strings for JSON compatibility.
        
        Args:
            dictionary (dict): Dictionary to serialize
            
        Returns:
            dict: Serialized dictionary with string keys
        """
        if not isinstance(dictionary, dict):
            return {}
            
        serialized = {}
        for key, value in dictionary.items():
            # Convert key to string
            str_key = str(key)
            
            # Handle nested dictionaries
            if isinstance(value, dict):
                serialized[str_key] = self._serialize_dict(value)
            else:
                serialized[str_key] = value
                
        return serialized
        
    def _deserialize_dict(self, serialized_dict):
        """
        Helper method to deserialize dictionaries.
        
        Args:
            serialized_dict (dict): Serialized dictionary
            
        Returns:
            dict: Deserialized dictionary
        """
        if not isinstance(serialized_dict, dict):
            return {}
            
        deserialized = {}
        for key, value in serialized_dict.items():
            # Try to convert numeric keys back to integers
            try:
                if key.isdigit():
                    key = int(key)
                elif key.replace('.', '', 1).isdigit() and key.count('.') == 1:
                    key = float(key)
            except (ValueError, AttributeError):
                pass  # Keep key as string if conversion fails
                
            # Handle nested dictionaries
            if isinstance(value, dict):
                deserialized[key] = self._deserialize_dict(value)
            else:
                deserialized[key] = value
                
        return deserialized
    
    def save_game(self, save_name=None):
        """
        Save the current game state to a file.
        
        Args:
            save_name (str, optional): Name for the save file. If None, a timestamp will be used.
        
        Returns:
            str: Path to the save file or None if save failed
        """
        try:
            # Generate save name if not provided
            if not save_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_name = f"vita_save_{timestamp}"
            
            # Ensure save name has .json extension
            if not save_name.endswith('.json'):
                save_name += '.json'
            
            save_path = os.path.join(self.save_directory, save_name)
            
            # Create the save data dictionary
            save_data = {
                'version': '1.0',
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'game_turn': self.game_manager.game_turn,
                'player': self._serialize_player(),
                'areas': self._serialize_areas(),
                'npcs': self._serialize_npcs(),
                'items': self._serialize_items(),
                'computers': self._serialize_computers()
            }
            
            # Write save data to file
            with open(save_path, 'w') as save_file:
                json.dump(save_data, save_file, indent=2)
            
            return save_path
        
        except Exception as e:
            print(f"Error saving game: {str(e)}")
            return None
    
    def load_game(self, save_name):
        """
        Load a game state from a file.
        
        Args:
            save_name (str): Name of the save file to load.
        
        Returns:
            bool: True if load was successful, False otherwise
        """
        try:
            # Ensure save name has .json extension
            if not save_name.endswith('.json'):
                save_name += '.json'
            
            save_path = os.path.join(self.save_directory, save_name)
            
            # Check if save file exists
            if not os.path.exists(save_path):
                print(f"Save file '{save_name}' not found.")
                return False
            
            # Load save data from file
            try:
                with open(save_path, 'r') as save_file:
                    save_data = json.load(save_file)
            except json.JSONDecodeError as e:
                print(f"Error: Save file is corrupted or not in valid JSON format: {str(e)}")
                return False
            
            # Reset current game state
            self._reset_game_state()
            
            # Load game turn
            self.game_manager.game_turn = save_data.get('game_turn', 0)
            
            # Load areas first (needed for other objects)
            self._deserialize_areas(save_data.get('areas', []))
            
            # Load items (before NPCs and player who might have them in inventory)
            self._deserialize_items(save_data.get('items', []))
            
            # Load NPCs
            self._deserialize_npcs(save_data.get('npcs', []))
            
            # Load player (after areas and items)
            self._deserialize_player(save_data.get('player', {}))
            
            # Load computers
            self._deserialize_computers(save_data.get('computers', []))
            
            return True
        
        except Exception as e:
            print(f"Error loading game: {str(e)}")
            return False
    
    def list_saves(self):
        """
        List all available save files.
        
        Returns:
            list: List of save file names
        """
        try:
            saves = [f for f in os.listdir(self.save_directory) if f.endswith('.json')]
            return sorted(saves, reverse=True)  # Most recent first
        except Exception as e:
            print(f"Error listing saves: {str(e)}")
            return []
    
    def _reset_game_state(self):
        """Reset the current game state before loading a save."""
        # Clear areas
        self.game_manager.area_manager.areas = {}
        
        # Clear NPCs
        self.game_manager.npc_manager.npcs = []
        
        # Clear items
        self.game_manager.item_manager.items_master_list = {}
        
        # Clear computers
        self.game_manager.computers = []
    
    def _serialize_player(self):
        """Serialize player data to a dictionary."""
        try:
            player = self.game_manager.player
            
            # Get current area and position
            current_area_name = None
            grid_x, grid_y = None, None
            
            if hasattr(player, 'current_area') and player.current_area:
                if hasattr(player.current_area, 'name'):
                    current_area_name = player.current_area.name
                    
                if hasattr(player, 'get_grid_position'):
                    try:
                        grid_x, grid_y = player.get_grid_position()
                    except Exception as e:
                        print(f"Warning: Could not get player grid position: {str(e)}")
            
            # Serialize inventory items
            inventory = []
            if hasattr(player, 'inventory'):
                for item in player.inventory:
                    if hasattr(item, 'name') and hasattr(item, 'description') and hasattr(item, 'value'):
                        inventory.append({
                            'name': item.name,
                            'description': item.description,
                            'value': item.value
                        })
                    else:
                        print(f"Warning: Player has invalid item in inventory")
            
            return {
                'name': getattr(player, 'name', 'Vita'),
                'money': getattr(player, 'money', 500),
                'current_area': current_area_name,
                'grid_position': [grid_x, grid_y] if grid_x is not None and grid_y is not None else None,
                'inventory': inventory,
                'stock_portfolio': getattr(player, 'stock_portfolio', {}),
                'properties_portfolio': getattr(player, 'properties_portfolio', {})
            }
        except Exception as e:
            print(f"Error serializing player: {str(e)}")
            # Return minimal valid player data
            return {
                'name': 'Vita',
                'money': 500,
                'current_area': None,
                'grid_position': None,
                'inventory': [],
                'stock_portfolio': {},
                'properties_portfolio': {}
            }
    
    def _serialize_areas(self):
        """Serialize all areas to a list of dictionaries."""
        areas = []
        
        for area_id, area in self.game_manager.area_manager.areas.items():
            # Serialize connections
            connections = {}
            for direction, connected_area in area.connections.items():
                # Make sure connected_area is an object with a name attribute
                if hasattr(connected_area, 'name'):
                    connections[direction] = connected_area.name
                else:
                    print(f"Warning: Connected area in direction {direction} is not a valid area object")
            
            # Serialize shop stock if applicable
            shop_stock = None
            if hasattr(area, 'shop_stock') and area.shop_stock:
                shop_stock = []
                for item_key, item_data in area.shop_stock.items():
                    # Make sure item_data has the expected structure
                    if isinstance(item_data, dict) and 'prototype' in item_data and hasattr(item_data['prototype'], 'name'):
                        shop_stock.append({
                            'item_key': item_key,
                            'name': item_data['prototype'].name,
                            'description': item_data['prototype'].description,
                            'value': item_data['prototype'].value,
                            'price': item_data['price'],
                            'quantity': "infinite" if item_data['stock'] == float('inf') else item_data['stock']
                        })
                    else:
                        print(f"Warning: Shop stock item {item_key} has invalid structure")
            
            # Create area data
            area_data = {
                'id': area.id,
                'name': area.name,
                'description': area.description,
                'origin_coords': [area.area_origin_coords.x, area.area_origin_coords.y, area.area_origin_coords.z],
                'grid_width': area.grid_width,
                'grid_length': area.grid_length,
                'connections': connections,
                'shop_stock': shop_stock,
                'associated_stock_symbol': getattr(area, 'associated_stock_symbol', None),
                'is_shelter': getattr(area, 'is_shelter', False)
            }
            
            areas.append(area_data)
        
        return areas
    
    def _serialize_npcs(self):
        """Serialize all NPCs to a list of dictionaries."""
        npcs = []
        
        # Debug the NPC manager
        if not hasattr(self.game_manager, 'npc_manager'):
            print("Warning: Game manager has no npc_manager attribute")
            return npcs
            
        if not hasattr(self.game_manager.npc_manager, 'npcs'):
            print("Warning: NPC manager has no npcs attribute")
            return npcs
            
        print(f"Debug: Found {len(self.game_manager.npc_manager.npcs)} NPCs to serialize")
        
        # Correctly iterate through the dictionary of NPCs
        for i, (npc_id, npc) in enumerate(self.game_manager.npc_manager.npcs.items()):
            try:
                # Skip if npc is not a proper object
                if not hasattr(npc, 'name') or not hasattr(npc, 'description'):
                    print(f"Warning: Skipping invalid NPC object with ID {npc_id}")
                    continue
                
                print(f"Debug: Serializing NPC: {npc.name}")
                
                # Get current area and position
                current_area_name = None
                grid_x, grid_y = None, None
                
                if hasattr(npc, 'location') and npc.location:
                    # Make sure location is an object with a name attribute
                    if hasattr(npc.location, 'name'):
                        current_area_name = npc.location.name
                        if hasattr(npc, 'coordinates') and hasattr(npc.location, 'get_relative_coordinates'):
                            try:
                                grid_x, grid_y = npc.location.get_relative_coordinates(npc.coordinates)[:2]
                            except Exception as e:
                                print(f"Warning: Could not get grid position for NPC {npc.name}: {str(e)}")
                    else:
                        print(f"Warning: NPC {npc.name} has invalid location object")
                
                # Serialize inventory items
                inventory = []
                if hasattr(npc, 'inventory'):
                    for item in npc.inventory:
                        if hasattr(item, 'name') and hasattr(item, 'description') and hasattr(item, 'value'):
                            inventory.append({
                                'name': item.name,
                                'description': item.description,
                                'value': item.value
                            })
                        else:
                            print(f"Warning: NPC {npc.name} has invalid item in inventory")
                
                # Create NPC data
                npc_data = {
                    'id': getattr(npc, 'id', f"npc_{i}"),  # Add an ID for reference
                    'name': npc.name,
                    'description': npc.description,
                    'money': getattr(npc, 'money', 0),
                    'current_area': current_area_name,
                    'grid_position': [int(grid_x), int(grid_y)] if grid_x is not None and grid_y is not None else None,
                    'inventory': inventory,
                    'action_cooldown': getattr(npc, 'action_cooldown', 0),
                    'desire_to_shop_chance': getattr(npc, 'desire_to_shop_chance', 0.6),
                    'is_currently_shopping': getattr(npc, 'is_currently_shopping', False),
                    'desire_to_change_area_chance': getattr(npc, 'desire_to_change_area_chance', 0.05),
                    'shopping_target_item_name': getattr(npc, 'shopping_target_item_name', None),
                    'is_fleeing': getattr(npc, 'is_fleeing', False),
                    'flee_timer': getattr(npc, 'flee_timer', 0),
                    # Mission-related attributes
                    'current_mission_type': getattr(npc, 'current_mission_type', None),
                    'mission_item_name': getattr(npc, 'mission_item_name', None),
                    'mission_target_area_name': getattr(npc, 'mission_target_area_name', None),
                    'mission_target_coords': list(getattr(npc, 'mission_target_coords', (None, None))) if getattr(npc, 'mission_target_coords', None) is not None else None,
                    'mission_phase': getattr(npc, 'mission_phase', None),
                    'active_mission_influence_id': getattr(npc, 'active_mission_influence_id', None),
                    # Additional attributes for influence tracking
                    'recently_processed_influences': self._serialize_dict(getattr(npc, 'recently_processed_influences', {})),
                    'active_influence_source_id': getattr(npc, 'active_influence_source_id', None),
                    'recently_failed_to_buy': self._serialize_dict(getattr(npc, 'recently_failed_to_buy', {})),
                    'shopping_frustration_cooldown': getattr(npc, 'shopping_frustration_cooldown', 0)
                }
                
                npcs.append(npc_data)
                print(f"Debug: Successfully serialized NPC: {npc.name}")
            except Exception as e:
                print(f"Warning: Error serializing NPC at index {i}: {str(e)}")
        
        return npcs
    
    def _serialize_items(self):
        """Serialize all items to a list of dictionaries."""
        items = []
        
        for item_id, item in self.game_manager.item_manager.items_master_list.items():
            try:
                # Skip if item is not a proper object
                if not hasattr(item, 'name') or not hasattr(item, 'description'):
                    print(f"Warning: Skipping invalid item object with ID {item_id}")
                    continue
                
                # Get item location (if in world)
                in_area = False
                area_name = None
                grid_position = None
                
                # Check each area to find where this item is
                for area in self.game_manager.area_manager.areas.values():
                    if hasattr(area, 'items') and item in area.items:
                        in_area = True
                        area_name = area.name
                        try:
                            if hasattr(item, 'coordinates') and item.coordinates and hasattr(area, 'get_relative_coordinates'):
                                grid_x, grid_y = area.get_relative_coordinates(item.coordinates)[:2]
                                grid_position = [int(grid_x), int(grid_y)]
                        except Exception as e:
                            print(f"Warning: Could not get grid position for item {item.name}: {str(e)}")
                        break
                
                # Create item data
                item_data = {
                    'name': item.name,
                    'description': item.description,
                    'value': getattr(item, 'value', 0),
                    'pickupable': getattr(item, 'pickupable', True),
                    'in_area': in_area,
                    'area_name': area_name,
                    'grid_position': grid_position
                }
                
                items.append(item_data)
            except Exception as e:
                print(f"Warning: Error serializing item with ID {item_id}: {str(e)}")
        
        return items
    
    def _serialize_computers(self):
        """Serialize all computers to a list of dictionaries."""
        computers = []
        
        for i, computer in enumerate(self.game_manager.computers):
            try:
                # Skip if computer is not a proper object
                if not hasattr(computer, 'name') or not hasattr(computer, 'description'):
                    print(f"Warning: Skipping invalid computer object at index {i}")
                    continue
                
                # Get computer location
                area_name = None
                grid_position = None
                
                # Find which area the computer is in
                for area in self.game_manager.area_manager.areas.values():
                    if not hasattr(area, 'grid_width') or not hasattr(area, 'grid_length'):
                        continue
                        
                    for gx in range(area.grid_width):
                        for gy in range(area.grid_length):
                            if hasattr(area, 'get_objects_at_grid_cell'):
                                objects = area.get_objects_at_grid_cell(gx, gy)
                                if computer in objects:
                                    area_name = area.name
                                    grid_position = [gx, gy]
                                    break
                        if grid_position:
                            break
                    if grid_position:
                        break
                
                # Serialize stock data if it's a stock terminal
                stock_data = None
                if hasattr(computer, 'stock_data'):
                    stock_data = computer.stock_data
                
                # Create computer data
                computer_data = {
                    'name': computer.name,
                    'description': computer.description,
                    'area_name': area_name,
                    'grid_position': grid_position,
                    'stock_data': stock_data
                }
                
                computers.append(computer_data)
            except Exception as e:
                print(f"Warning: Error serializing computer at index {i}: {str(e)}")
        
        return computers
    
    def _deserialize_player(self, player_data):
        """Restore player state from serialized data."""
        try:
            print("Debug: Deserializing player data")
            
            # Check if player_data is valid
            if not isinstance(player_data, dict):
                print("Warning: Player data is not a dictionary")
                return
                
            player = self.game_manager.player
            
            # Restore basic attributes
            player.name = player_data.get('name', 'Vita')
            player.money = player_data.get('money', 500)
            
            if hasattr(player, 'stock_portfolio'):
                stock_portfolio = player_data.get('stock_portfolio')
                if isinstance(stock_portfolio, dict):
                    player.stock_portfolio = stock_portfolio
                else:
                    print("Warning: Player stock portfolio is not a dictionary, using default")
                    player.stock_portfolio = {}
            
            if hasattr(player, 'properties_portfolio'):
                properties_portfolio = player_data.get('properties_portfolio')
                if isinstance(properties_portfolio, dict):
                    player.properties_portfolio = properties_portfolio
                else:
                    print("Warning: Player properties portfolio is not a dictionary, using default")
                    player.properties_portfolio = {}
            
            # Clear inventory
            player.inventory = []
            
            # Restore inventory items
            inventory_data = player_data.get('inventory', [])
            if isinstance(inventory_data, list):
                for i, item_data in enumerate(inventory_data):
                    if not isinstance(item_data, dict):
                        print(f"Warning: Player inventory item at index {i} is not a dictionary")
                        continue
                        
                    from .item import Item
                    item = Item(
                        name=item_data.get('name', 'Unknown Item'),
                        description=item_data.get('description', ''),
                        value=item_data.get('value', 0)
                    )
                    player.inventory.append(item)
                    self.game_manager.item_manager.items_master_list[item.id] = item
                    print(f"Debug: Added {item.name} to player inventory")
            else:
                print("Warning: Player inventory is not a list")
            
            # Restore current area and position
            current_area_name = player_data.get('current_area')
            grid_position = player_data.get('grid_position')
            
            if current_area_name and grid_position and isinstance(grid_position, list) and len(grid_position) >= 2:
                # Find the area by name
                area_found = False
                for area_id, area in self.game_manager.area_manager.areas.items():
                    if area.name == current_area_name:
                        try:
                            player.set_current_area(area, grid_position[0], grid_position[1])
                            area_found = True
                            print(f"Debug: Placed player in {area.name} at {grid_position}")
                            break
                        except Exception as e:
                            print(f"Warning: Could not place player in area {area.name}: {str(e)}")
                
                if not area_found:
                    print(f"Warning: Could not find area '{current_area_name}' for player")
                    # Try to place player in the first available area as a fallback
                    if self.game_manager.area_manager.areas:
                        first_area = next(iter(self.game_manager.area_manager.areas.values()))
                        player.set_current_area(first_area, 1, 1)
                        print(f"Debug: Placed player in {first_area.name} at [1, 1] as fallback")
            else:
                print("Warning: Invalid player area or position")
                # Try to place player in the first available area as a fallback
                if self.game_manager.area_manager.areas:
                    first_area = next(iter(self.game_manager.area_manager.areas.values()))
                    player.set_current_area(first_area, 1, 1)
                    print(f"Debug: Placed player in {first_area.name} at [1, 1] as fallback")
                    
            print("Debug: Player deserialization complete")
        except Exception as e:
            print(f"Error deserializing player: {str(e)}")
            # Try to place player in the first available area as a fallback
            if hasattr(self.game_manager, 'area_manager') and hasattr(self.game_manager.area_manager, 'areas') and self.game_manager.area_manager.areas:
                try:
                    first_area = next(iter(self.game_manager.area_manager.areas.values()))
                    self.game_manager.player.set_current_area(first_area, 1, 1)
                    print(f"Debug: Placed player in {first_area.name} at [1, 1] as emergency fallback")
                except Exception as e2:
                    print(f"Critical error placing player: {str(e2)}")
    
    def _deserialize_areas(self, areas_data):
        """Restore areas from serialized data."""
        from .area import Area
        from .coordinates import Coordinates
        
        print(f"Debug: Deserializing {len(areas_data)} areas")
        
        # First pass: Create all areas
        for i, area_data in enumerate(areas_data):
            try:
                print(f"Debug: Deserializing area {i+1}/{len(areas_data)}")
                
                # Check if area_data is valid
                if not isinstance(area_data, dict):
                    print(f"Warning: Area data at index {i} is not a dictionary")
                    continue
                
                area_id = area_data.get('id')
                if not area_id:
                    print(f"Warning: Area at index {i} has no ID, generating one")
                    area_id = f"area_{i}"
                    
                name = area_data.get('name')
                if not name:
                    print(f"Warning: Area at index {i} has no name, using default")
                    name = f"Area {i}"
                    
                description = area_data.get('description', '')
                origin_coords_data = area_data.get('origin_coords', [0, 0, 0])
                grid_width = area_data.get('grid_width', 10)
                grid_length = area_data.get('grid_length', 10)
                
                # Create origin coordinates
                origin_coords = Coordinates(origin_coords_data[0], origin_coords_data[1], origin_coords_data[2])
                
                # Create area
                area = Area(name=name, description=description, area_origin_coords=origin_coords, 
                            grid_width=grid_width, grid_length=grid_length)
                
                # Set area ID to match saved ID
                area.id = area_id
                
                # Set additional properties
                if 'associated_stock_symbol' in area_data:
                    area.associated_stock_symbol = area_data['associated_stock_symbol']
                
                if 'is_shelter' in area_data:
                    area.is_shelter = area_data['is_shelter']
                
                # Add area to manager
                self.game_manager.area_manager.areas[area_id] = area
                print(f"Debug: Successfully created area: {name} (ID: {area_id})")
            except Exception as e:
                print(f"Warning: Error creating area at index {i}: {str(e)}")
        
        # Second pass: Restore connections between areas
        for i, area_data in enumerate(areas_data):
            try:
                if not isinstance(area_data, dict):
                    continue
                    
                area_id = area_data.get('id')
                if not area_id or area_id not in self.game_manager.area_manager.areas:
                    continue
                    
                area = self.game_manager.area_manager.areas.get(area_id)
                
                # Restore connections
                connections = area_data.get('connections', {})
                if not isinstance(connections, dict):
                    print(f"Warning: Connections for area {area.name} is not a dictionary")
                    continue
                    
                for direction, connected_area_name in connections.items():
                    # Find connected area by name
                    connected_area = None
                    for other_area_id, other_area in self.game_manager.area_manager.areas.items():
                        if other_area.name == connected_area_name:
                            connected_area = other_area
                            break
                            
                    if connected_area:
                        area.connections[direction] = connected_area
                        print(f"Debug: Connected {area.name} to {connected_area.name} via {direction}")
                    else:
                        print(f"Warning: Could not find connected area '{connected_area_name}' for {area.name}")
                
                # Restore shop stock if applicable
                shop_stock_data = area_data.get('shop_stock')
                if shop_stock_data and isinstance(shop_stock_data, list):
                    from .item import Item
                    area.shop_stock = {}
                    
                    for stock_item in shop_stock_data:
                        if not isinstance(stock_item, dict):
                            continue
                            
                        item_key = stock_item.get('item_key')
                        if not item_key:
                            continue
                            
                        name = stock_item.get('name', 'Unknown Item')
                        description = stock_item.get('description', '')
                        value = stock_item.get('value', 0)
                        price = stock_item.get('price', 0)
                        quantity_value = stock_item.get('quantity', 0)
                        quantity = float('inf') if quantity_value == "infinite" else quantity_value
                        
                        # Create prototype item
                        prototype = Item(name=name, description=description, value=value)
                        
                        # Add to shop stock
                        area.shop_stock[item_key] = {
                            'prototype': prototype,
                            'price': price,
                            'stock': quantity
                        }
                        print(f"Debug: Added {name} to {area.name}'s shop stock")
            except Exception as e:
                print(f"Warning: Error restoring connections for area at index {i}: {str(e)}")
    
    def _deserialize_npcs(self, npcs_data):
        """Restore NPCs from serialized data."""
        from .npc import NPC
        
        print(f"Debug: Deserializing {len(npcs_data)} NPCs")
        
        # Make sure we're starting with a clean dictionary for NPCs
        # This ensures we don't have any leftover state from previous loads
        self.game_manager.npc_manager.npcs = {}
        
        for i, npc_data in enumerate(npcs_data):
            try:
                print(f"Debug: Deserializing NPC {i+1}/{len(npcs_data)}")
                
                # Check if npc_data is valid
                if not isinstance(npc_data, dict):
                    print(f"Warning: NPC data at index {i} is not a dictionary")
                    continue
                
                # Get basic NPC data
                name = npc_data.get('name')
                if not name:
                    print(f"Warning: NPC at index {i} has no name, using default")
                    name = f"NPC {i}"
                    
                description = npc_data.get('description', '')
                money = npc_data.get('money', 20)
                
                # Create NPC
                npc = NPC(name=name, description=description, money=money)
                
                # Set ID if available
                if 'id' in npc_data:
                    npc.id = npc_data['id']
                
                # Restore attributes
                npc.action_cooldown = npc_data.get('action_cooldown', 0)
                npc.desire_to_shop_chance = npc_data.get('desire_to_shop_chance', 0.6)
                npc.is_currently_shopping = npc_data.get('is_currently_shopping', False)
                npc.desire_to_change_area_chance = npc_data.get('desire_to_change_area_chance', 0.05)
                npc.shopping_target_item_name = npc_data.get('shopping_target_item_name')
                npc.is_fleeing = npc_data.get('is_fleeing', False)
                npc.flee_timer = npc_data.get('flee_timer', 0)
                
                # Restore mission-related attributes
                npc.current_mission_type = npc_data.get('current_mission_type')
                npc.mission_item_name = npc_data.get('mission_item_name')
                npc.mission_target_area_name = npc_data.get('mission_target_area_name')
                
                # Convert mission_target_coords from list back to tuple
                mission_coords = npc_data.get('mission_target_coords')
                if isinstance(mission_coords, list) and len(mission_coords) >= 2:
                    npc.mission_target_coords = tuple(mission_coords[:2])  # Take only the first two elements
                else:
                    npc.mission_target_coords = None
                    
                npc.mission_phase = npc_data.get('mission_phase')
                npc.active_mission_influence_id = npc_data.get('active_mission_influence_id')
                
                # Restore influence tracking attributes
                npc.recently_processed_influences = self._deserialize_dict(npc_data.get('recently_processed_influences', {}))
                npc.active_influence_source_id = npc_data.get('active_influence_source_id')
                npc.recently_failed_to_buy = self._deserialize_dict(npc_data.get('recently_failed_to_buy', {}))
                npc.shopping_frustration_cooldown = npc_data.get('shopping_frustration_cooldown', 0)
                
                # Restore inventory
                from .item import Item
                inventory_data = npc_data.get('inventory', [])
                if isinstance(inventory_data, list):
                    for item_data in inventory_data:
                        if not isinstance(item_data, dict):
                            continue
                            
                        item = Item(
                            name=item_data.get('name', 'Unknown Item'),
                            description=item_data.get('description', ''),
                            value=item_data.get('value', 0)
                        )
                        npc.add_item_to_inventory(item)
                        self.game_manager.item_manager.items_master_list[item.id] = item
                
                # Place NPC in area
                current_area_name = npc_data.get('current_area')
                grid_position = npc_data.get('grid_position')
                
                if current_area_name and grid_position and isinstance(grid_position, list) and len(grid_position) >= 2:
                    # Find the area by name
                    area_found = False
                    for area_id, area in self.game_manager.area_manager.areas.items():
                        if area.name == current_area_name:
                            try:
                                area.add_object_to_grid(npc, grid_position[0], grid_position[1])
                                npc.location = area
                                area_found = True
                                print(f"Debug: Placed NPC {name} in {area.name} at {grid_position}")
                                break
                            except Exception as e:
                                print(f"Warning: Could not place NPC {name} in area {area.name}: {str(e)}")
                    
                    if not area_found:
                        print(f"Warning: Could not find area '{current_area_name}' for NPC {name}")
                
                # Add NPC to manager
                self.game_manager.npc_manager.add_npc(npc)
                print(f"Debug: Successfully added NPC: {name}")
            except Exception as e:
                print(f"Warning: Error deserializing NPC at index {i}: {str(e)}")
    
    def _deserialize_items(self, items_data):
        """Restore items from serialized data."""
        from .item import Item
        
        print(f"Debug: Deserializing {len(items_data)} items")
        
        for i, item_data in enumerate(items_data):
            try:
                print(f"Debug: Deserializing item {i+1}/{len(items_data)}")
                
                # Check if item_data is valid
                if not isinstance(item_data, dict):
                    print(f"Warning: Item data at index {i} is not a dictionary")
                    continue
                
                # Get basic item data
                name = item_data.get('name')
                if not name:
                    print(f"Warning: Item at index {i} has no name, using default")
                    name = f"Item {i}"
                    
                description = item_data.get('description', '')
                value = item_data.get('value', 0)
                pickupable = item_data.get('pickupable', True)
                
                # Create item
                item = Item(name=name, description=description, value=value)
                
                # Set pickupable attribute
                item.pickupable = pickupable
                
                # Add to master list
                self.game_manager.item_manager.items_master_list[item.id] = item
                print(f"Debug: Created item: {name} (ID: {item.id})")
                
                # Place item in area if applicable
                in_area = item_data.get('in_area', False)
                if in_area:
                    area_name = item_data.get('area_name')
                    grid_position = item_data.get('grid_position')
                    
                    if area_name and grid_position and isinstance(grid_position, list) and len(grid_position) >= 2:
                        # Find the area by name
                        area_found = False
                        for area_id, area in self.game_manager.area_manager.areas.items():
                            if area.name == area_name:
                                try:
                                    area.add_object_to_grid(item, grid_position[0], grid_position[1])
                                    area_found = True
                                    print(f"Debug: Placed item {name} in {area.name} at {grid_position}")
                                    break
                                except Exception as e:
                                    print(f"Warning: Could not place item {name} in area {area.name}: {str(e)}")
                        
                        if not area_found:
                            print(f"Warning: Could not find area '{area_name}' for item {name}")
            except Exception as e:
                print(f"Warning: Error deserializing item at index {i}: {str(e)}")
    
    def _deserialize_computers(self, computers_data):
        """Restore computers from serialized data."""
        from .game_objects import Computer
        
        print(f"Debug: Deserializing {len(computers_data)} computers")
        
        for i, computer_data in enumerate(computers_data):
            try:
                print(f"Debug: Deserializing computer {i+1}/{len(computers_data)}")
                
                # Check if computer_data is valid
                if not isinstance(computer_data, dict):
                    print(f"Warning: Computer data at index {i} is not a dictionary")
                    continue
                
                # Get basic computer data
                name = computer_data.get('name')
                if not name:
                    print(f"Warning: Computer at index {i} has no name, using default")
                    name = f"Computer {i}"
                    
                description = computer_data.get('description', '')
                
                # Create computer
                computer = Computer(name=name, description=description)
                
                # Restore stock data if applicable
                if 'stock_data' in computer_data and computer_data['stock_data'] is not None:
                    computer.stock_data = computer_data['stock_data']
                
                # Place computer in area
                area_name = computer_data.get('area_name')
                grid_position = computer_data.get('grid_position')
                
                if area_name and grid_position and isinstance(grid_position, list) and len(grid_position) >= 2:
                    # Find the area by name
                    area_found = False
                    for area_id, area in self.game_manager.area_manager.areas.items():
                        if area.name == area_name:
                            try:
                                area.add_object_to_grid(computer, grid_position[0], grid_position[1])
                                area_found = True
                                print(f"Debug: Placed computer {name} in {area.name} at {grid_position}")
                                break
                            except Exception as e:
                                print(f"Warning: Could not place computer {name} in area {area.name}: {str(e)}")
                    
                    if not area_found:
                        print(f"Warning: Could not find area '{area_name}' for computer {name}")
                
                # Add to computers list
                self.game_manager.computers.append(computer)
                print(f"Debug: Added computer: {name}")
            except Exception as e:
                print(f"Warning: Error deserializing computer at index {i}: {str(e)}")