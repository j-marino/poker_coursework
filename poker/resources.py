# Pygame initialisation plus every font and image the game uses.
#
# Importing this module opens the window. Card images are loaded lazily and cached,
# so each of the 52 faces is read from disk at most once.
from pathlib import Path

import pygame

from poker.settings import (
    CARD_HEIGHT,
    CARD_WIDTH,
    DEALER_BUTTON_HEIGHT,
    DEALER_BUTTON_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TABLE_HEIGHT,
    TABLE_WIDTH,
)

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# Fonts
info_font = pygame.font.SysFont("consolas", 19)
info_font.set_bold(True)
font_consolas = pygame.font.SysFont("Consolas", 35)
font_verdana = pygame.font.SysFont("Verdana", 30)
turn_indicator_font = pygame.font.SysFont("Consolas", 25)
money_font = pygame.font.SysFont("Consolas", 25)


def _load_scaled(relative_path, size):
    image = pygame.image.load(str(ASSET_DIR / relative_path)).convert_alpha()
    return pygame.transform.scale(image, size)


poker_table = _load_scaled("table/poker_table.png", (TABLE_WIDTH, TABLE_HEIGHT))
card_back = _load_scaled("card_backs/card_back_red.png", (CARD_WIDTH, CARD_HEIGHT))
dealer_button = _load_scaled("dealer_button/dealer_button.png", (DEALER_BUTTON_WIDTH, DEALER_BUTTON_HEIGHT))

_card_image_cache = {}


def get_card_image(card_name):
    # Return the scaled face image for a card name such as 'ace_of_spades'.
    if card_name not in _card_image_cache:
        _card_image_cache[card_name] = _load_scaled(f"cards/{card_name}.png", (CARD_WIDTH, CARD_HEIGHT))
    return _card_image_cache[card_name]
