/**
 * Vita Game - Web Version
 * A text-based adventure game inspired by Goat Simulator
 */

// Game state
const gameState = {
    initialized: false,
    player: null,
    currentArea: null,
    areas: {},
    npcs: {},
    items: {},
    objects: {},
    quests: {},
    outputHistory: []
};

// Classes that mirror the Python implementation
class Coordinates {
    constructor(x = 0, y = 0, z = 0) {
        this.x = x;  // East-West position
        this.y = y;  // North-South position
        this.z = z;  // Height/Elevation
    }
    
    toString() {
        return `(${this.x}, ${this.y}, ${this.z})`;
    }
    
    distanceTo(otherCoords) {
        return Math.sqrt(Math.pow(this.x - otherCoords.x, 2) + Math.pow(this.y - otherCoords.y, 2));
    }
    
    heightDifference(otherCoords) {
        return Math.abs(this.z - otherCoords.z);
    }
}

class Item {
    constructor(name, description, coordinates = null, edible = false, nutrition = 0) {
        this.name = name;
        this.description = description;
        this.coordinates = coordinates || new Coordinates(0, 0, 0);
        this.edible = edible;
        this.nutrition = nutrition;
    }
    
    toString() {
        return this.name;
    }
    
    use(player) {
        return `You use the ${this.name}.`;
    }
}

class Food extends Item {
    constructor(name, description, nutrition = 10, effect = null) {
        super(name, description, null, true, nutrition);
        this.effectFunction = effect;
    }
    
    effect(player) {
        if (this.effectFunction) {
            return this.effectFunction(player);
        }
        return null;
    }
}

class Jetpack extends Item {
    constructor() {
        super("Jetpack", "A high-tech jetpack that allows you to fly.");
        this.fuel = 100;
        this.maxFuel = 100;
    }
    
    activate(player) {
        if (this.fuel > 0) {
            player.isFlying = true;
            return true;
        }
        return false;
    }
    
    refuel(amount = 100) {
        this.fuel = Math.min(this.maxFuel, this.fuel + amount);
        return `Jetpack refueled to ${this.fuel}%`;
    }
    
    toString() {
        return `${this.name} (Fuel: ${this.fuel}%)`;
    }
}

class Player {
    constructor() {
        this.name = "Vita";
        this.streetCred = 0;
        this.inventory = [];
        this.currentArea = null;
        this.coordinates = new Coordinates(0, 0, 0);
        this.jetpack = null;
        this.isFlying = false;
        this.energy = 100;
        this.maxEnergy = 100;
        this.hunger = 0;
    }
    
    setCurrentArea(area, gridX = 0, gridY = 0) {
        this.currentArea = area;
        // Update player coordinates to match area entrance coordinates plus grid position
        this.coordinates = new Coordinates(
            area.coordinates.x + gridX,
            area.coordinates.y + gridY,
            area.coordinates.z
        );
        
        // Use simplified look for initial area description
        return this.simpleLook();
    }
    
    simpleLook() {
        const output = [];
        
        // Basic area information
        output.push(`You are now in ${this.currentArea.name}. ${this.currentArea.description}`);
        
        // Get current grid position
        const [gridX, gridY, gridZ] = this.getGridPosition();
        output.push(`You are at position (${gridX}, ${gridY}) in ${this.currentArea.name}.`);
        
        // Display available directions for movement within the grid
        output.push("You can move:");
        if (gridY < this.currentArea.gridLength - 1) {
            output.push("- north/forward");
        }
        if (gridY > 0) {
            output.push("- south/backward");
        }
        if (gridX < this.currentArea.gridWidth - 1) {
            output.push("- east/right");
        }
        if (gridX > 0) {
            output.push("- west/left");
        }
        
        // Display area connections (exits to other areas)
        if (Object.keys(this.currentArea.connections).length > 0) {
            output.push("Area exits:");
            for (const [direction, area] of Object.entries(this.currentArea.connections)) {
                output.push(`- ${direction} to ${area.name}`);
            }
        }
        
        // Add a hint to use 'look' for more details
        output.push("\nType 'look' to see more details about your surroundings.");
        
        return output;
    }
    
