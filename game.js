/**
 * Vita Game Hustle - Web Version
 * A text-based adventure game where Vita the bunny causes chaos and makes money.
 */

// Game Classes
class Coordinates {
    constructor(x, y, z = 0) {
        this.x = x;
        this.y = y;
        this.z = z;
    }

    toString() {
        return `(${this.x}, ${this.y}, ${this.z})`;
    }
}

class GameObject {
    constructor(name, description) {
        this.id = Math.random().toString(36).substring(2, 15);
        this.name = name;
        this.description = description;
        this.coordinates = null;
    }
}

class Item extends GameObject {
    constructor(name, description, value = 0) {
        super(name, description);
        this.value = value;
        this.pickupable = true;
    }
}

class InfluenceSource extends GameObject {
    constructor(name, description, actionType, influenceRadius, influenceStrength) {
        super(name, description);
        this.actionType = actionType; // 'buy', 'sell', 'move', 'deliver'
        this.influenceRadius = influenceRadius;
        this.influenceStrength = influenceStrength;
        
        // Additional properties based on action type
        this.targetItemName = null;      // For 'buy' influence
        this.targetAreaName = null;      // For 'move' influence
        this.deliveryItemName = null;    // For 'deliver' influence
        this.deliveryTargetAreaName = null;
        this.deliveryTargetCoords = null;
        this.coordinates = null;         // Position in the world
    }
    
    // Set target item for 'buy' influence
    setTargetItem(itemName) {
        this.targetItemName = itemName;
        return this;
    }
    
    // Set target area for 'move' influence
    setTargetArea(areaName) {
        this.targetAreaName = areaName;
        return this;
    }
    
    // Set delivery details for 'deliver' influence
    setDeliveryDetails(itemName, targetAreaName, targetCoords = null) {
        this.deliveryItemName = itemName;
        this.deliveryTargetAreaName = targetAreaName;
        this.deliveryTargetCoords = targetCoords;
        return this;
    }
    
    // Calculate influence on an NPC based on distance
    calculateInfluence(npc) {
        if (!this.coordinates || !npc.coordinates) return 0;
        
        // Calculate distance between influence source and NPC
        const dx = this.coordinates.x - npc.coordinates.x;
        const dy = this.coordinates.y - npc.coordinates.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // If NPC is outside influence radius, no effect
        if (distance > this.influenceRadius) return 0;
        
        // Influence decreases with distance
        const distanceFactor = 1 - (distance / this.influenceRadius);
        return this.influenceStrength * distanceFactor;
    }
}

class Computer extends GameObject {
    constructor(name, description) {
        super(name, description);
        this.stocks = {
            'MALL': { price: 10.00, history: [10.00], sales: 0 },
            'TECH': { price: 25.00, history: [25.00], sales: 0 },
            'FARM': { price: 5.00, history: [5.00], sales: 0 }
        };
    }

    interact(player) {
        game.displayMessage("You access the stock terminal.");
        game.displayMessage("Available commands: 'check stocks', 'buy [symbol] [shares]', 'sell [symbol] [shares]', 'exit'");
        game.enterStockTerminalMode();
    }

    recordSaleForStock(symbol, price) {
        if (this.stocks[symbol]) {
            this.stocks[symbol].sales += price;
            // Adjust stock price based on sales
            const priceChange = (Math.random() * 0.2 - 0.1) + (price * 0.01);
            this.stocks[symbol].price += priceChange;
            this.stocks[symbol].history.push(this.stocks[symbol].price);
            
            // Keep history at a reasonable size
            if (this.stocks[symbol].history.length > 20) {
                this.stocks[symbol].history.shift();
            }
        }
    }

    getStockInfo() {
        let info = "Current Stock Prices:\n";
        for (const [symbol, data] of Object.entries(this.stocks)) {
            info += `${symbol}: $${data.price.toFixed(2)} `;
            
            // Show trend
            if (data.history.length > 1) {
                const lastPrice = data.history[data.history.length - 2];
                if (data.price > lastPrice) {
                    info += "↑";
                } else if (data.price < lastPrice) {
                    info += "↓";
                } else {
                    info += "→";
                }
            }
            info += "\n";
        }
        return info;
    }
}

class NPC extends GameObject {
    constructor(name, description, startCoords, area, money = 0) {
        super(name, description);
        this.coordinates = startCoords;
        this.money = money;
        this.inventory = [];
        this.location = area;
        this.isFleeing = false;
        this.fleeingDuration = 0;
        this.lastActionTurn = 0;
        
        // Personality traits (0-1 scale)
        this.traits = {
            greed: Math.random(),           // Likelihood to pick up valuable items
            curiosity: Math.random(),       // Likelihood to explore
            impulsiveness: Math.random(),   // Likelihood to make purchases
            influenceability: Math.random() // How susceptible to influence sources
        };
        
        // Current goals and influences
        this.currentGoal = null;  // 'buy', 'move', 'deliver', etc.
        this.goalTarget = null;   // Item name, area name, etc.
        this.goalStrength = 0;    // How strongly motivated (0-1)
        this.goalExpiration = 0;  // Game turn when goal expires
        
        // For pathfinding
        this.knownAreas = new Set(); // Areas the NPC has visited
        if (area) this.knownAreas.add(area.name);
    }

    addItemToInventory(item) {
        this.inventory.push(item);
        item.coordinates = null; // Item is no longer in the world
    }

    removeItemFromInventory(itemName) {
        const itemIndex = this.inventory.findIndex(item => 
            item.name.toLowerCase() === itemName.toLowerCase());
        
        if (itemIndex !== -1) {
            const item = this.inventory[itemIndex];
            this.inventory.splice(itemIndex, 1);
            return item;
        }
        
        return null;
    }

    startFleeing(duration = 3) {
        this.isFleeing = true;
        this.fleeingDuration = duration;
        // Clear current goal when fleeing
        this.clearGoal();
        return `${this.name} starts running away in panic!`;
    }
    
    setGoal(goalType, target, strength, duration) {
        this.currentGoal = goalType;
        this.goalTarget = target;
        this.goalStrength = Math.min(1, Math.max(0, strength)); // Clamp between 0-1
        this.goalExpiration = this.lastActionTurn + duration;
    }
    
    clearGoal() {
        this.currentGoal = null;
        this.goalTarget = null;
        this.goalStrength = 0;
        this.goalExpiration = 0;
    }
    
    // Check if NPC is influenced by nearby influence sources
    checkInfluences(influenceSources) {
        if (!this.location || !this.coordinates) return;
        
        // Skip if NPC is fleeing
        if (this.isFleeing) return;
        
        // Find influence sources in the same area
        const sourcesInArea = influenceSources.filter(source => 
            source.coordinates && 
            this.location === source.location);
        
        for (const source of sourcesInArea) {
            const influenceStrength = source.calculateInfluence(this);
            
            // Skip if influence is too weak or NPC is resistant
            if (influenceStrength <= 0.1) continue;
            
            // Adjust influence based on NPC's influenceability
            const adjustedInfluence = influenceStrength * this.traits.influenceability;
            
            // Only set a new goal if the influence is stronger than current goal
            // or if there is no current goal
            if (adjustedInfluence > this.goalStrength || !this.currentGoal) {
                // Duration based on influence strength (stronger = longer)
                const duration = Math.floor(5 + (adjustedInfluence * 10));
                
                switch (source.actionType) {
                    case 'buy':
                        if (source.targetItemName) {
                            this.setGoal('buy', source.targetItemName, adjustedInfluence, duration);
                        }
                        break;
                    case 'move':
                        if (source.targetAreaName) {
                            this.setGoal('move', source.targetAreaName, adjustedInfluence, duration);
                        }
                        break;
                    case 'deliver':
                        if (source.deliveryItemName && source.deliveryTargetAreaName) {
                            // Check if NPC has the item to deliver
                            const hasItem = this.inventory.some(item => 
                                item.name.toLowerCase() === source.deliveryItemName.toLowerCase());
                            
                            if (hasItem) {
                                this.setGoal('deliver', {
                                    item: source.deliveryItemName,
                                    area: source.deliveryTargetAreaName,
                                    coords: source.deliveryTargetCoords
                                }, adjustedInfluence, duration);
                            }
                        }
                        break;
                }
            }
        }
    }

