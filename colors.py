"""
Color module for Vita Game Hustle.
Provides functions and constants for adding color to game text.
"""

# ANSI color codes
class TextColor:
    """Class containing color constants and formatting functions."""
    # Basic colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    
    # RGB colors for more flexibility
    @staticmethod
    def rgb(r, g, b):
        """Returns ANSI escape code for RGB color."""
        return f"\033[38;2;{r};{g};{b}m"

# Game-specific color scheme
class GameColors:
    """Game-specific color constants for different game elements."""
    # Area colors
    AREA_NAME = TextColor.BOLD + TextColor.BRIGHT_CYAN
    AREA_DESCRIPTION = TextColor.CYAN
    
    # Player colors
    PLAYER_NAME = TextColor.BOLD + TextColor.BRIGHT_GREEN
    PLAYER_STATS = TextColor.GREEN
    PLAYER_MONEY = TextColor.rgb(255, 215, 0)  # Gold color
    
    # Item colors
    ITEM_NAME = TextColor.BRIGHT_YELLOW
    ITEM_DESCRIPTION = TextColor.YELLOW
    ITEM_VALUE = TextColor.rgb(255, 215, 0)  # Gold color
    
    # NPC colors
    NPC_NAME = TextColor.BOLD + TextColor.BRIGHT_MAGENTA
    NPC_DESCRIPTION = TextColor.MAGENTA
    NPC_DIALOG = TextColor.rgb(200, 150, 255)  # Light purple
    NPC_INFLUENCE_ACTIVE = TextColor.BRIGHT_GREEN
    
    
    # Command colors
    COMMAND_PROMPT = TextColor.BOLD + TextColor.BRIGHT_WHITE
    COMMAND_INPUT = TextColor.BRIGHT_WHITE
    
    # Message colors
    SUCCESS_MESSAGE = TextColor.BRIGHT_GREEN
    ERROR_MESSAGE = TextColor.BRIGHT_RED
    WARNING_MESSAGE = TextColor.BRIGHT_YELLOW
    INFO_MESSAGE = TextColor.BRIGHT_BLUE
    AMBIENT_MESSAGE = TextColor.rgb(180, 180, 180)  # Gray
    
    # Computer/Stock colors
    COMPUTER_TEXT = TextColor.rgb(50, 200, 200)  # Cyan
    STOCK_UP = TextColor.BRIGHT_GREEN
    STOCK_DOWN = TextColor.BRIGHT_RED
    STOCK_NEUTRAL = TextColor.BRIGHT_WHITE

# Utility functions for colored text
def colorize(text, color):
    """Wraps text in the specified color and resets afterward."""
    return f"{color}{text}{TextColor.RESET}"

def print_colored(text, color):
    """Prints text in the specified color."""
    print(colorize(text, color))

def format_area_name(name):
    """Format area name with appropriate color."""
    return colorize(name, GameColors.AREA_NAME)

def format_area_description(description):
    """Format area description with appropriate color."""
    return colorize(description, GameColors.AREA_DESCRIPTION)

def format_item_name(name):
    """Format item name with appropriate color."""
    return colorize(name, GameColors.ITEM_NAME)

def format_item_description(description):
    """Format item description with appropriate color."""
    return colorize(description, GameColors.ITEM_DESCRIPTION)

def format_npc_name(name):
    """Format NPC name with appropriate color."""
    return colorize(name, GameColors.NPC_NAME)

def format_npc_description(description):
    """Format NPC description with appropriate color."""
    return colorize(description, GameColors.NPC_DESCRIPTION)

def format_money(amount):
    """Format money amount with appropriate color."""
    return colorize(f"${amount:.2f}", GameColors.PLAYER_MONEY)

def format_success(message):
    """Format success message with appropriate color."""
    return colorize(message, GameColors.SUCCESS_MESSAGE)

def format_error(message):
    """Format error message with appropriate color."""
    return colorize(message, GameColors.ERROR_MESSAGE)

def format_warning(message):
    """Format warning message with appropriate color."""
    return colorize(message, GameColors.WARNING_MESSAGE)

def format_info(message):
    """Format info message with appropriate color."""
    return colorize(message, GameColors.INFO_MESSAGE)

def format_ambient(message):
    """Format ambient message with appropriate color."""
    return colorize(message, GameColors.AMBIENT_MESSAGE)