    lookAround() {
        const output = [];
        
        // Get current grid position
        const [gridX, gridY, gridZ] = this.getGridPosition();
        output.push(`You are at position (${gridX}, ${gridY}) in ${this.currentArea.name}.`);
        
        // Display available directions for movement within the grid
        output.push("You can move:");
        if (gridY < this.currentArea.gridLength - 1) {
            output.push("- north/forward");
        }
        if (gridY > 0) {
            output.push("- south/backward");
        }
        if (gridX < this.currentArea.gridWidth - 1) {
            output.push("- east/right");
        }
        if (gridX > 0) {
            output.push("- west/left");
        }
        
        // Display area connections (exits to other areas)
        if (Object.keys(this.currentArea.connections).length > 0) {
            output.push("Area exits:");
            for (const [direction, area] of Object.entries(this.currentArea.connections)) {
                output.push(`- ${direction} to ${area.name}`);
            }
        }
        
        // Display objects at the current position
        const objectsHere = this.currentArea.getObjectsAt(gridX, gridY, gridZ);
        if (objectsHere.length > 0) {
            output.push("At your position:");
            for (const obj of objectsHere) {
                output.push(`- ${obj.name}: ${obj.description}`);
            }
        }
        
        // Display items in the area
        if (this.currentArea.items.length > 0) {
            output.push("Items in this area:");
            for (const item of this.currentArea.items) {
                // Get the relative position of the item
                const itemRelX = item.coordinates.x - this.currentArea.coordinates.x;
                const itemRelY = item.coordinates.y - this.currentArea.coordinates.y;
                // Only show items that are visible (in the same area)
                if (0 <= itemRelX && itemRelX < this.currentArea.gridWidth && 
                    0 <= itemRelY && itemRelY < this.currentArea.gridLength) {
                    const direction = this.getRelativeDirection(gridX, gridY, itemRelX, itemRelY);
                    output.push(`- ${item.name}: ${item.description} (${direction})`);
                }
            }
        }
        
        // Display NPCs in the area
        if (this.currentArea.npcs.length > 0) {
            output.push("People in this area:");
            for (const npc of this.currentArea.npcs) {
                // Get the relative position of the NPC
                const npcRelX = npc.coordinates.x - this.currentArea.coordinates.x;
                const npcRelY = npc.coordinates.y - this.currentArea.coordinates.y;
                // Only show NPCs that are visible (in the same area)
                if (0 <= npcRelX && npcRelX < this.currentArea.gridWidth && 
                    0 <= npcRelY && npcRelY < this.currentArea.gridLength) {
                    const direction = this.getRelativeDirection(gridX, gridY, npcRelX, npcRelY);
                    output.push(`- ${npc.name}: ${npc.description} (${direction})`);
                }
            }
        }
        
        // Display objects in the area
        if (this.currentArea.objects.length > 0) {
            output.push("Objects in this area:");
            for (const obj of this.currentArea.objects) {
                // Get the relative position of the object
                const objRelX = obj.coordinates.x - this.currentArea.coordinates.x;
                const objRelY = obj.coordinates.y - this.currentArea.coordinates.y;
                // Only show objects that are visible (in the same area)
                if (0 <= objRelX && objRelX < this.currentArea.gridWidth && 
                    0 <= objRelY && objRelY < this.currentArea.gridLength) {
                    // Skip objects at the current position (already displayed above)
                    if (objRelX === gridX && objRelY === gridY) {
                        continue;
                    }
                    const direction = this.getRelativeDirection(gridX, gridY, objRelX, objRelY);
                    output.push(`- ${obj.name}: ${obj.description} (${direction})`);
                }
            }
        }
        
        return output;
    }
    
    getRelativeDirection(fromX, fromY, toX, toY) {
        if (fromX === toX && fromY === toY) {
            return "here";
        }
        
        const directions = [];
        if (toY > fromY) {
            directions.push("north");
        } else if (toY < fromY) {
            directions.push("south");
        }
        
        if (toX > fromX) {
            directions.push("east");
        } else if (toX < fromX) {
            directions.push("west");
        }
        
        const distance = Math.floor(Math.sqrt(Math.pow(toX - fromX, 2) + Math.pow(toY - fromY, 2)));
        let proximity;
        if (distance === 1) {
            proximity = "adjacent";
        } else if (distance <= 3) {
            proximity = "nearby";
        } else {
            proximity = "in the distance";
        }
        
        return `${directions.join(' ')} ${proximity}`;
    }
    
    addItem(item) {
        this.inventory.push(item);
        const output = [`You have picked up ${item.name}.`];
        
        // Special handling for jetpack
        if (item.name.toLowerCase() === "jetpack") {
            this.jetpack = item;
            output.push("You can now fly by activating your jetpack!");
        }
        
        return output;
    }
    
    removeItem(itemName) {
        const item = this.inventory.find(i => i.name.toLowerCase() === itemName.toLowerCase());
        if (item) {
            this.inventory = this.inventory.filter(i => i !== item);
            const output = [`You have dropped ${item.name}.`];
            
            // Special handling for jetpack
            if (item.name.toLowerCase() === "jetpack" && this.jetpack === item) {
                this.jetpack = null;
                this.isFlying = false;
                output.push("You can no longer fly without your jetpack!");
            }
            
            // Add the item to the current area
            if (this.currentArea) {
                this.currentArea.addItem(item);
            }
            
            return output;
        } else {
            return [`You don't have ${itemName} in your inventory.`];
        }
    }
    
    activateJetpack() {
        if (!this.jetpack) {
            return ["You don't have a jetpack!"];
        }
        
        if (this.jetpack.fuel <= 0) {
            return ["Your jetpack is out of fuel!"];
        }
        
        this.isFlying = true;
        return ["Whoosh! Your jetpack activates and you start flying!"];
    }
    
    deactivateJetpack() {
        if (this.isFlying) {
            this.isFlying = false;
            // Make sure player is at ground level of current area
            this.coordinates.z = this.currentArea.coordinates.z;
            return ["You deactivate your jetpack and land gently."];
        }
        return ["Your jetpack is not active."];
    }
    
