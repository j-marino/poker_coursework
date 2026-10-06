# Reusable UI widgets: buttons, a text input field and a button manager.
import pygame

from .resources import font_consolas, info_font, money_font, screen
from .settings import BLACK, HOVER_GREY, PLACEHOLDER_GREY, SCARY_RED, WHITE


class Button(pygame.Rect):
    def __init__(self, x, y, width, height, action, text, colour):
        super().__init__(x, y, width, height)
        self.action = action
        self.text = font_consolas.render(text, True, BLACK)
        self.colour = colour
        self.hover_colour = HOVER_GREY
        self.active = True  # inactive buttons aren't drawn or clickable

    def render_button_text(self):
        text_rect = self.text.get_rect(center=self.center)
        screen.blit(self.text, text_rect)

    def draw_button(self):
        if self.active:
            colour = self.hover_colour if self.is_hovering_over_button() else self.colour
            pygame.draw.rect(screen, colour, self)
            self.render_button_text()  # on top of the rectangle

    def is_hovering_over_button(self):
        return self.collidepoint(pygame.mouse.get_pos())

    def was_clicked(self):
        return self.active and self.collidepoint(pygame.mouse.get_pos())

    def run_action(self):
        return self.action()


class TextField(pygame.Rect):
    def __init__(self, x, y, width, height, placeholder=""):
        super().__init__(x, y, width, height)
        self.active = False  # not accepting keystrokes by default
        self.text = ""
        self.colour = WHITE
        self.placeholder = placeholder
        self.show_error = False

    def draw_text_input(self):
        if not self.active:
            return

        pygame.draw.rect(screen, self.colour, self)  # box first
        if self.text:
            screen.blit(money_font.render(self.text, True, BLACK), (self.x + 5, self.y + 5))
        else:
            screen.blit(money_font.render(str(self.placeholder), True, PLACEHOLDER_GREY), (self.x + 5, self.y + 5))

    def handle_events(self, event):
        # Update the field from an event. Returns the text when enter is pressed, else False.
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.collidepoint(pygame.mouse.get_pos()):
                self.active = True  # keystrokes now type into the field
            else:
                self.active = False
                self.text = ""

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                return self.text
            else:
                self.text += event.unicode  # unicode normalises the key press

        return False

    def get_wrong_response(self, above_box, error_message):
        # Rendered error message plus its position, above or below the box.
        error_surface = info_font.render(error_message, True, SCARY_RED)
        error_rect = error_surface.get_rect()

        if above_box:
            message_y = self.y - error_rect.height
        else:
            message_y = self.y + self.height + error_rect.height

        return error_surface, (self.x, message_y)

    def set_draw_error(self, expression):
        self.show_error = expression

    def reset_input(self):
        self.text = ""


class ButtonManager:
    def __init__(self, buttons):
        self.buttons = buttons  # dict of button_name -> Button

    def button_was_clicked(self):
        return any(button.was_clicked() for button in self.buttons.values())

    def execute_named_button(self, button_name):
        self.buttons[button_name].run_action()

    def get_action_name(self):
        # Name of the button under the mouse, or False if there isn't one.
        for button_name, button in self.buttons.items():
            if button.was_clicked():
                return button_name
        return False

    def draw_all_buttons(self, is_human_turn):
        if is_human_turn:  # buttons only appear on the human's turn, for clarity
            for button in self.buttons.values():
                button.draw_button()

    def get_button_object(self, name):
        return self.buttons.get(name)
