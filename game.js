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
        this.actionType = actionType;
        this.influenceRadius = influenceRadius;
        this.influenceStrength = influenceStrength;
        
        // Additional properties based on action type
        this.targetItemName = null;
        this.deliveryItemName = null;
        this.deliveryTargetAreaName = null;
        this.deliveryTargetCoords = null;
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
    }

    addItemToInventory(item) {
        this.inventory.push(item);
    }

    startFleeing(duration = 3) {
        this.isFleeing = true;
        this.fleeingDuration = duration;
        return `${this.name} starts running away in panic!`;
    }

    update(gameTurn) {
        // Skip if already acted this turn
        if (this.lastActionTurn === gameTurn) return null;
        
        this.lastActionTurn = gameTurn;
        
        // Handle fleeing behavior
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
        
        // Random actions when not fleeing (30% chance to do something)
        if (Math.random() < 0.3) {
            const actions = [
                this.randomMove.bind(this),
                this.lookAtItems.bind(this),
                this.considerBuying.bind(this)
            ];
            
            const randomAction = actions[Math.floor(Math.random() * actions.length)];
            return randomAction();
        }
        
        return null; // No action this turn
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

    considerBuying() {
        if (!this.location || !this.location.shopStock || this.money <= 0) return null;
        
        // Check if there are items for sale
        const affordableItems = Object.entries(this.location.shopStock)
            .filter(([_, details]) => details.price <= this.money && details.stock > 0);
        
        if (affordableItems.length > 0) {
            // Randomly decide whether to buy
            if (Math.random() < 0.4) {
                const [itemName, details] = affordableItems[Math.floor(Math.random() * affordableItems.length)];
                
                // Buy the item
                this.money -= details.price;
                const boughtItem = new Item(details.prototype.name, details.prototype.description, details.prototype.value);
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
        
        if (this.isFleeing) {
            info += `Status: Fleeing (${this.fleeingDuration} turns remaining)\n`;
        }
        
        if (this.inventory.length > 0) {
            info += "Inventory:\n";
            this.inventory.forEach(item => {
                info += `  - ${item.name}\n`;
            });
        } else {
            info += "Inventory: Empty\n";
        }
        
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
            this.lookAround();
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
        this.running = true;
        this.gameTurn = 0;
        this.inStockTerminalMode = false;
        this.currentComputer = null;
        
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
        
        for (const area of Object.values(this.areaManager.areas)) {
            // Check NPCs in area
            for (const npc of area.npcs) {
                if (npc.name.toLowerCase().includes(query)) {
                    const [npcGx, npcGy] = area.getRelativeCoordinates(npc.coordinates);
                    this.displayMessage(`NPC '${npc.name}' found in ${area.name} at grid (${Math.floor(npcGx)},${Math.floor(npcGy)}). Global: ${npc.coordinates}`);
                    found = true;
                }
            }
            
            // Check Items in area
            for (const item of area.items) {
                if (item.name.toLowerCase().includes(query)) {
                    const [itemGx, itemGy] = area.getRelativeCoordinates(item.coordinates);
                    this.displayMessage(`Item '${item.name}' found in ${area.name} at grid (${Math.floor(itemGx)},${Math.floor(itemGy)}). Global: ${item.coordinates}`);
                    found = true;
                }
            }
        }
        
        if (!found) {
            this.displayMessage(`No entity matching '${entityNameQuery}' found in any loaded area.`);
        }
    }

    updateWorld() {
        this.gameTurn++;
        
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
        this.displayMessage("Initializing game world...");
        
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
        
        const yellowStar = new Item("Yellow Star", "A bright yellow star.", 0);
        park.addObjectToGrid(yellowStar, 6, 6);
        
        let ysx = 6;
        let ysy = 6;
        for (let i = 0; i < 5; i++) {
            ysx--;
            ysy--;
            park.addObjectToGrid(yellowStar, ysx, ysy);
            console.log(`Yellow Star placed at (${ysx}, ${ysy})`);
        }
        
        // Stock the shop
        const shopApplePrototype = new Item("Apple", "A juicy red apple.", 2);
        shop.addItemToShop(shopApplePrototype, 3.00, 10); // Sell for $3
        
        const shopWaterPrototype = new Item("Bottled Water", "Clean drinking water.", 1);
        shop.addItemToShop(shopWaterPrototype, 1.50, Infinity); // Unlimited water
        
        // Create Influence Sources
        const appleAdvert = new InfluenceSource(
            "Shiny Apple Poster",
            "A vibrant poster exclaiming 'An Apple a Day Keeps the Doctor Away! Buy Apples!'",
            "shop",
            4,
            0.75
        );
        appleAdvert.targetItemName = "Apple";
        park.addObjectToGrid(appleAdvert, 7, 7);
        
        const offeringWhisper = new InfluenceSource(
            "Mysterious Whisper Stone",
            "A faint, almost inaudible whisper seems to emanate from this oddly smooth stone, urging devotion.",
            "deliver_item",
            5,
            0.60
        );
        offeringWhisper.deliveryItemName = "Yellow Star";
        offeringWhisper.deliveryTargetAreaName = "Gray Bird Garden";
        offeringWhisper.deliveryTargetCoords = [Math.floor(garden.gridWidth / 2), Math.floor(garden.gridLength / 2)];
        park.addObjectToGrid(offeringWhisper, 2, 8);
        
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
        
        this.displayMessage("Game initialized.");
        this.player.lookAround();
    }

    start() {
        this.displayMessage("Welcome to Vita Game Hustle - Web Edition!");
        this.displayMessage("Type 'help' for a list of commands.");
        this.initializeGame();
    }
}

// Initialize and start the game when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded, initializing game...');
    const game = new GameManager();
    game.start();
});