    fly(direction, distance = 1) {
        if (!this.isFlying) {
            return ["You need to activate your jetpack first!"];
        }
        
        if (this.jetpack.fuel <= 0) {
            this.isFlying = false;
            return ["Your jetpack runs out of fuel!"];
        }
        
        // Consume fuel
        this.jetpack.fuel -= distance;
        if (this.jetpack.fuel < 0) {
            this.jetpack.fuel = 0;
        }
        
        // Get current grid position
        const [gridX, gridY, gridZ] = this.getGridPosition();
        let newX = gridX, newY = gridY, newZ = gridZ;
        
        const output = [];
        
        // Move in the specified direction
        direction = direction.toLowerCase();
        if (direction === "up") {
            newZ += distance;
            output.push(`You fly upward to elevation ${this.currentArea.coordinates.z + newZ}.`);
        } else if (direction === "down") {
            if (gridZ - distance < 0) {
                // Don't go below ground level
                newZ = 0;
                output.push("You descend to ground level.");
            } else {
                newZ -= distance;
                output.push(`You fly downward to elevation ${this.currentArea.coordinates.z + newZ}.`);
            }
        } else if (direction === "north" || direction === "forward") {
            newY += distance;
            output.push("You fly north.");
        } else if (direction === "south" || direction === "backward") {
            newY -= distance;
            output.push("You fly south.");
        } else if (direction === "east" || direction === "right") {
            newX += distance;
            output.push("You fly east.");
        } else if (direction === "west" || direction === "left") {
            newX -= distance;
            output.push("You fly west.");
        } 
        // Handle diagonal directions
        else if (direction === "northeast") {
            newX += distance;
            newY += distance;
            output.push("You fly northeast.");
        } else if (direction === "northwest") {
            newX -= distance;
            newY += distance;
            output.push("You fly northwest.");
        } else if (direction === "southeast") {
            newX += distance;
            newY -= distance;
            output.push("You fly southeast.");
        } else if (direction === "southwest") {
            newX -= distance;
            newY -= distance;
            output.push("You fly southwest.");
        } else {
            return [`Unknown direction: ${direction}`];
        }
        
        // Check if new position is within area bounds
        if (0 <= newX && newX < this.currentArea.gridWidth && 
            0 <= newY && newY < this.currentArea.gridLength) {
            // Update player coordinates
            this.coordinates.x = this.currentArea.coordinates.x + newX;
            this.coordinates.y = this.currentArea.coordinates.y + newY;
            this.coordinates.z = this.currentArea.coordinates.z + newZ;
            
            // Check for objects at the new position
            const objectsHere = this.currentArea.getObjectsAt(newX, newY, newZ);
            if (objectsHere.length > 0) {
                output.push("You see:");
                for (const obj of objectsHere) {
                    output.push(`- ${obj.name}: ${obj.description}`);
                }
            }
            
            return output;
        } else {
            // Check if there's a connection in this direction
            if (direction in this.currentArea.connections) {
                const connectedArea = this.currentArea.connections[direction];
                // Determine entry point on the other side
                let entryX = 0, entryY = 0;
                if (direction === "north") {
                    entryY = 0;  // Enter from the south side
                    entryX = gridX;  // Keep the same x-coordinate
                } else if (direction === "south") {
                    entryY = connectedArea.gridLength - 1;  // Enter from the north side
                    entryX = gridX;  // Keep the same x-coordinate
                } else if (direction === "east") {
                    entryX = 0;  // Enter from the west side
                    entryY = gridY;  // Keep the same y-coordinate
                } else if (direction === "west") {
                    entryX = connectedArea.gridWidth - 1;  // Enter from the east side
                    entryY = gridY;  // Keep the same y-coordinate
                }
                
                // Move to the connected area
                const areaOutput = this.setCurrentArea(connectedArea, entryX, entryY);
                // Maintain flying elevation
                this.coordinates.z = connectedArea.coordinates.z + gridZ;
                
                return output.concat(areaOutput);
            } else {
                return [`You can't fly ${direction} from here. You've reached the edge of ${this.currentArea.name}.`];
            }
        }
    }
    
    eat(itemName) {
        const item = this.inventory.find(i => i.name.toLowerCase() === itemName.toLowerCase());
        if (!item) {
            return [`You don't have ${itemName} to eat.`];
        }
        
        if (item.edible) {
            this.hunger = Math.max(0, this.hunger - item.nutrition);
            this.inventory = this.inventory.filter(i => i !== item);
            
            const output = [`You eat the ${item.name}. Yum!`];
            
            if (typeof item.effect === 'function') {
                const effectResult = item.effect(this);
                if (effectResult) {
                    output.push(effectResult);
                }
            }
            
            return output;
        } else {
            return [`You can't eat the ${item.name}!`];
        }
    }
    
    getGridPosition() {
        if (!this.currentArea) {
            return [0, 0, 0];
        }
        
        const relX = this.coordinates.x - this.currentArea.coordinates.x;
        const relY = this.coordinates.y - this.currentArea.coordinates.y;
        const relZ = this.coordinates.z - this.currentArea.coordinates.z;
        
        return [relX, relY, relZ];
    }
    