    update(gameTurn) {
        // Skip if already acted this turn
        if (this.lastActionTurn === gameTurn) return null;
        
        this.lastActionTurn = gameTurn;
        
        // Check if goal has expired
        if (this.currentGoal && gameTurn > this.goalExpiration) {
            this.clearGoal();
        }
        
        // Handle fleeing behavior (highest priority)
        if (this.isFleeing) {
            this.fleeingDuration--;
            if (this.fleeingDuration <= 0) {
                this.isFleeing = false;
                return `${this.name} calms down and stops fleeing.`;
            }
            
            // Move randomly while fleeing
            const directions = ['north', 'south', 'east', 'west'];
            const randomDirection = directions[Math.floor(Math.random() * directions.length)];
            this.move(randomDirection);
            return `${this.name} continues to flee in panic!`;
        }
        
        // Handle goal-directed behavior
        if (this.currentGoal) {
            switch (this.currentGoal) {
                case 'buy':
                    return this.pursueBuyGoal();
                case 'move':
                    return this.pursueMoveGoal();
                case 'deliver':
                    return this.pursueDeliverGoal();
            }
        }
        
        // Random actions when not fleeing or pursuing a goal (30% chance to do something)
        if (Math.random() < 0.3) {
            const actions = [
                { action: this.randomMove.bind(this), weight: this.traits.curiosity },
                { action: this.lookAtItems.bind(this), weight: 0.5 },
                { action: this.considerPickingUpItem.bind(this), weight: this.traits.greed },
                { action: this.considerBuying.bind(this), weight: this.traits.impulsiveness }
            ];
            
            // Weight-based random selection
            const totalWeight = actions.reduce((sum, action) => sum + action.weight, 0);
            let randomValue = Math.random() * totalWeight;
            
            for (const action of actions) {
                randomValue -= action.weight;
                if (randomValue <= 0) {
                    return action.action();
                }
            }
            
            // Fallback if weights don't add up properly
            return actions[0].action();
        }
        
        return null; // No action this turn
    }
    
    pursueBuyGoal() {
        if (!this.location) return null;
        
        // If in a shop with the target item
        if (this.location.shopStock && 
            this.goalTarget.toLowerCase() in this.location.shopStock) {
            
            return this.buySpecificItem(this.goalTarget);
        }
        
        // Otherwise, move toward a shop that might have it
        // For simplicity, just move randomly for now, but prefer shops
        for (const [direction, area] of Object.entries(this.location.connections)) {
            if (area.shopStock) {
                this.move(direction);
                return `${this.name} heads ${direction} toward ${area.name}, looking for ${this.goalTarget}.`;
            }
        }
        
        // If no shop found, move randomly
        return this.randomMove();
    }
    
    pursueMoveGoal() {
        if (!this.location) return null;
        
        // If already in target area, goal is complete
        if (this.location.name.toLowerCase() === this.goalTarget.toLowerCase()) {
            this.clearGoal();
            return `${this.name} arrives at ${this.location.name}.`;
        }
        
        // Try to find a path to the target area
        // For simplicity, just check direct connections first
        for (const [direction, area] of Object.entries(this.location.connections)) {
            if (area.name.toLowerCase() === this.goalTarget.toLowerCase()) {
                this.move(direction);
                return `${this.name} heads ${direction} toward ${area.name}.`;
            }
        }
        
        // If no direct connection, move randomly for now
        // In a more complex implementation, we would use pathfinding
        return this.randomMove();
    }
    
    pursueDeliverGoal() {
        if (!this.location) return null;
        
        // Check if NPC has the item to deliver
        const hasItem = this.inventory.some(item => 
            item.name.toLowerCase() === this.goalTarget.item.toLowerCase());
        
        if (!hasItem) {
            this.clearGoal();
            return `${this.name} no longer has the ${this.goalTarget.item} to deliver.`;
        }
        
        // If in target area, deliver the item
        if (this.location.name.toLowerCase() === this.goalTarget.area.toLowerCase()) {
            const item = this.removeItemFromInventory(this.goalTarget.item);
            
            if (item) {
                // If specific coordinates provided, place item there
                if (this.goalTarget.coords) {
                    this.location.addObjectToGrid(item, 
                        this.goalTarget.coords.x, 
                        this.goalTarget.coords.y);
                } else {
                    // Otherwise place at NPC's position
                    const [gridX, gridY] = this.location.getRelativeCoordinates(this.coordinates);
                    this.location.addObjectToGrid(item, gridX, gridY);
                }
                
                this.clearGoal();
                return `${this.name} delivers the ${item.name} to ${this.location.name}.`;
            }
        }
        
        // Otherwise, move toward target area (similar to pursueMoveGoal)
        for (const [direction, area] of Object.entries(this.location.connections)) {
            if (area.name.toLowerCase() === this.goalTarget.area.toLowerCase()) {
                this.move(direction);
                return `${this.name} heads ${direction} toward ${area.name} to deliver the ${this.goalTarget.item}.`;
            }
        }
        
        // If no direct connection, move randomly
        return this.randomMove();
    }

    randomMove() {
        const directions = ['north', 'south', 'east', 'west'];
        const randomDirection = directions[Math.floor(Math.random() * directions.length)];
        
        const result = this.move(randomDirection);
        if (result) {
            return `${this.name} wanders ${randomDirection}.`;
        }
        return null;
    }

    move(direction) {
        if (!this.location) return false;
        
        // Get current grid position
        const [gridX, gridY] = this.location.getRelativeCoordinates(this.coordinates);
        let newGridX = gridX;
        let newGridY = gridY;
        
        // Calculate new position
        if (direction === 'north') newGridY += 1;
        else if (direction === 'south') newGridY -= 1;
        else if (direction === 'east') newGridX += 1;
        else if (direction === 'west') newGridX -= 1;
        
        // Check if new position is valid
        if (this.location.isValidGridPosition(newGridX, newGridY)) {
            this.coordinates = this.location.getGlobalCoordinates(newGridX, newGridY);
            return true;
        } else if (direction in this.location.connections) {
            // Move to connected area
            const newArea = this.location.connections[direction];
            this.location.removeNPC(this);
            this.location = newArea;
            
            // Add to known areas
            this.knownAreas.add(newArea.name);
            
            // Place at appropriate entry point in new area
            if (direction === 'north') {
                newGridX = Math.floor(newArea.gridWidth / 2);
                newGridY = 0;
            } else if (direction === 'south') {
                newGridX = Math.floor(newArea.gridWidth / 2);
                newGridY = newArea.gridLength - 1;
            } else if (direction === 'east') {
                newGridX = 0;
                newGridY = Math.floor(newArea.gridLength / 2);
            } else if (direction === 'west') {
                newGridX = newArea.gridWidth - 1;
                newGridY = Math.floor(newArea.gridLength / 2);
            }
            
            this.coordinates = newArea.getGlobalCoordinates(newGridX, newGridY);
            newArea.addNPC(this);
            return true;
        }
        
        return false;
    }

    lookAtItems() {
        if (!this.location) return null;
        
        const [gridX, gridY] = this.location.getRelativeCoordinates(this.coordinates);
        const objectsHere = this.location.getObjectsAtGridCell(gridX, gridY);
        
        const items = objectsHere.filter(obj => obj instanceof Item);
        if (items.length > 0) {
            const randomItem = items[Math.floor(Math.random() * items.length)];
            return `${this.name} examines the ${randomItem.name} curiously.`;
        }
        
        return null;
    }
    
