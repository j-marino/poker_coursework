import sys

import pygame

from poker.resources import screen
from poker.settings import (
    ACTION_BUTTON_HEIGHT,
    ACTION_BUTTON_WIDTH,
    FPS,
    POKERGREEN,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from .ui import Button, ButtonManager


class ScreenManager:
    def __init__(self):
        self.screens = []
        self.current_screen = 0

    def add_screen(self, screen_object):
        self.screens.append(screen_object)

    def load_current_screen(self):
        self.screens[self.current_screen].run_screen()

    def next_screen(self):
        self.current_screen += 1


class Screen:
    def __init__(self, action=None):
        self.action = action

    def run_screen(self):
        if self.action:  # guards against invalid actions such as None
            return self.action()


class GameScreen(Screen):
    def __init__(self, action):  # action is the GameController's game loop
        super().__init__(action)


class StartScreen(Screen):
    def __init__(self, screen_manager):
        super().__init__()
        self.screen_manager = screen_manager
        # a single start button, centred
        self.buttons = ButtonManager({
            "start": Button(SCREEN_WIDTH / 2 - ACTION_BUTTON_WIDTH / 2,
                            SCREEN_HEIGHT / 2 - ACTION_BUTTON_HEIGHT / 2,
                            ACTION_BUTTON_WIDTH, ACTION_BUTTON_HEIGHT,
                            self.increment_stack, "start", WHITE)
        })

    def increment_stack(self):
        self.screen_manager.next_screen()
        self.screen_manager.load_current_screen()

    def run_screen(self):
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.buttons.button_was_clicked():
                        self.buttons.execute_named_button(self.buttons.get_action_name())

            screen.fill(POKERGREEN)
            self.buttons.draw_all_buttons(True)
            pygame.display.update()
            clock.tick(FPS)