    move(direction, distance = 1) {
        if (!this.currentArea) {
            return ["You're not in any area."];
        }
        
        // Get current grid position
        const [gridX, gridY, gridZ] = this.getGridPosition();
        let newX = gridX, newY = gridY;
        
        // Calculate new position based on direction
        direction = direction.toLowerCase();
        
        // Handle vertical movement first
        if (direction === "up") {
            if (this.isFlying) {
                return this.fly("up", distance);
            } else {
                return ["You need to activate your jetpack to go up."];
            }
        } else if (direction === "down") {
            if (this.isFlying) {
                return this.fly("down", distance);
            } else if (gridZ > 0) {
                // If player is somehow elevated without flying
                this.coordinates.z = this.currentArea.coordinates.z;
                return ["You move down to ground level."];
            } else {
                return ["You're already at ground level."];
            }
        }
        
        // Handle cardinal directions
        if (direction === "north" || direction === "forward") {
            newY += distance;
        } else if (direction === "south" || direction === "backward") {
            newY -= distance;
        } else if (direction === "east" || direction === "right") {
            newX += distance;
        } else if (direction === "west" || direction === "left") {
            newX -= distance;
        } 
        // Handle diagonal directions
        else if (direction === "northeast") {
            newX += distance;
            newY += distance;
        } else if (direction === "northwest") {
            newX -= distance;
            newY += distance;
        } else if (direction === "southeast") {
            newX += distance;
            newY -= distance;
        } else if (direction === "southwest") {
            newX -= distance;
            newY -= distance;
        } else {
            return [`Unknown direction: ${direction}`];
        }
        
        // Check if new position is within area bounds
        if (0 <= newX && newX < this.currentArea.gridWidth && 
            0 <= newY && newY < this.currentArea.gridLength) {
            // Update player coordinates
            this.coordinates.x = this.currentArea.coordinates.x + newX;
            this.coordinates.y = this.currentArea.coordinates.y + newY;
            
            const output = [`You move ${direction}.`];
            
            // Check for objects at the new position
            const objectsHere = this.currentArea.getObjectsAt(newX, newY, gridZ);
            if (objectsHere.length > 0) {
                output.push("You see:");
                for (const obj of objectsHere) {
                    output.push(`- ${obj.name}: ${obj.description}`);
                }
            }
            
            return output;
        } else {
            // Check if there's a connection in this direction
            if (direction in this.currentArea.connections) {
                const connectedArea = this.currentArea.connections[direction];
                
                // Check if player needs to fly to reach this area
                const heightDiff = connectedArea.coordinates.z - this.currentArea.coordinates.z;
                
                if (heightDiff > 0 && !this.isFlying) {
                    return [`You need to fly to reach ${connectedArea.name}. Try activating your jetpack first!`];
                } else {
                    // Determine entry point on the other side
                    let entryX = 0, entryY = 0;
                    if (direction === "north" || direction === "forward") {
                        entryY = 0;  // Enter from the south side
                        entryX = gridX;  // Keep the same x-coordinate
                    } else if (direction === "south" || direction === "backward") {
                        entryY = connectedArea.gridLength - 1;  // Enter from the north side
                        entryX = gridX;  // Keep the same x-coordinate
                    } else if (direction === "east" || direction === "right") {
                        entryX = 0;  // Enter from the west side
                        entryY = gridY;  // Keep the same y-coordinate
                    } else if (direction === "west" || direction === "left") {
                        entryX = connectedArea.gridWidth - 1;  // Enter from the east side
                        entryY = gridY;  // Keep the same y-coordinate
                    } else if (direction === "northeast") {
                        entryX = 0;  // Enter from the west side
                        entryY = 0;  // Enter from the south side
                    } else if (direction === "northwest") {
                        entryX = connectedArea.gridWidth - 1;  // Enter from the east side
                        entryY = 0;  // Enter from the south side
                    } else if (direction === "southeast") {
                        entryX = 0;  // Enter from the west side
                        entryY = connectedArea.gridLength - 1;  // Enter from the north side
                    } else if (direction === "southwest") {
                        entryX = connectedArea.gridWidth - 1;  // Enter from the east side
                        entryY = connectedArea.gridLength - 1;  // Enter from the north side
                    }
                    
                    return this.setCurrentArea(connectedArea, entryX, entryY);
                }
            } else {
                return [`You can't go ${direction} from here.`];
            }
        }
    }
    
    getStatus() {
        const output = [
            `Name: ${this.name}`,
            `Street Cred: ${this.streetCred}`,
            `Position: ${this.coordinates}`,
            `Energy: ${this.energy}/${this.maxEnergy}`,
            `Hunger: ${this.hunger}`
        ];
        
        if (this.isFlying) {
            output.push("Status: Flying with jetpack");
        } else {
            output.push("Status: On the ground");
        }
        
        return output;
    }
}

class Area {
    constructor(name, description, coordinates = null, height = 1, gridWidth = 10, gridLength = 10) {
        this.name = name;
        this.description = description;
        this.coordinates = coordinates || new Coordinates(0, 0, 0);
        this.height = height;
        this.gridWidth = gridWidth;
        this.gridLength = gridLength;
        this.connections = {};
        this.objects = [];
        this.items = [];
        this.npcs = [];
    }
    
    addConnection(direction, area) {
        this.connections[direction] = area;
        
        // Add reverse connection if it doesn't exist
        const reverseDirection = this.getReverseDirection(direction);
        if (reverseDirection && !(reverseDirection in area.connections)) {
            area.connections[reverseDirection] = this;
        }
    }
    
    getReverseDirection(direction) {
        const directionMap = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east',
            'up': 'down',
            'down': 'up',
            'forward': 'backward',
            'backward': 'forward',
            'right': 'left',
            'left': 'right'
        };
        