    considerPickingUpItem() {
        if (!this.location) return null;
        
        const [gridX, gridY] = this.location.getRelativeCoordinates(this.coordinates);
        const objectsHere = this.location.getObjectsAtGridCell(gridX, gridY);
        
        // Filter for pickupable items
        const pickupableItems = objectsHere.filter(obj => 
            obj instanceof Item && obj.pickupable);
        
        if (pickupableItems.length > 0) {
            // Sort by value (higher value first)
            pickupableItems.sort((a, b) => b.value - a.value);
            
            // Chance to pick up based on greed and item value
            const item = pickupableItems[0];
            const pickupChance = this.traits.greed * (0.3 + (item.value / 20));
            
            if (Math.random() < pickupChance) {
                this.location.removeObjectFromGrid(item, gridX, gridY);
                this.addItemToInventory(item);
                return `${this.name} picks up the ${item.name}.`;
            }
        }
        
        return null;
    }

    buySpecificItem(itemName) {
        if (!this.location || !this.location.shopStock || this.money <= 0) return null;
        
        const itemDetails = this.location.shopStock[itemName.toLowerCase()];
        
        if (itemDetails && itemDetails.stock > 0 && this.money >= itemDetails.price) {
            // Buy the item
            this.money -= itemDetails.price;
            const boughtItem = new Item(
                itemDetails.prototype.name, 
                itemDetails.prototype.description, 
                itemDetails.prototype.value
            );
            this.addItemToInventory(boughtItem);
            
            // Reduce stock
            if (itemDetails.stock !== Infinity) {
                itemDetails.stock--;
            }
            
            // Record purchase for stock market
            const purchaseInfo = {
                itemName: boughtItem.name,
                price: itemDetails.price,
                stockSymbol: this.location.associatedStockSymbol
            };
            
            // Clear goal after successful purchase
            this.clearGoal();
            
            return {
                message: `${this.name} buys a ${boughtItem.name} for $${itemDetails.price.toFixed(2)}.`,
                purchaseInfo: purchaseInfo
            };
        }
        
        return null;
    }

    considerBuying() {
        if (!this.location || !this.location.shopStock || this.money <= 0) return null;
        
        // Check if there are items for sale
        const affordableItems = Object.entries(this.location.shopStock)
            .filter(([_, details]) => details.price <= this.money && details.stock > 0);
        
        if (affordableItems.length > 0) {
            // Chance to buy based on impulsiveness
            if (Math.random() < this.traits.impulsiveness * 0.5) {
                const [itemName, details] = affordableItems[Math.floor(Math.random() * affordableItems.length)];
                
                // Buy the item
                this.money -= details.price;
                const boughtItem = new Item(
                    details.prototype.name, 
                    details.prototype.description, 
                    details.prototype.value
                );
                this.addItemToInventory(boughtItem);
                
                // Reduce stock
                if (details.stock !== Infinity) {
                    details.stock--;
                }
                
                // Record purchase for stock market
                const purchaseInfo = {
                    itemName: boughtItem.name,
                    price: details.price,
                    stockSymbol: this.location.associatedStockSymbol
                };
                
                return {
                    message: `${this.name} buys a ${boughtItem.name} for $${details.price.toFixed(2)}.`,
                    purchaseInfo: purchaseInfo
                };
            }
        }
        
        return null;
    }

    getStatusInfo(gameTurn) {
        let info = `--- ${this.name} ---\n`;
        info += `${this.description}\n`;
        info += `Location: ${this.location ? this.location.name : 'Unknown'}\n`;
        info += `Money: $${this.money.toFixed(2)}\n`;
        
        // Show personality traits
        info += `\nPersonality:\n`;
        info += `  Greed: ${Math.round(this.traits.greed * 100)}%\n`;
        info += `  Curiosity: ${Math.round(this.traits.curiosity * 100)}%\n`;
        info += `  Impulsiveness: ${Math.round(this.traits.impulsiveness * 100)}%\n`;
        info += `  Influenceability: ${Math.round(this.traits.influenceability * 100)}%\n`;
        
        // Show current status
        if (this.isFleeing) {
            info += `\nStatus: Fleeing (${this.fleeingDuration} turns remaining)\n`;
        } else if (this.currentGoal) {
            info += `\nCurrent Goal: ${this.currentGoal} `;
            if (this.currentGoal === 'buy' || this.currentGoal === 'move') {
                info += `${this.goalTarget}\n`;
            } else if (this.currentGoal === 'deliver') {
                info += `${this.goalTarget.item} to ${this.goalTarget.area}\n`;
            }
            info += `Goal Strength: ${Math.round(this.goalStrength * 100)}%\n`;
            info += `Expires in: ${this.goalExpiration - gameTurn} turns\n`;
        } else {
            info += `\nStatus: Idle\n`;
        }
        
        // Show inventory
        if (this.inventory.length > 0) {
            info += "\nInventory:\n";
            this.inventory.forEach(item => {
                info += `  - ${item.name} (Value: $${item.value})\n`;
            });
        } else {
            info += "\nInventory: Empty\n";
        }
        
        // Show known areas
        info += "\nKnown Areas: ";
        info += Array.from(this.knownAreas).join(", ");
        
        return info;
    }
}

class Area {
    constructor(name, description, areaOriginCoords, gridWidth, gridLength) {
        this.id = Math.random().toString(36).substring(2, 15);
        this.name = name;
        this.description = description;
        this.areaOriginCoords = areaOriginCoords;
        this.gridWidth = gridWidth;
        this.gridLength = gridLength;
        this.grid = Array(gridLength).fill().map(() => Array(gridWidth).fill().map(() => []));
        this.connections = {};
        this.items = [];
        this.npcs = [];
        this.shopStock = null;
        this.associatedStockSymbol = null;
        this.isShelter = false;
    }

    isValidGridPosition(x, y) {
        return x >= 0 && x < this.gridWidth && y >= 0 && y < this.gridLength;
    }

    getGlobalCoordinates(gridX, gridY) {
        return new Coordinates(
            this.areaOriginCoords.x + gridX,
            this.areaOriginCoords.y + gridY,
            this.areaOriginCoords.z
        );
    }

    getRelativeCoordinates(globalCoords) {
        return [
            globalCoords.x - this.areaOriginCoords.x,
            globalCoords.y - this.areaOriginCoords.y,
            globalCoords.z - this.areaOriginCoords.z
        ];
    }

    addObjectToGrid(obj, gridX, gridY) {
        if (!this.isValidGridPosition(gridX, gridY)) {
            console.error(`Invalid grid position (${gridX}, ${gridY}) for area ${this.name}`);
            return false;
        }
        
        obj.coordinates = this.getGlobalCoordinates(gridX, gridY);
        this.grid[gridY][gridX].push(obj);
        
        if (obj instanceof Item) {
            this.items.push(obj);
        } else if (obj instanceof NPC) {
            this.npcs.push(obj);
        }
        
        return true;
    }

    removeObjectFromGrid(obj, gridX, gridY) {
        if (!this.isValidGridPosition(gridX, gridY)) {
            return false;
        }
        
        const cellObjects = this.grid[gridY][gridX];
        const index = cellObjects.indexOf(obj);
        
        if (index !== -1) {
            cellObjects.splice(index, 1);
            
            if (obj instanceof Item) {
                const itemIndex = this.items.indexOf(obj);
                if (itemIndex !== -1) {
                    this.items.splice(itemIndex, 1);
                }
            } else if (obj instanceof NPC) {
                const npcIndex = this.npcs.indexOf(obj);
                if (npcIndex !== -1) {
                    this.npcs.splice(npcIndex, 1);
                }
            }
            
            return true;
        }
        
        return false;
    }

    getObjectsAtGridCell(gridX, gridY) {
        if (!this.isValidGridPosition(gridX, gridY)) {
            return [];
        }
        return this.grid[gridY][gridX];
    }

    addNPC(npc) {
        if (!this.npcs.includes(npc)) {
            this.npcs.push(npc);
        }
    }

    removeNPC(npc) {
        const index = this.npcs.indexOf(npc);
        if (index !== -1) {
            this.npcs.splice(index, 1);
        }
    }

    addItemToShop(itemPrototype, price, quantity) {
        if (!this.shopStock) {
            this.shopStock = {};
        }
        
        this.shopStock[itemPrototype.name.toLowerCase()] = {
            prototype: itemPrototype,
            price: price,
            stock: quantity
        };
    }

