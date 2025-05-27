// Vita and Coral's Messy Day
document.addEventListener('DOMContentLoaded', () => {
    const gamePlansContainer = document.getElementById('game-plans-container');
    if (gamePlansContainer) {
        gamePlansContainer.style.display = 'block';
    }

    // Module aliases from Matter.js
    const Engine = Matter.Engine,
        Render = Matter.Render,
        Runner = Matter.Runner,
        Bodies = Matter.Bodies,
        Composite = Matter.Composite,
        Body = Matter.Body,
        Events = Matter.Events,
        Query = Matter.Query,
        Vector = Matter.Vector,
        Mouse = Matter.Mouse,
        Constraint = Matter.Constraint;

    // --- Game Configuration ---
    const BASE_GAME_WIDTH = 8000; // World width
    const SINGLE_AREA_HEIGHT = 1000;
    const NUM_AREAS_VERTICAL = 2; // Simplified to 2 areas for now
    const BASE_GAME_HEIGHT = SINGLE_AREA_HEIGHT * NUM_AREAS_VERTICAL;

    let GAME_WIDTH, GAME_HEIGHT; // World dimensions
    let CANVAS_WIDTH, CANVAS_HEIGHT; // Renderer/Canvas dimensions


    function calculateGameDimensions() {
        let sw = window.innerWidth;
        let sh = window.innerHeight;

        GAME_WIDTH = BASE_GAME_WIDTH;
        GAME_HEIGHT = BASE_GAME_HEIGHT;

        if (document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement) {
            CANVAS_WIDTH = sw;
            CANVAS_HEIGHT = sh;
        } else {
            let targetCanvasWidth = sw * 0.9;
            let targetCanvasHeight = sh * 0.9;
            CANVAS_WIDTH = Math.floor(Math.min(targetCanvasWidth, sw));
            CANVAS_HEIGHT = Math.floor(Math.min(targetCanvasHeight, sh));
        }
    }
    calculateGameDimensions();

    // Vita (Player) Configuration
    const VITA_START_X = 150;
    const VITA_WIDTH = 35;
    const VITA_HEIGHT = 60; // Adjusted for a bunny-like proportion
    const VITA_IMAGE_PATH = 'images/vitaimages/vitasprite.png'; // Placeholder - ensure you have this
    const VITA_SPRITE_X_SCALE = 0.06;
    const VITA_SPRITE_Y_SCALE = 0.06;
    const VITA_FRICTION_AIR = 0.01;
    const VITA_DENSITY = 0.002;
    const VITA_RESTITUTION = 0.1;
    let VITA_START_Y;

    // Coral (NPC Baby) Configuration
    const CORAL_WIDTH = 100;
    const CORAL_HEIGHT = 100;
    const CORAL_IMAGE_PATH = 'images/artwork/coral.png'; // Placeholder - ensure you have this
    const CORAL_SPRITE_X_SCALE = 0.5;
    const CORAL_SPRITE_Y_SCALE = 0.5;
    const CORAL_FRICTION_AIR = 0.02;
    const CORAL_DENSITY = 0.0015;
    const CORAL_RESTITUTION = 0.2;
    const CORAL_LIQUIFY_RADIUS = 70; // How close Coral needs to be to liquify something
    const CORAL_ACTION_COOLDOWN_MIN = 250; // ms
    const CORAL_ACTION_COOLDOWN_MAX = 500; // ms
    const CORAL_MOVE_FORCE = 0.0015;
    const CORAL_OBSTACLE_DETECTION_RANGE = 80; // How far ahead Coral detects obstacles (walls, platforms)
    


    // Ground Configuration
    const GROUND_HEIGHT = 60;
    const GROUND_COLOR = '#6B8E23';
    const PLATFORM_COLOR = '#A0522D';
    const PLATFORM_THICKNESS = GROUND_HEIGHT;

    // Walls & Ceiling
    const WALL_THICKNESS = 50;
    const WALL_COLOR = '#333333';
    const CEILING_Y_OFFSET = -WALL_THICKNESS / 2;
    const CEILING_HEIGHT = WALL_THICKNESS;

    // Physics
    const GRAVITY_Y = 1;
    const PLAYER_MOVE_FORCE_FACTOR = 0.005;
    const PLAYER_JUMP_FORCE_MULTIPLIER = 0.03;

    // Objects
    const BOX_SIZE = 50;
    const NUM_BOXES = 10;
    const BOUNCY_BALL_RADIUS = 20;
    const NUM_BALLS = 8;
    const BOUNCY_BALL_RESTITUTION = 0.9;
    const BACKGROUND_COLOR = '#ADD8E6'; // Light blue sky

    // Bouncy Platform Configuration
    const BOUNCY_PLATFORM_COLOR = '#FF69B4';
    const BOUNCY_PLATFORM_RESTITUTION = 1.0;
    const BOUNCY_PLATFORM_ACTIVE_FORCE_MULTIPLIER = 0.05;

    // Liquifier Object Configuration
    const LIQUIFIER_OBJECT_SIZE = 30;
    const LIQUIFIER_OBJECT_COLOR = '#40E0D0'; // Turquoise
    const NUM_LIQUIFIERS = 3;
    const LIQUIFIER_OBJECT_LABEL_PREFIX = "Liquifier";

    // Cleaner Object Configuration
    const CLEANER_OBJECT_SIZE = 30;
    const CLEANER_OBJECT_COLOR = '#FA8072'; // Salmon
    const NUM_CLEANERS = 3;
    const CLEANER_OBJECT_LABEL_PREFIX = "Cleaner";

    // Camera
    const CAMERA_PADDING = { x: 300, y: 300 };

    // Respawn Configuration
    let RESPAWN_Y_LIMIT;
    const RESPAWN_X_BUFFER = 200;

    // --- Global Game State Variables ---
    let engine, world, render, runner;
    let vitaBody, coralBody;
    let ground1, platform2, ceiling, leftWall, rightWall;
    let boxStack = [], bouncyBallsArray = [];
    let bouncyPlatformObjects = [], customStaticPlatformObjects = [];
    let liquifierObjectsArray = [], cleanerObjectsArray = [];

    let heldObject = null;
    let grabConstraint = null;

    // Player Grab/Throw Configuration
    const GRAB_RADIUS = 70; // Matched to original
    const THROW_FORCE_MAGNITUDE = 0.0001; // Matched to original
    const GRAB_POINT_OFFSET = { x: VITA_WIDTH / 2 + 15, y: -VITA_HEIGHT / 4 }; // Point in front of Vita to hold objects



    let isGameActive = false;
    let menuContainer = null;

    // Liquify Ability
    let liquifiedParticlesArray = [];
    window.liquifiedParticlesArray = liquifiedParticlesArray; // Expose for debugging
    const LIQUIFY_RADIUS_VITA = 100; // Vita's range to liquify an object
    const PARTICLE_SIZE = 8;
    const MIN_PARTICLES_ON_LIQUIFY = 8;
    const CLEANUP_RADIUS_VITA = 150; // Vita's range to clean up particles

    // --- Helper Classes for Game Object Creation ---
    class EnvironmentBuilder {
        constructor(world, config) {
            this.world = world;
            this.config = config;
        }

        createFloors() {
            const { GAME_WIDTH, GAME_HEIGHT, SINGLE_AREA_HEIGHT, GROUND_HEIGHT, PLATFORM_THICKNESS, GROUND_COLOR, PLATFORM_COLOR } = this.config;
            ground1 = Bodies.rectangle(GAME_WIDTH / 2, GAME_HEIGHT - (GROUND_HEIGHT / 2), GAME_WIDTH, GROUND_HEIGHT, {
                isStatic: true, label: "Ground1", render: { fillStyle: GROUND_COLOR }
            });
            platform2 = Bodies.rectangle(GAME_WIDTH / 2, (GAME_HEIGHT - SINGLE_AREA_HEIGHT) - (PLATFORM_THICKNESS / 2), GAME_WIDTH, PLATFORM_THICKNESS, {
                isStatic: true, label: "Platform2", render: { fillStyle: PLATFORM_COLOR }
            });
            Composite.add(this.world, [ground1, platform2]);
            return { ground1, platform2 };
        }

        createWalls() {
            const { GAME_WIDTH, GAME_HEIGHT, WALL_THICKNESS, WALL_COLOR } = this.config;
            leftWall = Bodies.rectangle(-WALL_THICKNESS / 4, GAME_HEIGHT / 2, WALL_THICKNESS, GAME_HEIGHT * 2, {
                isStatic: true, label: "WallLeft", render: { fillStyle: WALL_COLOR }
            });
            rightWall = Bodies.rectangle(GAME_WIDTH + WALL_THICKNESS / 2, GAME_HEIGHT / 2, WALL_THICKNESS, GAME_HEIGHT * 2, {
                isStatic: true, label: "WallRight", render: { fillStyle: WALL_COLOR }
            });
            Composite.add(this.world, [leftWall, rightWall]);
            return { leftWall, rightWall };
        }

        createCeiling() {
            const { GAME_WIDTH, CEILING_Y_OFFSET, CEILING_HEIGHT, WALL_THICKNESS, WALL_COLOR } = this.config;
            ceiling = Bodies.rectangle(GAME_WIDTH / 2, CEILING_Y_OFFSET, GAME_WIDTH + WALL_THICKNESS * 2, CEILING_HEIGHT, {
                isStatic: true, label: "Ceiling", render: { fillStyle: WALL_COLOR }
            });
            Composite.add(this.world, ceiling);
            return ceiling;
        }

        createCustomPlatforms(platformsData = []) {
            const createdPlatforms = [];
            platformsData.forEach(data => {
                const platform = Bodies.rectangle(data.x, data.y, data.width, data.height, {
                    isStatic: true,
                    label: data.label || "CustomPlatform",
                    render: { fillStyle: data.color || '#555555' }
                });
                createdPlatforms.push(platform);
            });
            if (createdPlatforms.length > 0) Composite.add(this.world, createdPlatforms);
            return createdPlatforms;
        }

        createBouncyPlatforms(platformsData = []) {
            const createdPlatforms = [];
            platformsData.forEach(data => {
                const platform = Bodies.rectangle(data.x, data.y, data.width, data.height, {
                    isStatic: true,
                    label: data.label || "BouncyPlatform",
                    restitution: this.config.BOUNCY_PLATFORM_RESTITUTION,
                    render: { fillStyle: data.color || this.config.BOUNCY_PLATFORM_COLOR }
                });
                createdPlatforms.push(platform);
            });
            if (createdPlatforms.length > 0) Composite.add(this.world, createdPlatforms);
            return createdPlatforms;
        }
    }

    class Box {
        constructor(x, y, size, labelSuffix, colorIndex) {
            this.body = Bodies.rectangle(x, y, size, size, {
                label: `Box-${labelSuffix}`,
                friction: 0.1,
                restitution: 0.1,
                render: { fillStyle: `hsl(${colorIndex * 36}, 70%, 60%)` } // Varied colors
            });
        }
        addToWorld(world) { Composite.add(world, this.body); }
    }

    class BouncyBall {
        constructor(x, y, radius, labelSuffix, colorIndex, numBallsTotal) {
            this.body = Bodies.circle(x, y, radius, {
                label: `Ball-${labelSuffix}`,
                friction: 0.001,
                restitution: BOUNCY_BALL_RESTITUTION,
                render: { fillStyle: `hsl(${colorIndex * (360 / numBallsTotal)}, 80%, 60%)` }
            });
        }
        addToWorld(world) { Composite.add(world, this.body); }
    }

    class LiquifierObject {
        constructor(x, y, size, labelSuffix) {
            this.body = Bodies.rectangle(x, y, size, size, {
                label: `${LIQUIFIER_OBJECT_LABEL_PREFIX}-${labelSuffix}`,
                isStatic: false, // Let them be movable
                friction: 0.1,
                restitution: 0.7,
                render: { fillStyle: LIQUIFIER_OBJECT_COLOR }
            });
        }
        addToWorld(world) { Composite.add(world, this.body); }
    }

    class CleanerObject {
        constructor(x, y, size, labelSuffix) {
            this.body = Bodies.rectangle(x, y, size, size, {
                label: `${CLEANER_OBJECT_LABEL_PREFIX}-${labelSuffix}`,
                isStatic: false, // Let them be movable
                friction: 0.1,
                restitution: 0.5,
                render: { fillStyle: CLEANER_OBJECT_COLOR }
            });
        }
        addToWorld(world) { Composite.add(world, this.body); }
    }

    class Coral {
        constructor(x, y, width, height, imagePath, spriteScaleX, spriteScaleY) {
            this.body = Bodies.rectangle(x, y, width, height, {
                label: "Coral",
                frictionAir: CORAL_FRICTION_AIR,
                density: CORAL_DENSITY,
                restitution: CORAL_RESTITUTION,
                render: {
                    sprite: {
                        texture: imagePath,
                        xScale: spriteScaleX,
                        yScale: spriteScaleY
                    }
                }
            });
            this.actionCooldown = CORAL_ACTION_COOLDOWN_MIN + Math.random() * (CORAL_ACTION_COOLDOWN_MAX - CORAL_ACTION_COOLDOWN_MIN);
            this.lastActionTime = Date.now();
            this.movementInterval = 1000 + Math.random() * 1500; // Time between movement decisions
            this.lastMovementTime = Date.now();
            this.isMovingRight = Math.random() < 0.5;
        }

        addToWorld(world) {
            Composite.add(world, this.body);
        }

        updateAI(worldContext, allDynamicObjects) {
            const now = Date.now();

            // Movement AI
            if (now - this.lastMovementTime > this.movementInterval) {
                if (Math.random() < 0.3) { // 30% chance to change direction
                    this.isMovingRight = !this.isMovingRight;
                }
                
                // Small chance to jump if on ground
                const coralOnGround = this.checkIfOnGround(worldContext);
                if (coralOnGround && Math.random() < 0.1) {
                     Body.applyForce(this.body, this.body.position, { x: 0, y: -PLAYER_JUMP_FORCE_MULTIPLIER * this.body.mass * 0.8 }); // Slightly weaker jump
                }

                this.lastMovementTime = now;
                this.movementInterval = 1000 + Math.random() * 2000; // 1-3 seconds
            }

            // Apply movement force
            const moveX = this.isMovingRight ? CORAL_MOVE_FORCE : -CORAL_MOVE_FORCE;
            Body.applyForce(this.body, this.body.position, { x: moveX * this.body.mass, y: 0 });

            // Flip sprite
            if (this.body.render.sprite) {
                const scaleX = Math.abs(this.body.render.sprite.xScale);
                this.body.render.sprite.xScale = this.isMovingRight ? scaleX : -scaleX;
            }

            // Liquify action AI
            if (now - this.lastActionTime > this.actionCooldown) {
                this.tryLiquifyNearby(allDynamicObjects);
                this.lastActionTime = now;
                this.actionCooldown = CORAL_ACTION_COOLDOWN_MIN + Math.random() * (CORAL_ACTION_COOLDOWN_MAX - CORAL_ACTION_COOLDOWN_MIN);
            }
        }
        
        checkIfOnGround(worldContext) {
            const coralBounds = this.body.bounds;
            const bodiesBelow = Query.region(Composite.allBodies(worldContext), {
                min: { x: coralBounds.min.x, y: coralBounds.max.y - 5 },
                max: { x: coralBounds.max.x, y: coralBounds.max.y + 5 }
            });
            for (const body of bodiesBelow) {
                if (body !== this.body && body.isStatic) { // Simplified check
                    const collisions = Query.collides(this.body, [body]);
                    if (collisions.length > 0) return true;
                }
            }
            return false;
        }


        tryLiquifyNearby(allDynamicObjects) {
            for (const obj of allDynamicObjects) {
                if (obj === this.body || obj.isStatic || obj.isSensor || 
                    obj.label.startsWith('particle-') || obj.label === "Vita" ||
                    obj.label.startsWith(LIQUIFIER_OBJECT_LABEL_PREFIX) || // Coral doesn't liquify these
                    obj.label.startsWith(CLEANER_OBJECT_LABEL_PREFIX)) {
                    continue;
                }

                const distSq = Vector.magnitudeSquared(Vector.sub(obj.position, this.body.position));
                if (distSq < CORAL_LIQUIFY_RADIUS * CORAL_LIQUIFY_RADIUS) {
                    if (liquifyBody(obj)) {
                        console.log("Coral liquified an object!");
                        // Optional: Add a visual/sound effect for Coral's action
                        break; // Liquify one object per attempt
                    }
                }
            }
        }
    }


    const gameContainer = document.getElementById('game-container');
    if (!gameContainer) {
        console.error("Fatal Error: Game container div not found!");
        return;
    }
    gameContainer.style.position = 'relative';

    // --- Player Input Handling (Persistent) ---
    const keysPressed = {};
    let isVitaOnGround = false;
    let rKeyPressed = false;

    document.addEventListener('keydown', (event) => {
        const key = event.key.toLowerCase();
        keysPressed[key] = true;

        if (key === 'r' && isGameActive && !rKeyPressed) {
            rKeyPressed = true;
            resetVitaPosition();
        }
        if (key === 'y' && isGameActive && !keysPressed.yWasPressed) {
            keysPressed.yWasPressed = true;
            vitaLiquifyNearestObject();
        }
        if (key === 'c' && isGameActive && !keysPressed.cWasPressed) {
            keysPressed.cWasPressed = true;
            vitaCleanupNearbyParticles();
        }
    });

    document.addEventListener('keyup', (event) => {
        const key = event.key.toLowerCase();
        keysPressed[key] = false;
        if (key === 'r') rKeyPressed = false;
        if (key === 'y') keysPressed.yWasPressed = false;
        if (key === 'c') keysPressed.cWasPressed = false;
    });

    // --- Menu Styling and Creation (Simplified from vitachaos2.js) ---
    function styleMenuElement(menuElement) { /* ... (same as vitachaos2.js) ... */ 
        menuElement.style.position = 'absolute';
        menuElement.style.top = '50%';
        menuElement.style.left = '50%';
        menuElement.style.transform = 'translate(-50%, -50%)';
        menuElement.style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
        menuElement.style.padding = '30px';
        menuElement.style.borderRadius = '10px';
        menuElement.style.textAlign = 'center';
        menuElement.style.zIndex = '100';
        menuElement.style.width = 'auto';
        menuElement.style.maxWidth = '500px';
        menuElement.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.3)';
    }

    function createMenuButton(text, onClick) { /* ... (same as vitachaos2.js) ... */ 
        const button = document.createElement('button');
        button.textContent = text;
        button.style.display = 'block';
        button.style.width = 'auto';
        button.style.margin = '10px auto';
        button.style.padding = '10px 20px';
        button.style.fontSize = '18px';
        button.style.cursor = 'pointer';
        button.style.borderRadius = '5px';
        button.style.border = 'none';
        button.style.backgroundColor = '#FFB6C1'; // Light Pink
        button.style.color = 'black';
        button.style.fontWeight = 'bold';
        button.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
        button.addEventListener('mouseover', () => button.style.backgroundColor = '#FFC0CB'); // Pink
        button.addEventListener('mouseout', () => button.style.backgroundColor = '#FFB6C1');
        button.addEventListener('click', onClick);
        return button;
    }

    function clearMenu() {
        if (menuContainer && menuContainer.parentNode) {
            menuContainer.parentNode.removeChild(menuContainer);
        }
        menuContainer = null;
    }

    function showStartMenu() {
        clearMenu();
        isGameActive = false;
        if (runner) Runner.stop(runner);
        if (gamePlansContainer) gamePlansContainer.style.display = 'block';
        
        const controlsInfo = document.getElementById('controls-info');
        if (controlsInfo) controlsInfo.style.display = 'none';

        menuContainer = document.createElement('div');
        styleMenuElement(menuContainer);

        const title = document.createElement('h1');
        title.textContent = "Vita & Coral's Messy Day";
        title.style.color = 'white';
        menuContainer.appendChild(title);

        const startButton = createMenuButton('Start Game', handleStartGame);
        menuContainer.appendChild(startButton);
        const fullscreenButton = createMenuButton('Toggle Fullscreen', toggleFullscreen);
        menuContainer.appendChild(fullscreenButton);
        gameContainer.appendChild(menuContainer);
    }

    function showPauseMenu() { /* ... (similar to vitachaos2.js, but with new game title) ... */ 
        if (!isGameActive) return;
        isGameActive = false;
        Runner.stop(runner);
        if (gamePlansContainer) gamePlansContainer.style.display = 'block';

        clearMenu();
        menuContainer = document.createElement('div');
        styleMenuElement(menuContainer);
        const title = document.createElement('h2');
        title.textContent = 'Paused';
        title.style.color = 'white';
        menuContainer.appendChild(title);
        const resumeButton = createMenuButton('Resume', handleResumeGame);
        const restartButton = createMenuButton('Restart', handleRestartGame);
        const quitButton = createMenuButton('Quit to Main Menu', handleQuitGame);
        menuContainer.appendChild(resumeButton);
        menuContainer.appendChild(restartButton);
        menuContainer.appendChild(quitButton);
        gameContainer.appendChild(menuContainer);
    }


    // --- Game Setup ---
    function setupGame() {
        engine = Engine.create();
        world = engine.world;
        world.gravity.y = GRAVITY_Y;

        RESPAWN_Y_LIMIT = GAME_HEIGHT + 200;

        const FLOOR_1_TOP_Y = GAME_HEIGHT - GROUND_HEIGHT;
        const FLOOR_2_TOP_Y = (GAME_HEIGHT - SINGLE_AREA_HEIGHT) - PLATFORM_THICKNESS;
        VITA_START_Y = FLOOR_1_TOP_Y - VITA_HEIGHT / 2 - 20;
        const CORAL_START_Y = FLOOR_1_TOP_Y - CORAL_HEIGHT / 2 - 20;


        const envConfig = {
            GAME_WIDTH, GAME_HEIGHT, SINGLE_AREA_HEIGHT,
            GROUND_HEIGHT, PLATFORM_THICKNESS, GROUND_COLOR, PLATFORM_COLOR,
            WALL_THICKNESS, WALL_COLOR, CEILING_Y_OFFSET, CEILING_HEIGHT,
            BOUNCY_PLATFORM_COLOR, BOUNCY_PLATFORM_RESTITUTION, BOUNCY_PLATFORM_ACTIVE_FORCE_MULTIPLIER
        };

        const envBuilder = new EnvironmentBuilder(world, envConfig);
        envBuilder.createFloors();
        envBuilder.createWalls();
        envBuilder.createCeiling();

        render = Render.create({
            element: gameContainer,
            engine: engine,
            options: {
                width: CANVAS_WIDTH,
                height: CANVAS_HEIGHT,
                wireframes: false,
                background: BACKGROUND_COLOR
            }
        });

        if (!render.mouse) { // Ensure mouse is initialized
            render.mouse = Mouse.create(render.canvas);
        }

        vitaBody = Bodies.rectangle(VITA_START_X, VITA_START_Y, VITA_WIDTH, VITA_HEIGHT, {
            label: "Vita",
            frictionAir: VITA_FRICTION_AIR, density: VITA_DENSITY, restitution: VITA_RESTITUTION,
            render: { sprite: { texture: VITA_IMAGE_PATH, xScale: VITA_SPRITE_X_SCALE, yScale: VITA_SPRITE_Y_SCALE } }
        });
        Composite.add(world, vitaBody);

        coralBody = new Coral(GAME_WIDTH * 0.7, CORAL_START_Y, CORAL_WIDTH, CORAL_HEIGHT, CORAL_IMAGE_PATH, CORAL_SPRITE_X_SCALE, CORAL_SPRITE_Y_SCALE);
        coralBody.addToWorld(world);


        // Platforms
        const customPlatformDefs = [
            { x: GAME_WIDTH * 0.3, y: FLOOR_1_TOP_Y - 120, width: 250, height: 30, label: "CustomPlatform1", color: '#CD853F' },
            { x: GAME_WIDTH * 0.7, y: FLOOR_1_TOP_Y - 220, width: 180, height: 25, label: "CustomPlatform2", color: '#D2B48C' },
            { x: GAME_WIDTH * 0.5, y: FLOOR_2_TOP_Y - 150, width: 300, height: 30, label: "CustomPlatformArea2", color: '#BC8F8F' }
        ];
        customStaticPlatformObjects = envBuilder.createCustomPlatforms(customPlatformDefs);

        const bouncyPlatformsData = [
            { x: GAME_WIDTH * 0.8, y: FLOOR_1_TOP_Y - 50, width: 200, height: 30, label: "BouncyPlatform1" },
            { x: GAME_WIDTH * 0.2, y: FLOOR_2_TOP_Y - 80, width: 150, height: 30, label: "BouncyPlatformArea2" }
        ];
        bouncyPlatformObjects = envBuilder.createBouncyPlatforms(bouncyPlatformsData);

        // Spawn Boxes
        boxStack = [];
        for (let i = 0; i < NUM_BOXES; i++) {
            const area = (i < NUM_BOXES / 2) ? 1 : 2;
            const floorTopY = area === 1 ? FLOOR_1_TOP_Y : FLOOR_2_TOP_Y;
            const initialX = GAME_WIDTH * (0.2 + Math.random() * 0.6);
            const initialY = floorTopY - BOX_SIZE / 2 - (Math.random() * 100 + 20);
            const boxObj = new Box(initialX, initialY, BOX_SIZE, `box-${i}`, i);
            boxObj.addToWorld(world);
            boxStack.push(boxObj.body);
        }

        // Spawn Bouncy Balls
        bouncyBallsArray = [];
        for (let i = 0; i < NUM_BALLS; i++) {
            const area = (i < NUM_BALLS / 2) ? 1 : 2;
            const floorTopY = area === 1 ? FLOOR_1_TOP_Y : FLOOR_2_TOP_Y;
            const initialX = GAME_WIDTH * (0.2 + Math.random() * 0.6);
            const initialY = floorTopY - BOUNCY_BALL_RADIUS - (Math.random() * 150 + 20);
            const ballObj = new BouncyBall(initialX, initialY, BOUNCY_BALL_RADIUS, `ball-${i}`, i, NUM_BALLS);
            ballObj.addToWorld(world);
            bouncyBallsArray.push(ballObj.body);
        }
        
        // Spawn Liquifier Objects
        liquifierObjectsArray = [];
        for (let i = 0; i < NUM_LIQUIFIERS; i++) {
            const initialX = GAME_WIDTH * (0.1 + Math.random() * 0.8); // Random X
            const initialY = (i % 2 === 0 ? FLOOR_1_TOP_Y : FLOOR_2_TOP_Y) - LIQUIFIER_OBJECT_SIZE / 2 - (Math.random() * 50 + 50); // Alternate floors, random Y
            const liquifierObj = new LiquifierObject(initialX, initialY, LIQUIFIER_OBJECT_SIZE, `liq-${i}`);
            liquifierObj.addToWorld(world);
            liquifierObjectsArray.push(liquifierObj.body);
        }

        // Spawn Cleaner Objects
        cleanerObjectsArray = [];
        for (let i = 0; i < NUM_CLEANERS; i++) {
            const initialX = GAME_WIDTH * (0.1 + Math.random() * 0.8); // Random X
            const initialY = (i % 2 === 0 ? FLOOR_1_TOP_Y : FLOOR_2_TOP_Y) - CLEANER_OBJECT_SIZE / 2 - (Math.random() * 50 + 70); // Alternate floors, random Y
            const cleanerObj = new CleanerObject(initialX, initialY, CLEANER_OBJECT_SIZE, `clean-${i}`);
            cleanerObj.addToWorld(world);
            cleanerObjectsArray.push(cleanerObj.body);
        }


        Events.on(engine, 'collisionStart', handleCollisions);
        Events.on(engine, 'beforeUpdate', updateGame);
        Events.on(engine, 'afterUpdate', afterUpdateGame);

        Render.run(render);
        runner = Runner.create();
    }

    function handleCollisions(event) {
        const pairs = event.pairs;
        for (let i = 0; i < pairs.length; i++) {
            const pair = pairs[i];
            const bodyA = pair.bodyA;
            const bodyB = pair.bodyB;

            let liquifier = null;
            let cleaner = null;
            let otherBody = null;

            // Check for Liquifier + Dynamic Object collision
            if (bodyA.label && bodyA.label.startsWith(LIQUIFIER_OBJECT_LABEL_PREFIX) && !bodyB.isStatic && bodyB !== vitaBody && bodyB !== coralBody.body && !bodyB.label.startsWith(CLEANER_OBJECT_LABEL_PREFIX)) {
                liquifier = bodyA; otherBody = bodyB;
            } else if (bodyB.label && bodyB.label.startsWith(LIQUIFIER_OBJECT_LABEL_PREFIX) && !bodyA.isStatic && bodyA !== vitaBody && bodyA !== coralBody.body && !bodyA.label.startsWith(CLEANER_OBJECT_LABEL_PREFIX)) {
                liquifier = bodyB; otherBody = bodyA;
            }
            if (liquifier && otherBody && !otherBody.label.startsWith('particle-')) {
                liquifyBody(otherBody);
                // Optional: remove liquifier after use: removeBody(liquifier);
            }

            // Check for Cleaner + (Particle or Dynamic Object) collision
            if (bodyA.label && bodyA.label.startsWith(CLEANER_OBJECT_LABEL_PREFIX) && bodyB !== vitaBody && bodyB !== coralBody.body && !bodyB.label.startsWith(LIQUIFIER_OBJECT_LABEL_PREFIX)) {
                cleaner = bodyA; otherBody = bodyB;
            } else if (bodyB.label && bodyB.label.startsWith(CLEANER_OBJECT_LABEL_PREFIX) && bodyA !== vitaBody && bodyA !== coralBody.body && !bodyA.label.startsWith(LIQUIFIER_OBJECT_LABEL_PREFIX)) {
                cleaner = bodyB; otherBody = bodyA;
            }
            if (cleaner && otherBody) {
                removeBody(otherBody, otherBody.label.startsWith('particle-'));
                 // Optional: remove cleaner after use: removeBody(cleaner);
            }
        }
    }
    
    function updateGame() {
        if (!isGameActive || !vitaBody) return;
        isVitaOnGround = false; // Reset per frame

        // Determine if Vita is on any standable surface
        const potentialSupports = Composite.allBodies(world).filter(body => body !== vitaBody && !body.isSensor);
        for (const supportBody of potentialSupports) {
            if (!supportBody) continue;
            const collisions = Query.collides(vitaBody, [supportBody]);
            if (collisions.length > 0) {
                for (const collision of collisions) {
                    if (collision.collided && collision.normal) {
                        let normalY = collision.normal.y;
                        if (collision.bodyA === vitaBody && normalY < -0.3) isVitaOnGround = true;
                        else if (collision.bodyB === vitaBody && normalY > 0.3) isVitaOnGround = true;
                        if (isVitaOnGround) break;
                    }
                }
            }
            if (isVitaOnGround) break;
        }

        handlePlayerMovement();
        if (coralBody) {
            coralBody.updateAI(world, [vitaBody, ...boxStack, ...bouncyBallsArray, ...liquifierObjectsArray, ...cleanerObjectsArray]);
        }
        
        // Bouncy platform logic (simplified from vitachaos2.js)
        const allBouncyPlatforms = [...bouncyPlatformObjects, ...Composite.allBodies(world).filter(b => b.isStatic && b.label && b.label.startsWith("BouncyPlatform") && !bouncyPlatformObjects.includes(b))];
        const dynamicObjects = [vitaBody, coralBody.body, ...boxStack, ...bouncyBallsArray, ...liquifiedParticlesArray, ...liquifierObjectsArray, ...cleanerObjectsArray].filter(obj => obj && !obj.isStatic);

        allBouncyPlatforms.forEach(platform => {
            dynamicObjects.forEach(obj => {
                if (obj === platform) return;
                const collisions = Query.collides(obj, [platform]);
                if (collisions.length > 0) {
                    for (const collision of collisions) {
                        if (collision.collided && collision.normal) {
                            let isObjectOnTop = false;
                            if ((collision.bodyA === obj && collision.normal.y < -0.3) || (collision.bodyB === obj && collision.normal.y > 0.3)) {
                                isObjectOnTop = true;
                            }
                            if (isObjectOnTop) {
                                const upwardForceMagnitude = obj.mass * world.gravity.y * BOUNCY_PLATFORM_ACTIVE_FORCE_MULTIPLIER;
                                Body.applyForce(obj, obj.position, { x: 0, y: -upwardForceMagnitude });
                            }
                        }
                    }
                }
            });
        });


        // Grab/throw with 'e' key
        if (keysPressed['e']) {
            // Only trigger once per keypress
            if (!keysPressed.eWasPressed) {
                keysPressed.eWasPressed = true;
                toggleGrabReleaseObject();
            }
        } else if (keysPressed['f'] && heldObject && !keysPressed.fWasPressed) { // Already handled in keydown, but good to be explicit
            if(!keysPressed.fWasPressed) { // Check again to ensure single action
                // stickHeldObjectToNearest(); // This is now called directly in keydown
            }
        } else {
            keysPressed.eWasPressed = false;
        }
        checkForRespawns();
}


    function toggleGrabReleaseObject() {
        if (heldObject) {
            // Release the currently held object
            releaseObject();
        } else {
            // Try to grab a nearby object
            grabNearestObject();
        }
    }

    function grabNearestObject() {
        // Find the nearest non-static object within grab radius
        let nearestObject = null;
        let minDistanceSq = GRAB_RADIUS * GRAB_RADIUS; // Use squared distance for efficiency
        
        const allDynamicBodies = [...boxStack, ...bouncyBallsArray.filter(t => !t.isStatic)];
        allDynamicBodies.push(...liquifierObjectsArray, ...cleanerObjectsArray); // Add new grabbable types
        
       

        allDynamicBodies.forEach(body => {
            if (body.isStatic || body === vitaBody) { // Simpler check, force triangles are already filtered if static
                return;
            }
            
            // Calculate distance between Vita and the object
            const dx = body.position.x - vitaBody.position.x;
            const dy = body.position.y - vitaBody.position.y;
            const distSq = dx * dx + dy * dy;
            
            if (distSq < minDistanceSq) {
                minDistanceSq = distSq;
                nearestObject = body;
            }
        });
        
        if (nearestObject) {
            heldObject = nearestObject;
            
            // Store original collision filters and then modify to prevent self-collision while holding
            heldObject.originalCollisionFilter = { ...heldObject.collisionFilter };
            vitaBody.originalCollisionFilterForGrab = { ...vitaBody.collisionFilter };

            const noCollideGroup = -1; // Objects in the same negative group don't collide
            Body.set(heldObject, 'collisionFilter', { ...heldObject.originalCollisionFilter, group: noCollideGroup });
            Body.set(vitaBody, 'collisionFilter', { ...vitaBody.originalCollisionFilterForGrab, group: noCollideGroup });
            
            const isFacingRight = vitaBody.render.sprite.xScale > 0;
            const actualPointA = {
                x: isFacingRight ? GRAB_POINT_OFFSET.x : -GRAB_POINT_OFFSET.x,
                y: GRAB_POINT_OFFSET.y
            };
            
            // Create a constraint to "hold" the object
            grabConstraint = Constraint.create({
                bodyA: vitaBody,
                pointA: actualPointA,
                bodyB: heldObject,
                pointB: { x: 0, y: 0 }, // Attach to center of held object
                stiffness: 0.07,        // Lowered to match original's typical feel
                damping: 0.1,           // Added from original
                length: Vector.magnitude(GRAB_POINT_OFFSET) + // Using GRAB_POINT_OFFSET magnitude
                        (heldObject.circleRadius || Math.max(heldObject.bounds.max.x - heldObject.bounds.min.x, heldObject.bounds.max.y - heldObject.bounds.min.y) / 3),
                render: {
                    visible: true,
                    lineWidth: 2,
                    strokeStyle: '#FFFFFF'
                }
            });
            Composite.add(world, grabConstraint);
        }
    }


   function releaseObject() {
        if (!heldObject || !grabConstraint) return;
        
        // Remove the constraint
        Composite.remove(world, grabConstraint);
        grabConstraint = null;

        // Restore original collision filters
        if (heldObject.originalCollisionFilter) {
            Body.set(heldObject, 'collisionFilter', heldObject.originalCollisionFilter);
            delete heldObject.originalCollisionFilter;
        }
        if (vitaBody.originalCollisionFilterForGrab) {
             Body.set(vitaBody, 'collisionFilter', vitaBody.originalCollisionFilterForGrab);
             delete vitaBody.originalCollisionFilterForGrab;
        }

        // Throwing logic (similar to kick, towards mouse) - matches original
        const mousePos = render.mouse.position; // Use render.mouse.position
        let throwDirection = Vector.sub(mousePos, vitaBody.position);
        if (Vector.magnitudeSquared(throwDirection) === 0) {
            // Default throw direction if mouse is exactly on Vita (e.g., throw right)
            throwDirection = { x: vitaBody.render.sprite.xScale > 0 ? 1 : -1, y: 0 };
        }
        throwDirection = Vector.normalise(throwDirection);
        
        const throwForceVector = Vector.mult(throwDirection, THROW_FORCE_MAGNITUDE);
        Body.applyForce(heldObject, heldObject.position, throwForceVector);
        
        // Reset held object and constraint
        heldObject = null;
    }




    window.pauseGame = function() { if(isGameActive) Runner.stop(runner); isGameActive = false; };
    window.resumeGame = function() { if(!isGameActive) Runner.run(runner, engine); isGameActive = true; };

    function afterUpdateGame() {
        if (!isGameActive || !vitaBody || !render) return;
        Render.lookAt(render, vitaBody, CAMERA_PADDING, true);
    }

    function handlePlayerMovement() {
        if (keysPressed['a'] || keysPressed['arrowleft']) {
            Body.applyForce(vitaBody, vitaBody.position, { x: -PLAYER_MOVE_FORCE_FACTOR * vitaBody.mass, y: 0 });
            if (vitaBody.render.sprite) vitaBody.render.sprite.xScale = -Math.abs(VITA_SPRITE_X_SCALE);
        }
        if (keysPressed['d'] || keysPressed['arrowright']) {
            Body.applyForce(vitaBody, vitaBody.position, { x: PLAYER_MOVE_FORCE_FACTOR * vitaBody.mass, y: 0 });
            if (vitaBody.render.sprite) vitaBody.render.sprite.xScale = Math.abs(VITA_SPRITE_X_SCALE);
        }
        if ((keysPressed['w'] || keysPressed['arrowup'] || keysPressed[' ']) && isVitaOnGround) {
            Body.applyForce(vitaBody, vitaBody.position, { x: 0, y: -PLAYER_JUMP_FORCE_MULTIPLIER * vitaBody.mass });
        }
    }

    function liquifyBody(bodyToLiquify) {
        if (!bodyToLiquify || bodyToLiquify.isStatic || bodyToLiquify === vitaBody || bodyToLiquify === coralBody.body || bodyToLiquify.isSensor || bodyToLiquify.label.startsWith('particle-')) {
            return false;
        }
        const originalPosition = { ...bodyToLiquify.position };
        const particleColors = getObjectColors(bodyToLiquify); // Use the multi-color function
        const originalLabel = bodyToLiquify.label;

        removeBody(bodyToLiquify, false, true); // Mark as being liquified

        let effectiveSize = bodyToLiquify.circleRadius ? bodyToLiquify.circleRadius * 2 : ( (bodyToLiquify.bounds.max.x - bodyToLiquify.bounds.min.x) + (bodyToLiquify.bounds.max.y - bodyToLiquify.bounds.min.y) ) / 2;
        const numParticlesToCreate = Math.max(MIN_PARTICLES_ON_LIQUIFY, Math.floor(effectiveSize * 1.5)); // Adjusted particle count

        for (let i = 0; i < numParticlesToCreate; i++) {
            const angle = Math.random() * Math.PI * 2;
            const offsetMagnitude = Math.random() * (bodyToLiquify.circleRadius || PARTICLE_SIZE * 3);
            const particleX = originalPosition.x + Math.cos(angle) * offsetMagnitude;
            const particleY = originalPosition.y + Math.sin(angle) * offsetMagnitude;
            const chosenParticleColor = particleColors[i % particleColors.length];

            const particle = Bodies.rectangle(particleX, particleY, PARTICLE_SIZE, PARTICLE_SIZE, {
                friction: 0.05, restitution: 0.4, density: 0.0005, // Lighter particles
                label: `particle-${originalLabel || 'unknown'}-${Date.now()}-${i}`,
                render: { fillStyle: chosenParticleColor }
            });
            Composite.add(world, particle);
            liquifiedParticlesArray.push(particle);
        }
        console.log(`Liquified object: ${originalLabel || 'Unknown'} by action.`);
        return true;
    }

    function getObjectColors(body) { // Simplified from vitachaos2.js
        if (body.render) {
            if (Array.isArray(body.render.multiFillStyles) && body.render.multiFillStyles.length > 0) {
                return body.render.multiFillStyles;
            }
            if (body.render.fillStyle && body.render.fillStyle !== 'transparent') {
                return [body.render.fillStyle];
            }
        }
        // Fallback colors based on label if render properties are not set
        if (body.label) {
            if (body.label.startsWith('Box-')) return ['#A0522D', '#8B4513']; // Brown shades for boxes
            if (body.label.startsWith('Ball-')) return ['#FFC0CB', '#FFB6C1']; // Pink shades for balls
        }
        return ['#CCCCCC', '#AAAAAA']; // Default gray shades
    }


    function vitaLiquifyNearestObject() {
        if (!vitaBody) return;
        let nearestObject = null;
        let minDistanceSq = LIQUIFY_RADIUS_VITA * LIQUIFY_RADIUS_VITA;
        
        const allDynamicBodies = [...boxStack, ...bouncyBallsArray, ...liquifierObjectsArray, ...cleanerObjectsArray];

        allDynamicBodies.forEach(body => {
            if (body.isStatic || body === vitaBody || body === coralBody.body || body.isSensor || body.label.startsWith('particle-') ||
                body.label.startsWith(LIQUIFIER_OBJECT_LABEL_PREFIX) || body.label.startsWith(CLEANER_OBJECT_LABEL_PREFIX)) { // Vita doesn't liquify special items
                return;
            }
            const dx = body.position.x - vitaBody.position.x;
            const dy = body.position.y - vitaBody.position.y;
            const distSq = dx * dx + dy * dy;
            if (distSq < minDistanceSq) {
                minDistanceSq = distSq;
                nearestObject = body;
            }
        });
        if (nearestObject) liquifyBody(nearestObject);
    }

    function vitaCleanupNearbyParticles() {
        if (!vitaBody) return;
        const vitaPos = vitaBody.position;
        let particlesToRemove = [];

        liquifiedParticlesArray.forEach(particle => {
            const distSq = Vector.magnitudeSquared(Vector.sub(particle.position, vitaPos));
            if (distSq < CLEANUP_RADIUS_VITA * CLEANUP_RADIUS_VITA) {
                Composite.remove(world, particle);
                particlesToRemove.push(particle);
            }
        });
        if (particlesToRemove.length > 0) {
            liquifiedParticlesArray = liquifiedParticlesArray.filter(p => !particlesToRemove.includes(p));
            console.log(`Vita cleaned up ${particlesToRemove.length} particles.`);
        }
    }

    function removeBody(bodyToRemove, isParticle = false, isBeingLiquified = false) {
        if (!bodyToRemove || bodyToRemove.isStatic) return false; // Cannot remove static bodies this way

        Composite.remove(world, bodyToRemove);
        let removedFromArray = false;

        const arraysToSearch = [
            { arr: boxStack, name: 'boxStack' },
            { arr: bouncyBallsArray, name: 'bouncyBallsArray' },
            { arr: liquifierObjectsArray, name: 'liquifierObjectsArray' },
            { arr: cleanerObjectsArray, name: 'cleanerObjectsArray' },
            { arr: liquifiedParticlesArray, name: 'liquifiedParticlesArray', isParticleArray: true }
        ];

        for (const entry of arraysToSearch) {
            const index = entry.arr.indexOf(bodyToRemove);
            if (index > -1) {
                entry.arr.splice(index, 1);
                // Update global window references if they exist (for potential editor interaction)
                if (window[entry.name]) window[entry.name] = entry.arr;
                removedFromArray = true;
                break; 
            }
        }
        
        if (removedFromArray && !isBeingLiquified && !isParticle) {
             console.log(`Removed object: ${bodyToRemove.label || 'Unknown'}`);
        } else if (isParticle && removedFromArray) {
            // console.log(`Removed particle: ${bodyToRemove.label}`);
        }
        return removedFromArray;
    }


    function checkForRespawns() {
        const respawnableBodies = Composite.allBodies(world).filter(body =>
            body && !body.isStatic && body !== vitaBody && body !== coralBody.body // Don't respawn Coral this way
        );
        respawnableBodies.forEach(body => {
            if (body.position.y > RESPAWN_Y_LIMIT ||
                body.position.x < -RESPAWN_X_BUFFER ||
                body.position.x > GAME_WIDTH + RESPAWN_X_BUFFER) {
                
                // For particles, just remove them instead of respawning
                if (body.label && body.label.startsWith('particle-')) {
                    removeBody(body, true);
                } else {
                    // Respawn other objects
                    Body.setPosition(body, {
                        x: Math.random() * (GAME_WIDTH - 100) + 50,
                        y: Math.random() * 100 
                    });
                    Body.setVelocity(body, { x: 0, y: 0 });
                    Body.setAngularVelocity(body, 0);
                    Body.setAngle(body, 0);
                }
            }
        });
    }

    function resetVitaPosition() {
        const FLOOR_1_TOP_Y_reset = GAME_HEIGHT - GROUND_HEIGHT;
        const VITA_START_Y_reset = FLOOR_1_TOP_Y_reset - VITA_HEIGHT / 2 - 20;
        Body.setPosition(vitaBody, { x: VITA_START_X, y: VITA_START_Y_reset });
        Body.setVelocity(vitaBody, { x: 0, y: 0 });
        Body.setAngularVelocity(vitaBody, 0);
        Body.setAngle(vitaBody, 0);
    }
    
    function resetCoralPosition() {
        const FLOOR_1_TOP_Y_reset = GAME_HEIGHT - GROUND_HEIGHT;
        const CORAL_START_Y_reset = FLOOR_1_TOP_Y_reset - CORAL_HEIGHT / 2 - 20;
        const CORAL_START_X_reset = GAME_WIDTH * 0.7; // Or some other default
        if (coralBody && coralBody.body) {
            Body.setPosition(coralBody.body, { x: CORAL_START_X_reset, y: CORAL_START_Y_reset });
            Body.setVelocity(coralBody.body, { x: 0, y: 0 });
            Body.setAngularVelocity(coralBody.body, 0);
            Body.setAngle(coralBody.body, 0);
            coralBody.lastActionTime = Date.now(); // Reset AI timers
            coralBody.lastMovementTime = Date.now();
        }
    }


    // --- Game Control Functions ---
    function handleStartGame() {
        clearMenu();
        if (gamePlansContainer) gamePlansContainer.style.display = 'none';
        const controlsInfo = document.getElementById('controls-info');
        if (controlsInfo) controlsInfo.style.display = 'block';

        if (engine && world && vitaBody) {
            resetVitaPosition();
            resetCoralPosition(); // Reset Coral too

            // Reset all movable objects (simplified)
            const allMovable = [...boxStack, ...bouncyBallsArray, ...liquifierObjectsArray, ...cleanerObjectsArray];
            const FLOOR_1_TOP_Y = GAME_HEIGHT - GROUND_HEIGHT;
            const FLOOR_2_TOP_Y = (GAME_HEIGHT - SINGLE_AREA_HEIGHT) - PLATFORM_THICKNESS;

            allMovable.forEach((obj, index) => {
                const area = (index % NUM_AREAS_VERTICAL) + 1;
                const floorTopY = area === 1 ? FLOOR_1_TOP_Y : FLOOR_2_TOP_Y;
                let randomX = Math.random() * (GAME_WIDTH - 100) + 50;
                let randomY = floorTopY - (obj.circleRadius || obj.height || BOX_SIZE) / 2 - (Math.random() * 100 + 50);
                Body.setPosition(obj, { x: randomX, y: randomY });
                Body.setVelocity(obj, { x: 0, y: 0 });
                Body.setAngularVelocity(obj, 0);
                Body.setAngle(obj, 0);
            });
            
            // Clear any liquified particles
            liquifiedParticlesArray.forEach(particle => Composite.remove(world, particle));
            liquifiedParticlesArray = [];
            window.liquifiedParticlesArray = liquifiedParticlesArray;

        } else {
            setupGame();
        }
        isGameActive = true;
        Runner.run(runner, engine);
        document.addEventListener('keydown', handlePauseKey);
    }

    function handlePauseKey(event) {
        if (event.key === 'Escape' || event.key === 'p') {
            if (isGameActive) showPauseMenu();
            else if (menuContainer && menuContainer.textContent.includes('Paused')) handleResumeGame();
        }
    }

    function handleResumeGame() {
        clearMenu();
        if (gamePlansContainer) gamePlansContainer.style.display = 'none';
        isGameActive = true;
        Runner.run(runner, engine);
    }

    function handleRestartGame() {
        clearMenu();
        handleStartGame();
    }

    function handleQuitGame() {
        clearMenu();
        showStartMenu();
    }

    function toggleFullscreen() { /* ... (same as vitachaos2.js) ... */ 
        if (!document.fullscreenElement && !document.mozFullScreenElement && !document.webkitFullscreenElement && !document.msFullscreenElement) {
            if (gameContainer.requestFullscreen) gameContainer.requestFullscreen();
            else if (gameContainer.msRequestFullscreen) gameContainer.msRequestFullscreen();
            else if (gameContainer.mozRequestFullScreen) gameContainer.mozRequestFullScreen();
            else if (gameContainer.webkitRequestFullscreen) gameContainer.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
        } else {
            if (document.exitFullscreen) document.exitFullscreen();
            else if (document.msExitFullscreen) document.msExitFullscreen();
            else if (document.mozCancelFullScreen) document.mozCancelFullScreen();
            else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
        }
    }

    function handleResizeOrOrientationChange() {
        if (!render) return;
        calculateGameDimensions();
        RESPAWN_Y_LIMIT = GAME_HEIGHT + 200;

        render.options.width = CANVAS_WIDTH;
        render.options.height = CANVAS_HEIGHT;
        render.canvas.width = CANVAS_WIDTH;
        render.canvas.height = CANVAS_HEIGHT;

        // Reposition static world elements (simplified from vitachaos2.js)
        if (ground1) {
            Body.setPosition(ground1, { x: GAME_WIDTH / 2, y: GAME_HEIGHT - (GROUND_HEIGHT / 2) });
            Body.setVertices(ground1, Bodies.rectangle(GAME_WIDTH / 2, GAME_HEIGHT - (GROUND_HEIGHT / 2), GAME_WIDTH, GROUND_HEIGHT).vertices);
        }
        if (platform2) {
            const platform2_y_center = (GAME_HEIGHT - SINGLE_AREA_HEIGHT) - (PLATFORM_THICKNESS / 2);
            Body.setPosition(platform2, { x: GAME_WIDTH / 2, y: platform2_y_center });
            Body.setVertices(platform2, Bodies.rectangle(GAME_WIDTH / 2, platform2_y_center, GAME_WIDTH, PLATFORM_THICKNESS).vertices);
        }
        if (ceiling) {
            Body.setPosition(ceiling, { x: GAME_WIDTH / 2, y: CEILING_Y_OFFSET });
            Body.setVertices(ceiling, Bodies.rectangle(GAME_WIDTH / 2, CEILING_Y_OFFSET, GAME_WIDTH + WALL_THICKNESS * 2, CEILING_HEIGHT).vertices);
        }
        if (leftWall) {
            Body.setPosition(leftWall, { x: -WALL_THICKNESS / 4, y: GAME_HEIGHT / 2 });
            Body.setVertices(leftWall, Bodies.rectangle(-WALL_THICKNESS / 4, GAME_HEIGHT / 2, WALL_THICKNESS, GAME_HEIGHT * 2).vertices);
        }
        if (rightWall) {
            Body.setPosition(rightWall, { x: GAME_WIDTH + WALL_THICKNESS / 2, y: GAME_HEIGHT / 2 });
            Body.setVertices(rightWall, Bodies.rectangle(GAME_WIDTH + WALL_THICKNESS / 2, GAME_HEIGHT / 2, WALL_THICKNESS, GAME_HEIGHT * 2).vertices);
        }
        
        // Update positions of custom static platforms (simplified)
        // This part would need more robust handling if platforms are dynamically defined relative to GAME_WIDTH/HEIGHT
        // For now, assuming their initial definitions are sufficient or they are manually managed if resize is complex.
    }

    window.addEventListener('resize', handleResizeOrOrientationChange);
    document.addEventListener('fullscreenchange', handleResizeOrOrientationChange);
    document.addEventListener('webkitfullscreenchange', handleResizeOrOrientationChange);
    document.addEventListener('mozfullscreenchange', handleResizeOrOrientationChange);
    document.addEventListener('MSFullscreenChange', handleResizeOrOrientationChange);

    // --- Preload Assets and Initialize Game ---
    // Make sure to have placeholder images at these paths or update them
    const assetsToLoad = [VITA_IMAGE_PATH, CORAL_IMAGE_PATH];
    let assetsLoaded = 0;
    assetsToLoad.forEach(src => {
        const img = new Image();
        img.src = src;
        img.onload = () => {
            assetsLoaded++;
            console.log(`${src} loaded.`);
            if (assetsLoaded === assetsToLoad.length) {
                console.log('All assets loaded successfully');
                showStartMenu();
            }
        };
        img.onerror = () => {
            console.error(`Failed to load ${src}`);
            assetsLoaded++; // Still count it to proceed, game might look odd
            if (assetsLoaded === assetsToLoad.length) {
                showStartMenu(); // Show menu even if some assets fail
            }
        };
    });
    if (assetsToLoad.length === 0) { // If no assets to load, show menu immediately
        showStartMenu();
    }
});