        return directionMap[direction] || null;
    }
    
    placeObjectAt(obj, x, y, z = 0) {
        obj.coordinates = new Coordinates(
            this.coordinates.x + x,
            this.coordinates.y + y,
            this.coordinates.z + z
        );
        
        if (obj instanceof Item) {
            this.items.push(obj);
        } else if (obj.constructor.name === 'NPC') {
            this.npcs.push(obj);
        } else {
            this.objects.push(obj);
        }
    }
    
    getObjectsAt(x, y, z = 0) {
        const areaX = this.coordinates.x + x;
        const areaY = this.coordinates.y + y;
        const areaZ = this.coordinates.z + z;
        
        const objectsHere = [];
        
        // Check objects
        for (const obj of this.objects) {
            if (obj.coordinates.x === areaX && 
                obj.coordinates.y === areaY && 
                obj.coordinates.z === areaZ) {
                objectsHere.push(obj);
            }
        }
        
        // Check items
        for (const item of this.items) {
            if (item.coordinates.x === areaX && 
                item.coordinates.y === areaY && 
                item.coordinates.z === areaZ) {
                objectsHere.push(item);
            }
        }
        
        // Check NPCs
        for (const npc of this.npcs) {
            if (npc.coordinates.x === areaX && 
                npc.coordinates.y === areaY && 
                npc.coordinates.z === areaZ) {
                objectsHere.push(npc);
            }
        }
        
        return objectsHere;
    }
    
    addItem(item) {
        // Set item coordinates to match player's position
        this.items.push(item);
    }
    
    removeItem(itemName) {
        const itemIndex = this.items.findIndex(i => i.name.toLowerCase() === itemName.toLowerCase());
        if (itemIndex !== -1) {
            this.items.splice(itemIndex, 1);
            return true;
        }
        return false;
    }
    
    addNPC(npc) {
        this.npcs.push(npc);
    }
}

class GameObject {
    constructor(name, description, coordinates = null) {
        this.name = name;
        this.description = description;
        this.coordinates = coordinates || new Coordinates(0, 0, 0);
    }
    
    interact(player) {
        return [`You interact with the ${this.name}.`];
    }
}

class Transport extends GameObject {
    constructor(name, description, coordinates = null) {
        super(name, description, coordinates);
        this.destination = null;  // Where this transport leads to
        this.destination_coords = new Coordinates(0, 0, 0);  // Grid coordinates in the destination area
    }
    
    setDestination(area, gridX = 0, gridY = 0, gridZ = 0) {
        this.destination = area;
        this.destination_coords = new Coordinates(gridX, gridY, gridZ);
        return [`Destination set to ${area.name} at position (${gridX}, ${gridY}, ${gridZ}).`];
    }
    
    transport(player) {
        if (this.destination) {
            const [gridX, gridY, gridZ] = [
                this.destination_coords.x,
                this.destination_coords.y,
                this.destination_coords.z
            ];
            
            const output = player.setCurrentArea(this.destination, gridX, gridY);
            
            // Update z-coordinate if needed
            if (gridZ !== 0) {
                player.coordinates.z = this.destination.coordinates.z + gridZ;
                output.push(`You are now at elevation ${player.coordinates.z}.`);
            }
            
            output.push(`You travel to ${this.destination.name}.`);
            return output;
        } else {
            return [`${this.name} has no destination set.`];
        }
    }
    
    // Override the interact method to provide transport functionality
    interact(player) {
        if (this.destination) {
            const output = [`You use the ${this.name}.`];
            const transportOutput = this.transport(player);
            return output.concat(transportOutput);
        } else {
            return [`The ${this.name} is not in service. No destination is set.`];
        }
    }
}

class Elevator extends Transport {
    constructor(name = "Elevator", description = "An elevator that can take you to different floors.", coordinates = null) {
        super(name, description, coordinates);
        this.floors = {};  // Dictionary mapping floor numbers to [area, gridX, gridY] arrays
        this.currentFloor = 1;
    }
    
    addFloor(floorNumber, area, gridX = 0, gridY = 0) {
        this.floors[floorNumber] = [area, gridX, gridY];
        return [`Floor ${floorNumber} added: ${area.name}`];
    }
    
    goToFloor(floorNumber, player) {
        if (floorNumber in this.floors) {
            const [area, gridX, gridY] = this.floors[floorNumber];
            this.currentFloor = floorNumber;
            
            // Set destination to the selected floor
            this.setDestination(area, gridX, gridY);
            
            // Transport player to the floor
            const output = this.transport(player);
            output.unshift(`Going to floor ${floorNumber}...`);
            return output;
        } else {
            return [`Floor ${floorNumber} is not accessible from this elevator.`];
        }
    }
    
    interact(player) {
        const availableFloors = Object.keys(this.floors).sort((a, b) => a - b);
        if (availableFloors.length === 0) {
            return [`This elevator doesn't have any floors configured.`];
        }
        
        const output = [
            `You are in the elevator. Current floor: ${this.currentFloor}`,
            `Available floors: ${availableFloors.join(', ')}`
        ];
        
        output.push(`Use 'elevator go to [floor number]' to select a floor.`);
        return output;
    }
}



class NPC {
    constructor(name, description, dialogue = {}) {
        this.name = name;
        this.description = description;
        this.dialogue = dialogue;
        this.coordinates = new Coordinates(0, 0, 0);
        this.quest = null;
    }
    