    getShopListing() {
        if (!this.shopStock) return [];
        
        return Object.entries(this.shopStock).map(([itemName, details]) => {
            const stockDisplay = details.stock === Infinity ? "∞" : details.stock;
            return `${details.prototype.name}: $${details.price.toFixed(2)} (Stock: ${stockDisplay})`;
        });
    }

    processPurchase(itemNameQuery, playerMoney) {
        if (!this.shopStock) return [null, 0];
        
        const itemKey = itemNameQuery.toLowerCase();
        const itemDetails = this.shopStock[itemKey];
        
        if (!itemDetails) return [null, 0];
        if (itemDetails.stock <= 0) return [null, 0];
        if (playerMoney < itemDetails.price) return [null, 0];
        
        // Create a new instance of the item
        const newItem = new Item(
            itemDetails.prototype.name,
            itemDetails.prototype.description,
            itemDetails.prototype.value
        );
        
        // Reduce stock if not infinite
        if (itemDetails.stock !== Infinity) {
            itemDetails.stock--;
        }
        
        return [newItem, itemDetails.price];
    }
}

class Player {
    constructor(name = "Vita", startMoney = 500, displayCallback = null) {
        this.name = name;
        this.inventory = [];
        this.currentArea = null;
        this.coordinates = new Coordinates(0, 0, 0);
        this.money = startMoney;
        this.stockPortfolio = {}; // symbol -> {shares: int, avgPrice: float}
        this.propertiesPortfolio = {}; // propertyId -> {name: str, value: float, lastCollectedTurn: int}
        this.displayMessage = displayCallback || console.log;
    }

    setCurrentArea(area, gridX = null, gridY = null) {
        this.currentArea = area;
        if (area) {
            if (gridX === null) {
                gridX = Math.floor(area.gridWidth / 2);
            }
            if (gridY === null) {
                gridY = Math.floor(area.gridLength / 2);
            }
            
            // Ensure player is within bounds
            gridX = Math.max(0, Math.min(gridX, area.gridWidth - 1));
            gridY = Math.max(0, Math.min(gridY, area.gridLength - 1));
            
            this.coordinates = area.getGlobalCoordinates(gridX, gridY);
            this.displayMessage(`You are now in ${area.name}. ${area.description}`);
            //this.lookAround();
        } else {
            this.displayMessage("Error: Tried to move to a null area.");
        }
    }

    getGridPosition() {
        if (!this.currentArea) {
            return [null, null];
        }
        const relCoords = this.currentArea.getRelativeCoordinates(this.coordinates);
        return [Math.floor(relCoords[0]), Math.floor(relCoords[1])];
    }

    lookAround() {
        if (!this.currentArea) {
            this.displayMessage("You are floating in the void...");
            return;
        }
        
        const [gridX, gridY] = this.getGridPosition();
        let output = `\n--- ${this.currentArea.name} ---\n`;
        output += `${this.currentArea.description}\n`;
        output += `You are at grid position (${gridX}, ${gridY}).\n`;
        
        // Display items at current position
        const objectsHere = this.currentArea.getObjectsAtGridCell(gridX, gridY);
        const itemsHere = objectsHere.filter(obj => obj instanceof Item);
        if (itemsHere.length > 0) {
            output += "Items at your feet:\n";
            itemsHere.forEach(item => {
                output += `  - ${item.name}: ${item.description}\n`;
            });
        }
        
        const otherGameObjectsHere = objectsHere.filter(obj => !(obj instanceof Item) && !(obj instanceof NPC));
        if (otherGameObjectsHere.length > 0) {
            output += "Objects here:\n";
            otherGameObjectsHere.forEach(gameObj => {
                output += `  - ${gameObj.name}: ${gameObj.description}\n`;
            });
        }
        
        // Display NPCs at current position
        const npcsHere = objectsHere.filter(obj => obj instanceof NPC);
        if (npcsHere.length > 0) {
            output += "People here:\n";
            npcsHere.forEach(npc => {
                output += `  - ${npc.name}\n`;
            });
        }
        
        // Display other items in the area
        if (this.currentArea.items.length > 0) {
            output += "Other items in the area:\n";
            this.currentArea.items.forEach(item => {
                if (!itemsHere.includes(item)) {
                    const [itemGx, itemGy] = this.currentArea.getRelativeCoordinates(item.coordinates);
                    output += `  - ${item.name} at (${Math.floor(itemGx)}, ${Math.floor(itemGy)})\n`;
                }
            });
        }
        
        // Display other NPCs in the area
        if (this.currentArea.npcs.length > 0) {
            output += "Other people in the area:\n";
            this.currentArea.npcs.forEach(npc => {
                if (!npcsHere.includes(npc)) {
                    const [npcGx, npcGy] = this.currentArea.getRelativeCoordinates(npc.coordinates);
                    output += `  - ${npc.name} at (${Math.floor(npcGx)}, ${Math.floor(npcGy)})\n`;
                }
            });
        }
        
        // Display area connections
        if (Object.keys(this.currentArea.connections).length > 0) {
            output += "Exits:\n";
            for (const [direction, area] of Object.entries(this.currentArea.connections)) {
                output += `  - ${direction.charAt(0).toUpperCase() + direction.slice(1)}: to ${area.name}\n`;
            }
        }
        output += "---\n";
        
        // Display items for sale if this area is a shop
        if (this.currentArea.shopStock) {
            output += "Items for sale here:\n";
            this.currentArea.getShopListing().forEach(line => {
                output += `  ${line}\n`;
            });
        }
        
        this.displayMessage(output);
    }

    move(direction) {
        if (!this.currentArea) {
            this.displayMessage("You can't move, you're not in any area.");
            return;
        }
        
        const [gridX, gridY] = this.getGridPosition();
        let newGridX = gridX;
        let newGridY = gridY;
        let movedWithinArea = false;
        
        if (direction === "north") newGridY += 1;
        else if (direction === "south") newGridY -= 1;
        else if (direction === "east") newGridX += 1;
        else if (direction === "west") newGridX -= 1;
        else {
            // Check for area connection by direction name
            if (direction in this.currentArea.connections) {
                // Moving to a new area
                this.setCurrentArea(this.currentArea.connections[direction]);
                return;
            }
            this.displayMessage(`Unknown direction: ${direction}. Try north, south, east, west, or an exit name.`);
            return;
        }
        
        if (this.currentArea.isValidGridPosition(newGridX, newGridY)) {
            this.coordinates = this.currentArea.getGlobalCoordinates(newGridX, newGridY);
            this.displayMessage(`You move ${direction}.`);
            movedWithinArea = true;
        } else if (direction in this.currentArea.connections) {
            // Edge of grid, try to use connection
            this.setCurrentArea(this.currentArea.connections[direction]);
            return;
        } else {
            this.displayMessage("You can't go that way.");
            return;
        }
        
        if (movedWithinArea) {
            // Check what's at the new location for a concise update
            const [currentGx, currentGy] = this.getGridPosition();
            const objectsHere = this.currentArea.getObjectsAtGridCell(currentGx, currentGy);
            const itemsHere = objectsHere.filter(obj => obj instanceof Item);
            const npcsHere = objectsHere.filter(obj => obj instanceof NPC);
            const otherInteractiveObjectsHere = objectsHere.filter(obj => !(obj instanceof Item) && !(obj instanceof NPC));
            
            let foundSomethingNotable = false;
            if (itemsHere.length > 0) {
                const itemNames = itemsHere.map(item => item.name).join(", ");
                this.displayMessage(`You notice ${itemNames} on the ground here.`);
                foundSomethingNotable = true;
            }
            
            if (npcsHere.length > 0) {
                const npcNames = npcsHere.map(npc => npc.name).join(", ");
                this.displayMessage(`${npcNames} ${npcsHere.length === 1 ? 'is' : 'are'} here.`);
                foundSomethingNotable = true;
            }
            
            if (otherInteractiveObjectsHere.length > 0) {
                const objectNames = otherInteractiveObjectsHere.map(obj => obj.name).join(", ");
                this.displayMessage(`There is a ${objectNames} here.`);
                foundSomethingNotable = true;
            }
        }
    }

