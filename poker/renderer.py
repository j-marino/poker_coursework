# Everything that draws the poker table. Reads game state, never changes it.
from poker.resources import (
    card_back,
    dealer_button,
    font_consolas,
    font_verdana,
    get_card_image,
    info_font,
    money_font,
    poker_table,
    screen,
    turn_indicator_font,
)
from poker.settings import (
    CARD_HEIGHT,
    CARD_WIDTH,
    COMMUNITY_CARD_X,
    COMMUNITY_CARD_Y,
    DEALER_BUTTON_HEIGHT,
    HAND_CARD_X,
    HAND_CARD_X_GAP,
    HAND_CARD_Y,
    LIGHT_BLACK,
    POKER_TABLE_X,
    POKER_TABLE_Y,
    POKERGREEN,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    seat_position,
)

LABEL_HEIGHT_SPACER = 5  # gap between a label and the cards beneath it


class TableRenderer:
    def __init__(self, game):
        self.game = game  # the GameController whose state is drawn

    #
    # Cards
    #
    @staticmethod
    def _draw_card_face(card):
        screen.blit(get_card_image(card.get_name()), (card.x, card.y))

    @staticmethod
    def _draw_card_back(card):
        screen.blit(card_back, (card.x, card.y))

    def draw_cards(self):
        # active_players, not players: a folded player's cards disappear
        for player in self.game.active_players:
            for card in player.hand:
                if card.has_pos():
                    if player.is_human:
                        self._draw_card_face(card)
                    else:
                        self._draw_card_back(card)  # the human must not see AI cards until the end

        for card in self.game.community_cards:
            if card.has_pos():
                self._draw_card_face(card)

    def reveal_ai_cards(self):
        # Draw the AI hands face up. Only players still in the hand have to show.
        for player in self.game.active_players:
            if not player.is_human:
                for card in player.hand:
                    if card.has_pos():
                        self._draw_card_face(card)

    def draw_table(self):
        screen.blit(poker_table, (POKER_TABLE_X, POKER_TABLE_Y))

    #
    # Labels
    #
    @staticmethod
    def _above_hand_rect(text_surface, player):
        # Rect centred above a player's hand cards, or None if they have no seat.
        text_rect = text_surface.get_rect()
        # middle of the 2 hand cards, minus half the text width
        if player.is_human:
            text_rect.x = HAND_CARD_X[1] - 0.5 * HAND_CARD_X_GAP - text_rect.width * 0.5
            text_rect.y = HAND_CARD_Y - text_rect.height - LABEL_HEIGHT_SPACER
            return text_rect

        position = seat_position(player.seat)
        if position is None:
            return None
        x_coords, y_coord = position
        text_rect.x = x_coords[1] - 0.5 * HAND_CARD_X_GAP - text_rect.width * 0.5
        text_rect.y = y_coord - text_rect.height - LABEL_HEIGHT_SPACER
        return text_rect

    def draw_winner_text(self, winner):
        winner_text = turn_indicator_font.render("WINNER", True, WHITE)
        text_rect = self._above_hand_rect(winner_text, winner)
        if text_rect:
            screen.blit(winner_text, text_rect)

    def draw_turn_indicator(self, current_player):
        # A "my turn" label above whoever is acting.
        if self.game.check_post_river() or self.game.showdown_running:
            return

        turn_text = turn_indicator_font.render("my turn", True, RED)
        text_rect = self._above_hand_rect(turn_text, current_player)
        if text_rect:
            screen.blit(turn_text, text_rect)

    def draw_ai_names(self):
        # beneath the left hand card, leaving room on the right for their action
        for player in self.game.players:
            position = seat_position(player.seat)
            if not player.is_human and position:
                x_coords, y_coord = position
                screen.blit(font_verdana.render(player.name, True, WHITE), (x_coords[0], y_coord + CARD_HEIGHT))

    def draw_action_names(self):
        # 'raise', 'call', 'fold' or 'check' beside an AI's name.
        for player in self.game.players:
            position = seat_position(player.seat)
            if not player.is_human and position and player.get_action_name() != "":
                x_coords, y_coord = position
                action_text = font_verdana.render(player.get_action_name(), True, LIGHT_BLACK)
                screen.blit(action_text, (x_coords[1], y_coord + CARD_HEIGHT))  # under the right hand card

    def draw_action_value(self):
        # The amount an AI has bet this round, e.g. call -> '20'.
        round_bets = self.game.banker.current_round_bets
        for player in self.game.active_players:
            if player.is_human or player not in round_bets:
                continue
            if player.action_name in ("fold", "check", ""):
                continue

            position = seat_position(player.seat)
            if position:
                x_coords, y_coord = position
                money_text = font_verdana.render(str(round_bets[player]), True, LIGHT_BLACK)
                screen.blit(money_text, (x_coords[1] + 80, y_coord + CARD_HEIGHT)) # TODO: make this a constant, not a magic number

    #
    # Money
    #
    def draw_pot_money(self):
        pot_text = money_font.render("pot £" + str(self.game.banker.pot), True, WHITE)
        text_rect = pot_text.get_rect()
        # centred on the middle community card, just above it
        screen.blit(pot_text, (COMMUNITY_CARD_X[2] + abs(text_rect.width - CARD_WIDTH) / 2,
                              COMMUNITY_CARD_Y - text_rect.height))

    def _draw_blind_label(self, player, x, y):
        # Pre-flop only: label the small and big blind with how much they paid.
        banker = self.game.banker
        if player == self.game.small_blind:
            label = "small blind £" + str(banker.small_blind_bet)
        elif player == self.game.big_blind:
            label = "big blind £" + str(banker.big_blind_bet)
        else:
            return
        screen.blit(info_font.render(label, True, WHITE), (x, y))

    def draw_player_money(self):
        pre_flop = self.game.game_turn < 1

        for player in self.game.players:
            bank_text = money_font.render("£" + str(player.bank), True, WHITE)
            text_height = bank_text.get_rect().height

            if player.is_human:
                # right underneath the cards, lined up with the left hand card
                x = HAND_CARD_X[0]
                y = HAND_CARD_Y + CARD_WIDTH + text_height * 3.5 # TODO: PLEASE REMOVE MAGIC NUMBERS, THIS IS A HACKY FIX FOR THE LABELS BEING TOO CLOSE TO THE CARDS
                label_x = HAND_CARD_X[1]
            else:
                position = seat_position(player.seat)
                if position is None:
                    continue
                x_coords, y_coord = position
                x = x_coords[0]
                y = y_coord + CARD_WIDTH + text_height * 4.5  # * 4 is a spacer for the name TODO: remove magic nums
                label_x = x_coords[1]

            screen.blit(bank_text, (x, y))
            if pre_flop:
                self._draw_blind_label(player, label_x, y)

    #
    # Other table items
    #
    def draw_dealer_button(self):
        # Bottom left of the dealer's left hand card.
        dealer_player = self.game.dealer.dealer_button
        if dealer_player not in self.game.players:
            return

        if dealer_player.is_human:
            x, y = HAND_CARD_X[0], HAND_CARD_Y
        else:
            position = seat_position(dealer_player.seat)
            if position is None:
                return
            x, y = position[0][0], position[1]

        screen.blit(dealer_button, (x, y + CARD_HEIGHT - DEALER_BUTTON_HEIGHT))

    def draw_game_info(self):
        # Key numbers in the top right corner.
        banker = self.game.banker
        bet_x = SCREEN_WIDTH - 180
        blind_x = SCREEN_WIDTH - 350
        top = 10
        line_height = 25

        lines = [
            (f"bet call: £{banker.call_value}", bet_x, top),
            (f"minraise: £{banker.min_raise}", bet_x, top + line_height),
            (f"s.blind: £{banker.small_blind_bet}", blind_x, top),
            (f"b.blind: £{banker.big_blind_bet}", blind_x, top + line_height),
        ]
        for text, x, y in lines:
            screen.blit(info_font.render(text, True, WHITE), (x, y))

    def draw_raise_error(self):
        message = "min raise is " + str(self.game.banker.min_raise)
        error_surface, position = self.game.raise_field.get_wrong_response(True, message)
        screen.blit(error_surface, position)

    #
    # Whole screens
    #
    def draw_poker_assets(self):
        screen.fill(POKERGREEN)  # background must be first
        self.draw_table()         # table second
        self.draw_cards()         # cards third, so they sit on the table

        # order doesn't matter from here
        self.draw_ai_names()
        self.draw_action_names()
        self.draw_action_value()
        self.draw_pot_money()
        self.draw_player_money()
        self.game.raise_field.draw_text_input()
        self.draw_dealer_button()
        self.draw_game_info()

    def draw_continue_prompt(self):
        continue_text = turn_indicator_font.render("click to continue", True, WHITE)
        text_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        screen.blit(continue_text, text_rect)

    def draw_game_over_screen(self, won):
        screen.fill(POKERGREEN)

        if won:
            message, sub_message = "CONGRATULATIONS! YOU WON!", "AI SCRUBZ SMASHED! GG EZ"
        else:
            message, sub_message = "GAME OVER", "YOU SUCK! AGI ALREADY?"

        main_text = font_consolas.render(message, True, WHITE)
        screen.blit(main_text, main_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))

        sub_text = font_verdana.render(sub_message, True, LIGHT_BLACK)
        screen.blit(sub_text, sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10)))

        exit_text = turn_indicator_font.render("click to exit", True, WHITE)
        screen.blit(exit_text, exit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)))