    talk(player) {
        if (this.quest) {
            if (this.quest.isCompleted) {
                return [this.dialogue.quest_complete || this.dialogue.default || `${this.name} has nothing to say.`];
            } else if (this.quest.isActive) {
                if (this.quest.checkCompletion(player)) {
                    this.quest.complete(player);
                    return [this.dialogue.quest_complete || `${this.name} thanks you for completing the quest!`];
                } else {
                    return [this.dialogue.quest_active || this.dialogue.default || `${this.name} is waiting for you to complete the quest.`];
                }
            } else {
                return [
                    this.dialogue.default || `${this.name} has a quest for you.`,
                    `Quest: ${this.quest.name}`,
                    `${this.quest.description}`
                ];
            }
        } else {
            return [this.dialogue.default || `${this.name} has nothing to say.`];
        }
    }
    
    assignQuest(quest) {
        this.quest = quest;
    }
}

class Quest {
    constructor(name, description, objectiveFunction, rewardFunction) {
        this.name = name;
        this.description = description;
        this.objectiveFunction = objectiveFunction;
        this.rewardFunction = rewardFunction;
        this.isActive = false;
        this.isCompleted = false;
    }
    
    start(player) {
        this.isActive = true;
        return [`You have accepted the quest: ${this.name}`];
    }
    
    checkCompletion(player) {
        return this.objectiveFunction(player);
    }
    
    complete(player) {
        this.isActive = false;
        this.isCompleted = true;
        return this.rewardFunction(player);
    }
}

// Game initialization
function initializeGame() {
    // Create areas
    const park = new Area("Central Park", "A beautiful park with trees and a pond.", 
                         new Coordinates(0, 0, 0), 1, 10, 10);
    
    const house = new Area("Abandoned House", "A creaky old house with dusty furniture.", 
                          new Coordinates(-10, 0, 0), 1, 5, 5);
    
    const street = new Area("Main Street", "A busy street with shops and pedestrians.", 
                           new Coordinates(0, 10, 0), 1, 15, 5);
    
    const alley = new Area("Dark Alley", "A narrow alley between tall buildings.", 
                          new Coordinates(15, 10, 0), 1, 3, 8);
    
    const rooftop = new Area("Rooftop", "A flat rooftop with a great view of the city.", 
                            new Coordinates(15, 10, 10), 1, 5, 5);
    
    const skyscraperLobby = new Area("Skyscraper Lobby", "The grand entrance to a tall skyscraper.", 
                                    new Coordinates(20, 0, 0), 1, 5, 5);
    
    const skyscraperMid = new Area("Skyscraper Mid-Level", "A mid-level floor of the skyscraper.", 
                                  new Coordinates(20, 0, 20), 1, 5, 5);
    
    const skyscraperTop = new Area("Skyscraper Top", "The top floor of the skyscraper with panoramic views.", 
                                  new Coordinates(20, 0, 40), 1, 5, 5);
    
    // Connect areas
    park.addConnection("west", house);
    park.addConnection("north", street);
    street.addConnection("east", alley);
    street.addConnection("north", skyscraperLobby);
    alley.addConnection("up", rooftop);
    skyscraperLobby.addConnection("up", skyscraperMid);
    skyscraperMid.addConnection("up", skyscraperTop);
    
    // Create objects
    const tree = new GameObject("Tree", "A tall oak tree. Home to Jeff and a few other squirrels.");
    park.placeObjectAt(tree, 3, 7);
    
    const bench = new GameObject("Bench", "A wooden bench to sit and relax.");
    park.placeObjectAt(bench, 5, 5);
    
    const pond = new GameObject("Pond", "A small pond with ducks swimming in it.");
    park.placeObjectAt(pond, 8, 2);
    
    // Create items
    const carrot = new Food("Carrot", "A fresh orange carrot.", 15);
    park.placeObjectAt(carrot, 2, 3);
    
    const jetpack = new Jetpack();
    park.placeObjectAt(jetpack, 7, 7);


    // Create an elevator in the skyscraper
    const skyscraperElevator = new Elevator(
        "Skyscraper Elevator", 
        "A modern elevator that can take you to different floors of the skyscraper."
    );
    
    // Add floors to the elevator
    skyscraperElevator.addFloor(1, skyscraperLobby, 2, 2);  // Floor 1 (Lobby)
    skyscraperElevator.addFloor(10, skyscraperMid, 2, 2);   // Floor 10 (Mid-level)
    skyscraperElevator.addFloor(20, skyscraperTop, 2, 2);   // Floor 20 (Top floor)
    
    // Place the elevator in each floor
    skyscraperLobby.placeObjectAt(skyscraperElevator, 2, 2);
    
    // Create a second elevator instance for the mid-level floor
    const midElevator = new Elevator(
        "Skyscraper Elevator", 
        "A modern elevator that can take you to different floors of the skyscraper."
    );
    midElevator.addFloor(1, skyscraperLobby, 2, 2);
    midElevator.addFloor(10, skyscraperMid, 2, 2);
    midElevator.addFloor(20, skyscraperTop, 2, 2);
    midElevator.currentFloor = 10;  // Set current floor to mid-level
    skyscraperMid.placeObjectAt(midElevator, 2, 2);
    
    // Create a third elevator instance for the top floor
    const topElevator = new Elevator(
        "Skyscraper Elevator", 
        "A modern elevator that can take you to different floors of the skyscraper."
    );
    topElevator.addFloor(1, skyscraperLobby, 2, 2);
    topElevator.addFloor(10, skyscraperMid, 2, 2);
    topElevator.addFloor(20, skyscraperTop, 2, 2);
    topElevator.currentFloor = 20;  // Set current floor to top level
    skyscraperTop.placeObjectAt(topElevator, 2, 2);
    
    // Create a transport example (a taxi)
    const taxi = new Transport(
        "Taxi", 
        "A yellow taxi cab that can take you to different locations."
    );
    taxi.setDestination(park, 5, 5);
    street.placeObjectAt(taxi, 7, 2);
    
    
    // Create NPCs
    const squirrel = new NPC("Jeff", "A bushy-tailed squirrel with a worried expression.", 
                           {
                               "default": "I've lost my acorns! Can you help me find 10 acorns?",
                               "quest_active": "Have you found my acorns yet?",
                               "quest_complete": "Thank you for finding my acorns! Now I can survive the winter."
                           });
    park.placeObjectAt(squirrel, 3, 6);
    
    // Create the acorn collection quest
    function acornQuestObjective(player) {
        const acornCount = player.inventory.filter(item => item.name.toLowerCase() === "acorn").length;
        const goldenAcornCount = player.inventory.filter(item => item.name.toLowerCase() === "golden acorn").length;
        return acornCount + (goldenAcornCount * 2) >= 10;
    }
    
    function acornQuestReward(player) {
        // Remove acorns from inventory
        const acornsToRemove = [];
        let count = 0;
        
        for (const item of player.inventory) {
            if (item.name.toLowerCase() === "acorn" && count < 10) {
                acornsToRemove.push(item);
                count += 1;
            } else if (item.name.toLowerCase() === "golden acorn" && count < 10) {
                acornsToRemove.push(item);
                count += 2;  // Golden acorns count as 2
            }
        }
        
        for (const acorn of acornsToRemove) {
            player.inventory = player.inventory.filter(item => item !== acorn);
        }
        
        // Give reward
        player.streetCred += 20;
        
        const output = [
            "Your street cred increased by 20 points!",
            "Jeff (the squirrel) is very grateful and spreads the word about your helpfulness."
        ];
        
        // Add a special item as reward
        const jetpackUpgrade = new Item("Jetpack Fuel Upgrade", "A special upgrade that increases jetpack efficiency.");
        player.addItem(jetpackUpgrade);
        
        if (player.jetpack) {
            player.jetpack.maxFuel = 150;
            player.jetpack.fuel = 150;
            output.push("Your jetpack has been upgraded with a larger fuel tank!");
        }
        
        return output;
    }
    
    const acornQuest = new Quest("Acorn Collector", 
                               "Find 10 acorns for the squirrels. Golden acorns count as 2!", 
                               acornQuestObjective, 
                               acornQuestReward);
    squirrel.assignQuest(acornQuest);
    
    // Add areas to game state
    gameState.areas = {
        park,
        house,
        street,
        alley,
        rooftop,
        skyscraperLobby,
        skyscraperMid,
        skyscraperTop
    };
    
    // Create player
    gameState.player = new Player();
    
    // Set player's starting area
    return gameState.player.setCurrentArea(park);
}