    teleport(targetArea, gridX = null, gridY = null) {
        if (!targetArea) {
            this.displayMessage("Teleport target area not found.");
            return;
        }
        this.displayMessage(`Teleporting to ${targetArea.name}${gridX !== null && gridY !== null ? ` at coordinates (${gridX}, ${gridY})` : ''}...`);
        this.setCurrentArea(targetArea, gridX, gridY);
    }

    addItem(item) {
        this.inventory.push(item);
        item.coordinates = null; // Item is no longer in the world
        this.displayMessage(`You picked up ${item.name}.`);
    }

    removeItem(itemName) {
        const itemToDrop = this.inventory.find(item => item.name.toLowerCase() === itemName.toLowerCase());
        
        if (itemToDrop) {
            this.inventory = this.inventory.filter(item => item !== itemToDrop);
            this.displayMessage(`You dropped ${itemToDrop.name}.`);
            
            if (this.currentArea) {
                const [playerGx, playerGy] = this.getGridPosition();
                this.currentArea.addObjectToGrid(itemToDrop, playerGx, playerGy);
            }
        } else {
            this.displayMessage(`You don't have '${itemName}' in your inventory.`);
        }
    }

    pickUp(itemName) {
        if (!this.currentArea) {
            this.displayMessage("You are not in an area to pick up items from.");
            return;
        }
        
        const [playerGx, playerGy] = this.getGridPosition();
        const objectsAtPlayer = this.currentArea.getObjectsAtGridCell(playerGx, playerGy);
        
        const itemToPickup = objectsAtPlayer.find(obj => 
            obj instanceof Item && 
            obj.name.toLowerCase() === itemName.toLowerCase() &&
            obj.pickupable
        );
        
        if (itemToPickup) {
            this.currentArea.removeObjectFromGrid(itemToPickup, playerGx, playerGy);
            this.addItem(itemToPickup);
        } else {
            const nonPickupableItem = objectsAtPlayer.find(obj => 
                obj instanceof Item && 
                obj.name.toLowerCase() === itemName.toLowerCase() &&
                !obj.pickupable
            );
            
            if (nonPickupableItem) {
                this.displayMessage(`You can't pick up ${nonPickupableItem.name}.`);
            } else {
                this.displayMessage(`You don't see '${itemName}' here to pick up.`);
            }
        }
    }

    showInventory() {
        if (this.inventory.length === 0) {
            this.displayMessage("Your inventory is empty.");
        } else {
            let output = "\nInventory:\n";
            this.inventory.forEach(item => {
                output += `  - ${item.name}\n`;
            });
            this.displayMessage(output);
        }
        this.displayMessage(`Money: $${this.money.toFixed(2)}`);
    }

    buyItem(itemNameQuery) {
        if (!this.currentArea) {
            this.displayMessage("You are not in any area to buy from.");
            return [false, null, 0, null];
        }
        
        if (!this.currentArea.shopStock) {
            this.displayMessage("This place doesn't seem to be selling anything.");
            return [false, null, 0, null];
        }
        
        const [itemInstance, price] = this.currentArea.processPurchase(itemNameQuery, this.money);
        
        if (itemInstance) {
            this.money -= price;
            this.addItem(itemInstance);
            this.displayMessage(`You paid $${price.toFixed(2)}. Your money: $${this.money.toFixed(2)}`);
            return [true, itemInstance, price, this.currentArea.associatedStockSymbol];
        } else {
            const details = this.currentArea.shopStock[itemNameQuery.toLowerCase()];
            if (!details) {
                this.displayMessage(`The shop doesn't have '${itemNameQuery}'.`);
            } else if (details.stock <= 0) {
                this.displayMessage(`'${itemNameQuery}' is out of stock.`);
            } else if (this.money < details.price) {
                this.displayMessage(`You can't afford '${itemNameQuery}'. It costs $${details.price.toFixed(2)}, you have $${this.money.toFixed(2)}.`);
            }
            return [false, null, 0, null];
        }
    }

    viewPortfolio() {
        if (Object.keys(this.stockPortfolio).length === 0) {
            this.displayMessage("Your stock portfolio is empty.");
            return;
        }
        
        let output = "\n--- Your Stock Portfolio ---\n";
        for (const [symbol, data] of Object.entries(this.stockPortfolio)) {
            output += `  ${symbol}: ${data.shares} shares, Avg. Buy Price: $${data.avgPrice.toFixed(2)}\n`;
        }
        output += "--------------------------\n";
        this.displayMessage(output);
    }

    buyStock(symbol, shares, pricePerShare) {
        this.money -= shares * pricePerShare;
        
        if (symbol in this.stockPortfolio) {
            const currentShares = this.stockPortfolio[symbol].shares;
            const currentAvgPrice = this.stockPortfolio[symbol].avgPrice;
            const totalCostOld = currentShares * currentAvgPrice;
            const totalCostNewBatch = shares * pricePerShare;
            
            const newTotalShares = currentShares + shares;
            const newAvgPrice = (totalCostOld + totalCostNewBatch) / newTotalShares;
            
            this.stockPortfolio[symbol].shares = newTotalShares;
            this.stockPortfolio[symbol].avgPrice = newAvgPrice;
        } else {
            this.stockPortfolio[symbol] = { shares: shares, avgPrice: pricePerShare };
        }
        
        this.displayMessage(`Successfully bought ${shares} shares of ${symbol} at $${pricePerShare.toFixed(2)} each.`);
        this.displayMessage(`Remaining money: $${this.money.toFixed(2)}`);
        return true;
    }

    sellStock(symbol, sharesToSell, pricePerShare) {
        this.money += sharesToSell * pricePerShare;
        
        const avgBuyPrice = this.stockPortfolio[symbol].avgPrice;
        const profitLossPerShare = pricePerShare - avgBuyPrice;
        const totalProfitLoss = profitLossPerShare * sharesToSell;
        
        this.stockPortfolio[symbol].shares -= sharesToSell;
        
        // Remove stock from portfolio if all shares sold
        if (this.stockPortfolio[symbol].shares <= 0) {
            delete this.stockPortfolio[symbol];
        }
        
        this.displayMessage(`Successfully sold ${sharesToSell} shares of ${symbol} at $${pricePerShare.toFixed(2)} each.`);
        this.displayMessage(`${totalProfitLoss >= 0 ? 'Profit' : 'Loss'}: $${Math.abs(totalProfitLoss).toFixed(2)}`);
        this.displayMessage(`Remaining money: $${this.money.toFixed(2)}`);
        return true;
    }
}

class AreaManager {
    constructor() {
        this.areas = {};
    }

    addArea(area) {
        this.areas[area.id] = area;
    }

    getArea(areaNameQuery) {
        const query = areaNameQuery.toLowerCase();
        return Object.values(this.areas).find(area => 
            area.name.toLowerCase().includes(query)
        );
    }

    connectAreas(sourceAreaId, direction, targetAreaId) {
        const sourceArea = this.areas[sourceAreaId];
        const targetArea = this.areas[targetAreaId];
        
        if (!sourceArea || !targetArea) {
            console.error("Cannot connect areas: one or both areas not found");
            return false;
        }
        
        // Connect source to target
        sourceArea.connections[direction] = targetArea;
        
        // Connect target back to source (reverse direction)
        const reverseDirections = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east'
        };
        
        if (direction in reverseDirections) {
            targetArea.connections[reverseDirections[direction]] = sourceArea;
        }
        
        return true;
    }
}

