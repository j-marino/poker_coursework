# Constants and screen-layout maths shared across the game.
#
# Everything here is plain data (no surfaces are loaded), so it is safe to import
# from anywhere. Positions are derived from the screen size so the table scales.
import pygame

#
# Screen
#
SCREEN_WIDTH, SCREEN_HEIGHT = 1600, 900
FPS = 60

#
# Colours
#
POKERGREEN = pygame.Color("#3c7257")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)                      # button text
LIGHT_BLACK = (200, 200, 200)          # action names
HOVER_GREY = (190, 190, 190)           # button hover colour
RED = (255, 140, 140)                  # turn indicator
PLACEHOLDER_GREY = (150, 150, 150)
SCARY_RED = (200, 20, 20)              # error messages

#
# Game rules
#
STARTING_MONEY = 1000
MONTE_CARLO_SIMULATIONS = 16000 # can change according to system -> this is used as sort of a buffer of time so the player can comprehend a turn and they have a delay
# this is a hacky fix please change to real time delay (perhaps ASYNC so there are calculations done in the background during a time wait)

# AI seats, clockwise from the player's left. The key is the seat number used
# to look up screen coordinates. Names are kept short (<= 6 chars) to fit.
AI_NAMES = {
    1: "sharky",
    2: "rusher",
    3: "stackz",
    4: "sphinx",
    5: "richy",
}

#
# Action buttons
#
ACTION_BUTTON_WIDTH, ACTION_BUTTON_HEIGHT = 120, 38

# Four buttons equally spaced across the screen at 20/40/60/80% of its width.
# Half a button width is subtracted because rects are drawn from the top left.
ACTION_BUTTON_X = {
    "check": int(SCREEN_WIDTH * 0.20) - ACTION_BUTTON_WIDTH / 2,
    "fold": int(SCREEN_WIDTH * 0.40) - ACTION_BUTTON_WIDTH / 2,
    "call": int(SCREEN_WIDTH * 0.60) - ACTION_BUTTON_WIDTH / 2,
    "raise": int(SCREEN_WIDTH * 0.80) - ACTION_BUTTON_WIDTH / 2,
}
ACTION_BUTTON_Y = SCREEN_HEIGHT - 50      # shared by every action button

#
# Cards and table
#
CARD_WIDTH = 125
CARD_HEIGHT = 182
TABLE_WIDTH = 1400                      # original image is 735x350, keep the ratio
TABLE_HEIGHT = 700

DEALER_BUTTON_WIDTH, DEALER_BUTTON_HEIGHT = 50, 50

HAND_CARD_X_GAP = 5                       # horizontal gap between a player's 2 cards
HAND_CARD_Y_GAP = 290                     # distance of the hand cards from the bottom

# The human's hand cards sit bottom-middle.
HAND_CARD_X = [SCREEN_WIDTH / 2 - CARD_WIDTH - HAND_CARD_X_GAP, SCREEN_WIDTH / 2]
HAND_CARD_Y = SCREEN_HEIGHT - HAND_CARD_Y_GAP

# Community cards: 5 cards with a gap between each, centred on the screen.
COMMUNITY_CARD_X_GAP = 10
COMMUNITY_CARD_Y_GAP = SCREEN_HEIGHT / 2 + CARD_HEIGHT / 2
TOTAL_CARDS_WIDTH = 5 * CARD_WIDTH + 4 * COMMUNITY_CARD_X_GAP
START_X = (SCREEN_WIDTH - TOTAL_CARDS_WIDTH) / 2
COMMUNITY_CARD_X = [START_X + i * (CARD_WIDTH + COMMUNITY_CARD_X_GAP) for i in range(5)]
COMMUNITY_CARD_Y = SCREEN_HEIGHT - COMMUNITY_CARD_Y_GAP

# The mathematical centre of the table looks off, so nudge it upwards.
POKER_TABLE_Y_SPACER = 40
POKER_TABLE_X = (SCREEN_WIDTH - TABLE_WIDTH) / 2
POKER_TABLE_Y = (SCREEN_HEIGHT - TABLE_HEIGHT) / 2 - POKER_TABLE_Y_SPACER

#
# AI seat positions (clockwise from the player's left)
#
# The left two seats start at 23% of the screen width, so the right two sit at 77%.
AI_POS_X = {
    1: [SCREEN_WIDTH * 0.23 - CARD_WIDTH * 2 - HAND_CARD_X_GAP, SCREEN_WIDTH * 0.23 - CARD_WIDTH],
    2: [SCREEN_WIDTH * 0.23 - CARD_WIDTH * 2 - HAND_CARD_X_GAP, SCREEN_WIDTH * 0.23 - CARD_WIDTH],
    3: [HAND_CARD_X[0], HAND_CARD_X[1]],
    4: [SCREEN_WIDTH * 0.77, SCREEN_WIDTH * 0.77 + CARD_WIDTH + HAND_CARD_X_GAP],
    5: [SCREEN_WIDTH * 0.77, SCREEN_WIDTH * 0.77 + CARD_WIDTH + HAND_CARD_X_GAP],
}

# The Y positions form an oval around the table (tested at 1080p and 1440p).
Y_SPACER = 15
AI_POS_Y = {
    1: HAND_CARD_Y - CARD_HEIGHT / 2 - Y_SPACER,
    2: SCREEN_HEIGHT * 0.05 + CARD_HEIGHT / 2 - Y_SPACER,
    3: SCREEN_HEIGHT * 0.05 - Y_SPACER,
    4: SCREEN_HEIGHT * 0.05 + CARD_HEIGHT / 2 - Y_SPACER,
    5: HAND_CARD_Y - CARD_HEIGHT / 2 - Y_SPACER,
}


def seat_position(seat):
    # Return ([x1, x2], y) for an AI seat, or None for the human / unknown seats.
    if seat in AI_POS_X and seat in AI_POS_Y:
        return AI_POS_X[seat], AI_POS_Y[seat]
    return None