// Command processor
function processCommand(command) {
    const player = gameState.player;
    let output = [];
    
    command = command.toLowerCase().trim();
    
    if (command === "quit") {
        output = ["Thanks for playing!"];
    } else if (command === "look") {
        output = player.lookAround();
    } else if (command.startsWith("pick up ")) {
        const itemName = command.substring(8);
        const item = player.currentArea.items.find(i => i.name.toLowerCase() === itemName.toLowerCase());
        if (item) {
            output = player.addItem(item);
            player.currentArea.removeItem(itemName);
        } else {
            output = [`There is no ${itemName} here.`];
        }
    } else if (command.startsWith("drop ")) {
        const itemName = command.substring(5);
        output = player.removeItem(itemName);
    } else if (command.startsWith("go ")) {
        const direction = command.substring(3);
        output = player.move(direction);
    } else if (command === "up" || command === "down" || 
               command === "north" || command === "south" || 
               command === "east" || command === "west" ||
               command === "northeast" || command === "northwest" ||
               command === "southeast" || command === "southwest" ||
               command === "forward" || command === "backward" ||
               command === "right" || command === "left") {
        // Allow direct direction commands without "go"
        output = player.move(command);
    } else if (command === "inventory" || command === "inv") {
        if (player.inventory.length > 0) {
            output = ["Your inventory:"];
            for (const item of player.inventory) {
                output.push(`- ${item}`);
            }
        } else {
            output = ["Your inventory is empty."];
        }
    } else if (command.startsWith("eat ")) {
        const itemName = command.substring(4);
        output = player.eat(itemName);
    } else if (command === "activate jetpack") {
        output = player.activateJetpack();
    } else if (command === "deactivate jetpack") {
        output = player.deactivateJetpack();
    } else if (command.startsWith("fly ")) {
        const direction = command.substring(4);
        output = player.fly(direction);
    } else if (command.startsWith("talk to ")) {
        const npcName = command.substring(8);
        const npc = player.currentArea.npcs.find(n => n.name.toLowerCase() === npcName.toLowerCase());
        if (npc) {
            output = npc.talk(player);
            if (npc.quest && !npc.quest.isActive && !npc.quest.isCompleted) {
                output.push("Accept quest? (Type 'yes' or 'no')");
                // Set a flag to handle the quest acceptance in the next command
                gameState.pendingQuestAcceptance = {
                    npc: npc,
                    quest: npc.quest
                };
            }
        } else {
            output = [`There is no ${npcName} here to talk to.`];
        }
    } else if (command === "yes" && gameState.pendingQuestAcceptance) {
        const quest = gameState.pendingQuestAcceptance.quest;
        output = quest.start(player);
        gameState.pendingQuestAcceptance = null;
    } else if (command === "no" && gameState.pendingQuestAcceptance) {
        output = ["You declined the quest."];
        gameState.pendingQuestAcceptance = null;
    } else if (command === "status") {
        output = player.getStatus();
    } else if (command.startsWith("use ")) {
        const objectName = command.substring(4);
        // Find the object at the player's current position
        const [gridX, gridY, gridZ] = player.getGridPosition();
        const objectsHere = player.currentArea.getObjectsAt(gridX, gridY, gridZ);
        const object = objectsHere.find(obj => obj.name.toLowerCase() === objectName.toLowerCase());
        
        if (object) {
            output = object.interact(player);
        } else {
            output = [`There is no ${objectName} here to use.`];
        }
    } else if (command.startsWith("elevator go to ") || command.startsWith("elevator goto ")) {
        // Extract floor number
        const floorStr = command.includes("goto") ? 
            command.substring(13) : 
            command.substring(15);
        const floorNumber = parseInt(floorStr);
        
        if (isNaN(floorNumber)) {
            output = ["Please specify a valid floor number."];
        } else {
            // Find an elevator at the player's current position
            const [gridX, gridY, gridZ] = player.getGridPosition();
            const objectsHere = player.currentArea.getObjectsAt(gridX, gridY, gridZ);
            const elevator = objectsHere.find(obj => obj instanceof Elevator);
            
            if (elevator) {
                output = elevator.goToFloor(floorNumber, player);
            } else {
                output = ["There is no elevator here."];
            }
        }
    } else if (command === "help") {
        output = [
            "Available commands:",
            "- look - Look around your current location",
            "- go [direction] - Move in a direction (north, south, east, west, northeast, etc.)",
            "- up/down - Move vertically (requires jetpack for up)",
            "- pick up [item] - Pick up an item",
            "- drop [item] - Drop an item from your inventory",
            "- inventory or inv - Check your inventory",
            "- eat [item] - Eat food",
            "- activate jetpack - Start flying",
            "- deactivate jetpack - Stop flying",
            "- fly [direction] - Fly in a direction",
            "- talk to [npc] - Talk to an NPC",
            "- use [object] - Interact with an object at your location",
            "- elevator go to [floor] - Use an elevator to go to a specific floor",
            "- status - Check your status",
            "- help - Show this help message"
        ];
    } else {
        output = ["Command not recognized. Try 'help' for a list of commands."];
    }
    
    return output;
}