// Game Manager
class GameManager {
    constructor() {
        // DOM elements
        this.outputArea = document.getElementById('output-area');
        this.commandInput = document.getElementById('command-input');
        this.submitButton = document.getElementById('submit-button');
        
        // Debug DOM elements
        console.log('Output area element:', this.outputArea);
        console.log('Command input element:', this.commandInput);
        console.log('Submit button element:', this.submitButton);
        
        // Create player with displayMessage callback
        this.player = new Player("Vita", 500, this.displayMessage.bind(this));
        this.areaManager = new AreaManager();
        this.npcs = [];
        this.computers = [];
        this.influenceSources = []; // New array for influence sources
        this.running = true;
        this.gameTurn = 0;
        this.inStockTerminalMode = false;
        this.currentComputer = null;
        this.stockMarketEnabled = true; // Enable stock market features
        this.stockUpdateFrequency = 5; // Update stocks every 5 turns
        
        this.ambientNoEventMessages = [
            "Time passes.",
            "The world is quiet for a moment.",
            "You take a breath; nothing remarkable happens right now.",
            "The air is still.",
            "A moment of calm."
        ];
        
        // Set up event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.submitButton.addEventListener('click', () => this.processInput());
        this.commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.processInput();
            }
        });
    }

    processInput() {
        console.log('processInput called');
        const commandInput = this.commandInput.value.trim();
        console.log('Command input:', commandInput);
        if (!commandInput) return;
        
        // Echo the command
        this.displayCommand(commandInput);
        
        // Clear the input field
        this.commandInput.value = '';
        
        // Process the command
        if (this.inStockTerminalMode) {
            this.processStockTerminalCommand(commandInput);
        } else {
            this.processCommand(commandInput);
            if (this.running) {
                this.updateWorld();
            }
        }
    }

    displayCommand(command) {
        const commandElement = document.createElement('p');
        commandElement.className = 'command-echo';
        commandElement.textContent = `> ${command}`;
        this.outputArea.appendChild(commandElement);
        this.outputArea.scrollTop = this.outputArea.scrollHeight;
    }

    displayMessage(message, className = 'game-message') {
        const lines = message.split('\n');
        lines.forEach(line => {
            if (line.trim()) {
                const messageElement = document.createElement('p');
                messageElement.className = className;
                messageElement.textContent = line;
                this.outputArea.appendChild(messageElement);
            }
        });
        this.outputArea.scrollTop = this.outputArea.scrollHeight;
    }

    displayErrorMessage(message) {
        this.displayMessage(message, 'error-message');
    }

    processCommand(commandInput) {
        const parts = commandInput.toLowerCase().split(' ');
        if (parts.length === 0) return;
        
        const action = parts[0];
        const args = parts.slice(1);
        
        if (['n', 'north', 's', 'south', 'e', 'east', 'w', 'west'].includes(action)) {
            const directionMap = { 'n': 'north', 's': 'south', 'e': 'east', 'w': 'west' };
            this.player.move(directionMap[action] || action);
        } else if (action === 'look' || action === 'l') {
            this.player.lookAround();
        } else if (action === 'inventory' || action === 'i') {
            this.player.showInventory();
        } else if (action === 'get' || action === 'take' || action === 'pickup') {
            if (args.length > 0) {
                this.player.pickUp(args.join(' '));
            } else {
                this.displayMessage("Pickup what?");
            }
        } else if (action === 'drop') {
            if (args.length > 0) {
                this.player.removeItem(args.join(' '));
            } else {
                this.displayMessage("Drop what?");
            }
        } else if (action === 'buy') {
            if (args.length > 0) {
                const itemToBuy = args.join(' ');
                const [success, boughtItem, price, stockSymbol] = this.player.buyItem(itemToBuy);
                if (success && stockSymbol) {
                    for (const computer of this.computers) {
                        if (computer.recordSaleForStock) {
                            computer.recordSaleForStock(stockSymbol, price);
                        }
                    }
                }
            } else {
                this.displayMessage("Buy what? (e.g., buy apple)");
            }
        } else if (action === 'interact') {
            if (args.length === 0) {
                this.displayMessage("Interact with what?");
                return;
            }
            
            const objectNameQuery = args.join(' ');
            const [playerGx, playerGy] = this.player.getGridPosition();
            
            // Check objects at player's current cell
            const objectsHere = this.player.currentArea.getObjectsAtGridCell(playerGx, playerGy);
            const targetObject = objectsHere.find(obj => 
                obj.name.toLowerCase().includes(objectNameQuery.toLowerCase()) && 
                obj.interact
            );
            
            if (targetObject) {
                this.currentComputer = targetObject;
                targetObject.interact(this.player);
            } else {
                this.displayMessage(`You don't see a '${objectNameQuery}' here to interact with.`);
            }
        } else if (action === 'teleport' || action === 'tp') {
            if (args.length === 0) {
                this.displayMessage("Teleport where? Usage: tp <area_name> [x] [y]");
                return;
            }
            
            let areaNameParts = [];
            let tpX = null, tpY = null;
            
            // Try to parse coordinates at the end
            if (args.length >= 2 && !isNaN(args[args.length-2]) && !isNaN(args[args.length-1])) {
                tpX = parseInt(args[args.length-2]);
                tpY = parseInt(args[args.length-1]);
                areaNameParts = args.slice(0, -2);
            } else if (args.length >= 1 && args[args.length-1].includes(',')) {
                const coords = args[args.length-1].split(',');
                if (coords.length === 2 && !isNaN(coords[0]) && !isNaN(coords[1])) {
                    tpX = parseInt(coords[0]);
                    tpY = parseInt(coords[1]);
                    areaNameParts = args.slice(0, -1);
                } else {
                    areaNameParts = args;
                }
            } else {
                areaNameParts = args;
            }
            
            const targetAreaName = areaNameParts.join(' ');
            let targetArea = this.areaManager.getArea(targetAreaName);
            
            if (!targetArea) {
                if (!areaNameParts.length && tpX !== null && tpY !== null && this.player.currentArea) {
                    targetArea = this.player.currentArea;
                } else {
                    this.displayMessage(`Area '${targetAreaName}' not found.`);
                    return;
                }
            }
            
            this.player.teleport(targetArea, tpX, tpY);
        } else if (action === 'scare') {
            if (!this.player.currentArea) {
                this.displayMessage("You shout into the void, but nothing happens.");
                return;
            }
            
            const npcsInArea = [...this.player.currentArea.npcs];
            if (npcsInArea.length === 0) {
                this.displayMessage("You try to look menacing, but there's no one here to scare.");
                return;
            }
            
            this.displayMessage("You let out a terrifying shout!");
            npcsInArea.forEach(npc => {
                if (npc.startFleeing) {
                    npc.startFleeing();
                }
            });
        } else if (action === 'birds' || action === 'summon_birds') {
            if (!this.player.currentArea) {
                this.displayMessage("You whistle, but you're in a void. No birds answer.");
                return;
            }
            
            const npcsInArea = [...this.player.currentArea.npcs];
            if (npcsInArea.length === 0) {
                this.displayMessage("You summon a flock of birds, but there's no one around to appreciate (or fear) them.");
                return;
            }
            
            this.displayMessage("With a sharp whistle, you summon a chaotic flock of birds!");
            this.displayMessage("They dive and circle, causing a ruckus!");
            
            npcsInArea.forEach(npc => {
                if (npc.startFleeing) {
                    npc.startFleeing(Math.floor(Math.random() * 4) + 4); // Birds scare for 4-7 turns
                }
            });
        } else if (action === 'where') {
            if (args.length > 0) {
                this.findEntityCoordinates(args.join(' '));
            } else {
                if (this.player.currentArea) {
                    const [gx, gy] = this.player.getGridPosition();
                    this.displayMessage(`You are in ${this.player.currentArea.name} at grid (${gx},${gy}). Global: ${this.player.coordinates}`);
                } else {
                    this.displayMessage("You are nowhere.");
                }
            }
        } else if (action === 'quit' || action === 'exit') {
            this.running = false;
            this.displayMessage("Thanks for playing Vita Game Hustle!");
        } else if (action === 'npcinfo') {
            if (args.length > 0) {
                const npcNameQuery = args.join(' ');
                this.showNpcInfo(npcNameQuery);
            } else {
                this.displayMessage("Usage: npcinfo <npc_name>");
            }
        } else if (action === 'help') {
            this.showHelp();
        } else {
            this.displayMessage(`Unknown command: ${action}`);
        }
    }

    processStockTerminalCommand(commandInput) {
        const parts = commandInput.toLowerCase().split(' ');
        if (parts.length === 0) return;
        
        const action = parts[0];
        
        if (action === 'exit') {
            this.exitStockTerminalMode();
            this.displayMessage("You step away from the terminal.");
        } else if (action === 'check' && parts[1] === 'stocks') {
            if (this.currentComputer) {
                this.displayMessage(this.currentComputer.getStockInfo());
            }
        } else if (action === 'buy' && parts.length === 3) {
            const symbol = parts[1].toUpperCase();
            const shares = parseInt(parts[2]);
            
            if (isNaN(shares) || shares <= 0) {
                this.displayMessage("Please enter a valid number of shares.");
                return;
            }
            
            if (this.currentComputer && this.currentComputer.stocks[symbol]) {
                const price = this.currentComputer.stocks[symbol].price;
                const totalCost = price * shares;
                
                if (totalCost > this.player.money) {
                    this.displayMessage(`You can't afford ${shares} shares of ${symbol} at $${price.toFixed(2)} each (total: $${totalCost.toFixed(2)}). You have $${this.player.money.toFixed(2)}.`);
                } else {
                    this.player.buyStock(symbol, shares, price);
                }
            } else {
                this.displayMessage(`Stock symbol '${symbol}' not found.`);
            }
        } else if (action === 'sell' && parts.length === 3) {
            const symbol = parts[1].toUpperCase();
            const shares = parseInt(parts[2]);
            
            if (isNaN(shares) || shares <= 0) {
                this.displayMessage("Please enter a valid number of shares.");
                return;
            }
            
            if (!(symbol in this.player.stockPortfolio)) {
                this.displayMessage(`You don't own any shares of ${symbol}.`);
                return;
            }
            
            if (shares > this.player.stockPortfolio[symbol].shares) {
                this.displayMessage(`You only have ${this.player.stockPortfolio[symbol].shares} shares of ${symbol}.`);
                return;
            }
            
            if (this.currentComputer && this.currentComputer.stocks[symbol]) {
                const price = this.currentComputer.stocks[symbol].price;
                this.player.sellStock(symbol, shares, price);
            } else {
                this.displayMessage(`Stock symbol '${symbol}' not found in market.`);
            }
        } else if (action === 'portfolio') {
            this.player.viewPortfolio();
        } else if (action === 'help') {
            this.displayMessage("Stock Terminal Commands:\n- check stocks: View current stock prices\n- buy [symbol] [shares]: Buy shares of a stock\n- sell [symbol] [shares]: Sell shares of a stock\n- portfolio: View your stock portfolio\n- exit: Exit the terminal");
        } else {
            this.displayMessage(`Unknown terminal command: ${action}`);
        }
    }

    enterStockTerminalMode() {
        this.inStockTerminalMode = true;
    }

    exitStockTerminalMode() {
        this.inStockTerminalMode = false;
        this.currentComputer = null;
    }

    showNpcInfo(npcNameQuery) {
        const npc = this.npcs.find(n => n.name.toLowerCase().includes(npcNameQuery.toLowerCase()));
        if (npc) {
            this.displayMessage(npc.getStatusInfo(this.gameTurn));
        } else {
            this.displayMessage(`NPC '${npcNameQuery}' not found.`);
        }
    }

    findEntityCoordinates(entityNameQuery) {
        const query = entityNameQuery.toLowerCase();
        let found = false;
        
        // Group items by name and area for better display
        const itemsByNameAndArea = {};
        
        for (const area of Object.values(this.areaManager.areas)) {
            // Check NPCs in area
            for (const npc of area.npcs) {
                if (npc.name.toLowerCase().includes(query)) {
                    const [npcGx, npcGy] = area.getRelativeCoordinates(npc.coordinates);
                    this.displayMessage(`NPC '${npc.name}' found in ${area.name} at grid (${Math.floor(npcGx)},${Math.floor(npcGy)}). Global: ${npc.coordinates}`);
                    found = true;
                }
            }
            
            // Check Items in area and group them
            for (const item of area.items) {
                if (item.name.toLowerCase().includes(query)) {
                    found = true;
                    
                    // Create a key for this item type and area
                    const key = `${item.name}|${area.name}`;
                    
                    if (!itemsByNameAndArea[key]) {
                        itemsByNameAndArea[key] = {
                            name: item.name,
                            area: area.name,
                            locations: []
                        };
                    }
                    
                    const [itemGx, itemGy] = area.getRelativeCoordinates(item.coordinates);
                    itemsByNameAndArea[key].locations.push({
                        grid: `(${Math.floor(itemGx)}, ${Math.floor(itemGy)})`,
                        global: item.coordinates.toString()
                    });
                }
            }
        }
        
        // Display grouped items
        for (const key in itemsByNameAndArea) {
            const itemGroup = itemsByNameAndArea[key];
            
            if (itemGroup.locations.length === 1) {
                // Single item
                const location = itemGroup.locations[0];
                this.displayMessage(`Item '${itemGroup.name}' found in ${itemGroup.area} at grid ${location.grid}. Global: ${location.global}`);
            } else {
                // Multiple items with same name
                this.displayMessage(`Found ${itemGroup.locations.length} '${itemGroup.name}' items in ${itemGroup.area}:`);
                itemGroup.locations.forEach((location, index) => {
                    this.displayMessage(`  ${index + 1}. At grid ${location.grid}. Global: ${location.global}`);
                });
            }
        }
        
        if (!found) {
            this.displayMessage(`No entity matching '${entityNameQuery}' found in any loaded area.`);
        }
    }

    updateWorld() {
        this.gameTurn++;
        
        // Apply influence sources to NPCs
        for (const npc of this.npcs) {
            npc.checkInfluences(this.influenceSources);
        }
        
        // Update NPCs
        const npcUpdates = [];
        for (const npc of this.npcs) {
            const updateResult = npc.update(this.gameTurn);
            if (updateResult) {
                if (typeof updateResult === 'string') {
                    npcUpdates.push({
                        npc: npc,
                        actionMessage: updateResult,
                        originalLocation: npc.location
                    });
                } else if (typeof updateResult === 'object') {
                    npcUpdates.push({
                        npc: npc,
                        actionMessage: updateResult.message,
                        purchaseInfo: updateResult.purchaseInfo,
                        originalLocation: npc.location
                    });
                }
            }
        }
        
        // Process NPC updates
        for (const update of npcUpdates) {
            // Only show messages for NPCs in the player's current area
            if (update.npc.location === this.player.currentArea || 
                update.originalLocation === this.player.currentArea) {
                
                if (update.actionMessage) {
                    this.displayMessage(update.actionMessage);
                }
                
                if (update.purchaseInfo && update.purchaseInfo.stockSymbol) {
                    for (const computer of this.computers) {
                        if (computer.recordSaleForStock) {
                            computer.recordSaleForStock(
                                update.purchaseInfo.stockSymbol,
                                update.purchaseInfo.price
                            );
                        }
                    }
                }
            }
        }
        
        // Update stock market periodically
        if (this.stockMarketEnabled && this.gameTurn % this.stockUpdateFrequency === 0) {
            this.updateStockMarket();
        }
        
        // Random ambient message (5% chance if no other messages)
        if (npcUpdates.length === 0 && Math.random() < 0.05) {
            const randomMessage = this.ambientNoEventMessages[
                Math.floor(Math.random() * this.ambientNoEventMessages.length)
            ];
            this.displayMessage(randomMessage);
        }
    }
    
    updateStockMarket() {
        for (const computer of this.computers) {
            if (!computer.stocks) continue;
            
            // Update each stock with some randomness
            for (const [symbol, data] of Object.entries(computer.stocks)) {
                // Base volatility
                const volatility = 0.05;
                
                // Random price change (-volatility to +volatility)
                const randomFactor = (Math.random() * 2 - 1) * volatility;
                
                // Adjust based on sales (more sales = higher price)
                const salesFactor = data.sales > 0 ? Math.min(0.03, data.sales / 1000) : 0;
                
                // Calculate new price
                const priceChange = data.price * (randomFactor + salesFactor);
                data.price += priceChange;
                
                // Ensure price doesn't go below 1.00
                data.price = Math.max(1.00, data.price);
                
                // Add to history
                data.history.push(data.price);
                if (data.history.length > 20) {
                    data.history.shift();
                }
                
                // Reset sales counter
                data.sales = 0;
            }
            
            // If player is using this computer, show updated prices
            if (this.inStockTerminalMode && this.currentComputer === computer) {
                this.displayMessage(computer.getStockInfo());
            }
        }
    }

    showHelp() {
        const helpText = `
Vita Game Hustle - Commands:
---------------------------
Movement:
  north, n - Move north
  south, s - Move south
  east, e - Move east
  west, w - Move west

Basic Actions:
  look, l - Look around your current location
  inventory, i - Check your inventory
  get/take/pickup [item] - Pick up an item
  drop [item] - Drop an item from your inventory
  buy [item] - Buy an item from a shop
  interact [object] - Interact with an object (like computers)

Special Abilities:
  scare - Frighten nearby NPCs
  birds, summon_birds - Summon birds to cause chaos

Information:
  where - Show your current location
  where [entity] - Find the location of an NPC or item
  npcinfo [npc] - Get detailed information about an NPC

Advanced:
  teleport/tp [area] [x] [y] - Teleport to a specific area and coordinates
  quit, exit - Exit the game

When using a computer terminal, different commands will be available.
`;
        this.displayMessage(helpText);
    }

    initializeGame() {
        this.displayMessage("Game Loading...");
        
        // Create Areas
        const parkOrigin = new Coordinates(0, 0, 0);
        const park = new Area("Central Park", "A grassy park with a few trees.", parkOrigin, 10, 10);
        this.areaManager.addArea(park);
        
        const shopOrigin = new Coordinates(20, 0, 0); // Shop is to the east of the park
        const shop = new Area("General Store", "A small store with various goods.", shopOrigin, 8, 8);
        shop.associatedStockSymbol = "MALL"; // Vita Mall Corp stock
        shop.isShelter = true; // The store is a shelter
        this.areaManager.addArea(shop);
        
        const gardenOrigin = new Coordinates(0, -20, 0); // Garden is south of the park
        const garden = new Area("Gray Bird Garden", "A serene, slightly unsettling garden. A large, smooth stone sits in the center.", gardenOrigin, 7, 7);
        this.areaManager.addArea(garden);
        
        // Connect Areas
        this.areaManager.connectAreas(park.id, "east", shop.id);
        this.areaManager.connectAreas(park.id, "south", garden.id);
        
        // Create Items
        const redBall = new Item("Red Ball", "A bouncy red ball.", 5);
        park.addObjectToGrid(redBall, 3, 3);
        
        const blueCube = new Item("Blue Cube", "A smooth blue cube.", 10);
        park.addObjectToGrid(blueCube, 3, 4);
        
        const greenPyramid = new Item("Green Pyramid", "A shiny green pyramid.", 15);
        park.addObjectToGrid(greenPyramid, 8, 8);
        
        // Place the first yellow star
        const yellowStar1 = new Item("Yellow Star", "A bright yellow star.", 0);
        park.addObjectToGrid(yellowStar1, 6, 6);
        console.log(`Yellow Star placed at (6, 6)`);
        
        // Place additional yellow stars at different coordinates
        const starPositions = [
            [5, 5],
            [4, 4],
            [3, 3],
            [2, 2],
            [1, 1]
        ];
        
        // Create a new instance for each star
        starPositions.forEach(([x, y]) => {
            const newStar = new Item("Yellow Star", "A bright yellow star.", 0);
            park.addObjectToGrid(newStar, x, y);
            console.log(`Yellow Star placed at (${x}, ${y})`);
        });
        
        // Stock the shop
        const shopApplePrototype = new Item("Apple", "A juicy red apple.", 2);
        shop.addItemToShop(shopApplePrototype, 3.00, 10); // Sell for $3
        
        const shopWaterPrototype = new Item("Bottled Water", "Clean drinking water.", 1);
        shop.addItemToShop(shopWaterPrototype, 1.50, Infinity); // Unlimited water
        
        // Create Influence Sources
        const appleAdvert = new InfluenceSource(
            "Shiny Apple Poster",
            "A vibrant poster exclaiming 'An Apple a Day Keeps the Doctor Away! Buy Apples!'",
            "buy",
            4,
            0.75
        ).setTargetItem("Apple");
        
        appleAdvert.coordinates = park.getGlobalCoordinates(7, 7);
        appleAdvert.location = park;
        park.addObjectToGrid(appleAdvert, 7, 7);
        this.influenceSources.push(appleAdvert);
        
        const offeringWhisper = new InfluenceSource(
            "Mysterious Whisper Stone",
            "A faint, almost inaudible whisper seems to emanate from this oddly smooth stone, urging devotion.",
            "deliver",
            5,
            0.60
        ).setDeliveryDetails(
            "Yellow Star", 
            "Gray Bird Garden", 
            { x: Math.floor(garden.gridWidth / 2), y: Math.floor(garden.gridLength / 2) }
        );
        
        offeringWhisper.coordinates = park.getGlobalCoordinates(2, 8);
        offeringWhisper.location = park;
        park.addObjectToGrid(offeringWhisper, 2, 8);
        this.influenceSources.push(offeringWhisper);
        
        // Add a "move to shop" influence
        const shopSign = new InfluenceSource(
            "Shop poster",
            "A poster hung on a tree, promoting the general store.",
            "move",
            6,
            0.65
        ).setTargetArea("General Store");
        
        shopSign.coordinates = park.getGlobalCoordinates(9, 5);
        shopSign.location = park;
        park.addObjectToGrid(shopSign, 9, 5);
        this.influenceSources.push(shopSign);
        
        // Create NPCs
        const roboCoords = park.getGlobalCoordinates(3, 2);
        const robo = new NPC("Robo", "A small, curious robot.", roboCoords, park, 25);
        const shinyTrinket = new Item("Shiny Trinket", "A small, glittering object.");
        robo.addItemToInventory(shinyTrinket);
        park.addObjectToGrid(robo, 3, 2);
        this.npcs.push(robo);
        
        const zippyCoords = park.getGlobalCoordinates(1, 8);
        const zippy = new NPC("Zippy", "A fast-moving drone.", zippyCoords, park, 10);
        park.addObjectToGrid(zippy, 1, 8);
        this.npcs.push(zippy);
        
        const gusGusCoords = park.getGlobalCoordinates(5, 5);
        const gusGus = new NPC("Gus-Gus", "A robotic cow.", gusGusCoords, park, 50);
        park.addObjectToGrid(gusGus, 5, 5);
        this.npcs.push(gusGus);
        
        const abertathurCoords = park.getGlobalCoordinates(6, 5);
        const abertathur = new NPC("Abertathur", "An old genie.", abertathurCoords, park, 75);
        park.addObjectToGrid(abertathur, 6, 5);
        this.npcs.push(abertathur);
        
        // Create and place a Computer
        const stockComputer = new Computer("Stock Terminal", "A terminal for trading stocks.");
        shop.addObjectToGrid(stockComputer, 1, 1);
        this.computers.push(stockComputer);
        
        // Place Player
        this.player.setCurrentArea(park, 1, 1);
        
        this.displayMessage("Game loaded.");
    }

    start() {
        this.displayMessage("Welcome to Vita Game Hustle - Web Edition!");
        this.displayMessage("Type 'help' for a list of commands.");
        this.initializeGame();
        
        // Only describe the world once after everything is loaded
        this.player.lookAround();
    }
}

// Initialize and start the game when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded, initializing game...');
    const game = new GameManager();
    game.start();
});