// UI Interaction
document.addEventListener('DOMContentLoaded', function() {
    const gameOutput = document.getElementById('game-output');
    const gameInput = document.getElementById('game-input');
    const submitButton = document.getElementById('submit-command');
    const actionButtons = document.querySelectorAll('.action-btn');
    const moveButtons = document.querySelectorAll('.move-btn');
    
    // Initialize the game
    function startGame() {
        if (!gameState.initialized) {
            const welcomeMessages = [
                "Welcome to the Vita Game!",
                "You are Vita, a mischievous bunny with a jetpack and a taste for adventure.",
                "Explore the world, cause some chaos, and have fun!",
                "Type 'look' to see details about your surroundings, or 'help' for a list of commands."
            ];
            
            for (const msg of welcomeMessages) {
                appendToOutput(msg, 'system-message');
            }
            
            const initOutput = initializeGame();
            for (const msg of initOutput) {
                appendToOutput(msg);
            }
            
            gameState.initialized = true;
        }
    }
    
    // Append text to the game output
    function appendToOutput(text, className = '') {
        const p = document.createElement('p');
        p.textContent = text;
        p.className = className + ' new-message';
        gameOutput.appendChild(p);
        gameOutput.scrollTop = gameOutput.scrollHeight;
        
        // Store in history
        gameState.outputHistory.push({
            text: text,
            className: className
        });
    }
    
    // Process player input
    function handleCommand(command) {
        if (!command.trim()) return;
        
        appendToOutput('> ' + command, 'player-command');
        
        const output = processCommand(command);
        for (const msg of output) {
            appendToOutput(msg);
        }
        
        // Clear input field
        gameInput.value = '';
    }
    
    // Event listeners
    submitButton.addEventListener('click', function() {
        handleCommand(gameInput.value);
    });
    
    gameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleCommand(gameInput.value);
        }
    });
    
    // Action button handlers
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const command = this.getAttribute('data-command');
            handleCommand(command);
        });
    });
    
    // Movement button handlers
    moveButtons.forEach(button => {
        button.addEventListener('click', function() {
            const direction = this.getAttribute('data-direction');
            if (direction === 'center') return;
            
            // Determine if we should use "go" or "fly" based on player state
            const prefix = gameState.player && gameState.player.isFlying ? 'fly ' : 'go ';
            handleCommand(prefix + direction);
        });
    });
    
    // Start the game
    startGame();
});
