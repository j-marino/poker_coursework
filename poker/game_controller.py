# The GameController runs a game of poker: the main loop, betting rounds and turn order.
import sys

import pygame

from poker.banker import Banker
from poker.cards import Dealer
from poker.hand_evaluator import HAND_VALUES, evaluate_hand
from poker.players import AIPlayer, Player
from poker.renderer import TableRenderer
from poker.settings import (
    ACTION_BUTTON_HEIGHT,
    ACTION_BUTTON_WIDTH,
    ACTION_BUTTON_X,
    ACTION_BUTTON_Y,
    AI_NAMES,
    COMMUNITY_CARD_X,
    COMMUNITY_CARD_Y,
    FPS,
    HAND_CARD_X,
    HAND_CARD_Y,
    MONTE_CARLO_SIMULATIONS,
    STARTING_MONEY,
    WHITE,
    seat_position,
)
from .ui import Button, ButtonManager, TextField


def quit_game():
    pygame.quit()
    sys.exit()


class GameController:
    def __init__(self):
        self.players = []        # every player still in the game (human + AI)
        self.active_players = []  # players who haven't folded this hand
        self.community_cards = []
        self.dealer = Dealer()
        self.banker = Banker()
        self.renderer = TableRenderer(self)
        self.current_player_turn = 0  # index into active_players
        self.game_turn = 0           # 0 pre-flop, 1 flop, 2 turn, 3 river

        # There is only one human, created here because the buttons need its actions.
        human_player = Player()
        human_player.add_to_game(self.players)

        # NOTE: an "all-in" button may be added to this dictionary in future.
        self.buttons = ButtonManager({
            name: Button(ACTION_BUTTON_X[name], ACTION_BUTTON_Y, ACTION_BUTTON_WIDTH, ACTION_BUTTON_HEIGHT,
                         action, name, WHITE)
            for name, action in (
                ("check", human_player.check),
                ("fold", human_player.fold),
                ("raise", human_player.raise_pot),
                ("call", human_player.call),
            )
        })
        # The raise text field takes the raise button's place once it is clicked.
        self.raise_field = TextField(ACTION_BUTTON_X["raise"], ACTION_BUTTON_Y,
                                     ACTION_BUTTON_WIDTH, ACTION_BUTTON_HEIGHT, "e.g: 100")

        # Dealing functions for each stage after pre-flop. Pre-flop isn't here because
        # it happens at the start of the hand, which lets the game turn start at 0.
        self.game_turn_state = {1: self.flop, 2: self.turn, 3: self.river}

        # Flags for the game loop
        self.raise_happened = False       # keeps the betting round going after a raise
        self.round_cycle_finished = False  # everyone has acted at least once
        self.raiser = None               # the most recent raiser (a Player/AIPlayer)
        self.players_checked = []
        self.available_actions = ["call", "fold", "raise"]  # no check pre-flop
        self.showdown_running = False     # true once everyone is all in
        self.small_blind = None           # decided from the dealer button position
        self.big_blind = None
        self.rounds_passed = 0

    #
    # Main loop
    #
    def setup_game(self):
        for seat, name in AI_NAMES.items():
            AIPlayer(name, seat).add_to_game(self.players)

        self.active_players += self.players[:]  # a copy, for safety
        self.banker.give_all_starting_money(self.active_players, STARTING_MONEY)
        self.banker.reset_debt_list(self.active_players)
        self.dealer.shuffle()  # must shuffle at the start of every game

        self.dealer.initial_dealer_button(self.active_players)
        self.set_blinds()
        self.renderer.draw_poker_assets()  # draw first so the blinds are seen acting

        self.banker.take_blind_money(self.small_blind, self.small_blind, self.big_blind)
        self.banker.take_blind_money(self.big_blind, self.small_blind, self.big_blind)
        self.pre_flop()

    def game_loop(self):
        self.setup_game()
        clock = pygame.time.Clock()

        while True:
            # the turn index must behave like a circular list
            if self.current_player_turn >= len(self.active_players):
                self.current_player_turn = 0
            current_player = self.active_players[self.current_player_turn]

            current_player = self.handle_events(current_player)
            self.check_round_end()
            current_player = self.process_turn(current_player)

            # draw order matters: background, then table, then everything else
            self.renderer.draw_poker_assets()
            self.buttons.draw_all_buttons(current_player.is_human and not current_player.is_all_in)
            self.renderer.draw_turn_indicator(current_player)
            if self.raise_field.show_error:
                self.renderer.draw_raise_error()

            if self.showdown_running and current_player != self.last_player_in_turn_order():
                self.showdown()

            pygame.display.update()
            clock.tick(FPS)

    #
    # Input
    #
    def handle_events(self, current_player):
        # Process quit, raise-field and button events. Returns the (possibly new) current player.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

            raise_input = self.raise_field.handle_events(event)  # text is returned on enter
            if raise_input is not False:
                current_player = self.submit_raise(raise_input, current_player)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                current_player = self.handle_click(current_player)

        return current_player

    def submit_raise(self, raise_input, current_player):
        # Validate typed raise text; run the raise if it's within the limits.
        if not raise_input.isdigit():  # letters, symbols or nothing
            self.raise_field.set_draw_error(True)
            return current_player

        raise_amount = int(raise_input)
        if raise_amount < self.banker.min_raise and raise_amount < current_player.bank:
            self.raise_field.set_draw_error(True)  # a valid number, but below the minimum raise
            return current_player

        raise_amount = min(raise_amount, current_player.bank)  # typing more than the bank is an all in
        self.raise_field.reset_input()
        self.human_action("raise", current_player, raise_amount)
        current_player = self.active_players[self.current_player_turn]

        # draw the raise button again instead of the text field
        self.buttons.get_button_object("raise").active = True
        self.raise_field.set_draw_error(False)
        self.raise_field.active = False
        return current_player

    def handle_click(self, current_player):
        # A left click: either an action button was pressed or the player clicked away.
        raise_button = self.buttons.get_button_object("raise")

        if not self.buttons.button_was_clicked():
            raise_button.active = True  # clicked elsewhere: show the raise button again
            return current_player

        self.raise_field.set_draw_error(False)
        named_action = self.buttons.get_action_name()

        if named_action == "raise" and raise_button.active:
            raise_button.active = False       # swap the button for the input field
            self.raise_field.active = True
        else:
            self.human_action(named_action, current_player, self.banker.min_raise)
            current_player = self.active_players[self.current_player_turn]

        return current_player

    #
    # Turn processing
    #
    def check_round_end(self):
        if self.raise_happened:
            # a raise keeps the round going until play returns to the raiser
            if self.raise_cycle_finished():
                self.process_round_end()

        elif self.round_cycle_finished:
            # must not end the round if only some people checked
            if not self.players_checked or len(self.players_checked) == len(self.active_players):
                self.process_round_end()

    def process_turn(self, current_player):
        # Let the AI act (or skip all-in players). Returns the current player afterwards.
        if not current_player.is_human:
            if self.current_player_is_all_in(current_player):
                self.skip_all_in_player_turn()  # nothing to do when all in
            elif self.computer_action():
                self.process_action(current_player.action_name, current_player, current_player.raise_amount)

                try:  # the turn index can run off the end of the list after an action
                    current_player = self.active_players[self.current_player_turn]
                except IndexError:
                    pass  # keep the current player

                if self.round_ended():
                    self.renderer.draw_poker_assets()
                    pygame.display.update()
                    pygame.time.wait(1000)  # time to digest what happened
                    self.reset_round()

        if current_player.is_human and self.current_player_is_all_in(current_player):
            self.skip_all_in_player_turn()

        return current_player

    def computer_action(self):
        # Run the current AI's turn. Returns True once an action was chosen and executed.
        # not valid when the turn index has run past the end of the list
        if self.current_player_turn >= len(self.active_players):
            return False

        current_player = self.active_players[self.current_player_turn]
        if current_player.is_human:  # waiting for the human to press a button
            return False

        can_check = "check" in self.available_actions
        current_player.monte_carlo_simulation(MONTE_CARLO_SIMULATIONS, self.community_cards, can_check,
                                           self.banker.call_value, self.banker.min_raise)
        current_player.do_action()
        self.current_player_turn += 1
        return True

    def human_action(self, named_action, current_player, raise_amount):
        if self.valid_action(named_action) and current_player.is_human:
            if self.process_action(named_action, current_player, raise_amount):
                return  # the hand ended and a new one has been set up: don't skip its first player
            self.current_player_turn += 1  # the action is guaranteed valid so move on

            # The round finishes when the last player in the cycle has acted, but that
            # doesn't always start the next round: a raise may have happened.
            if self.round_ended():
                self.reset_round()

    def valid_action(self, action_name):
        # only used for the human; the AI always makes a valid action
        # "check" is only available when nobody has put money in yet this round
        return action_name in self.available_actions

    def process_action(self, action, player, raise_amount):
        # Carry out an action. Returns True if it ended the hand (everyone else folded).
        # once anyone does something other than check, checking is no longer allowed this round
        if action != "check" and "check" in self.available_actions:
            self.available_actions.remove("check")

        if action == "raise":
            self.raise_happened = True
            self.raiser = player
            self.remove_from_check_list(player)
            self.all_in_handling(player, raise_amount)  # before the money is taken, or it's calculated wrong
            self.banker.handle_raise(player, raise_amount)

        elif action == "fold":
            self.remove_from_check_list(player)
            player.fold()
            self.active_players.remove(player)
            if len(self.active_players) == 1:  # everyone else folded: premature win
                self.renderer.draw_poker_assets()
                pygame.display.update()
                pygame.time.wait(1000)
                self.post_river()
                return True

            # The turn index is incremented after every valid action, but removing a
            # player already shifts the next one into this slot, so step back one.
            self.current_player_turn -= 1

            if self.raiser == player:  # the raiser folded: the next player becomes the raiser
                try:
                    self.raiser = self.active_players[self.current_player_turn + 1]
                except IndexError:  # raiser was at the end of the list
                    self.raiser = self.active_players[0]

            self.banker.remove_from_debts(player)
            if self.should_trigger_showdown():  # everyone left is all in
                self.showdown_running = True

        elif action == "call":
            self.remove_from_check_list(player)
            self.all_in_handling(player, self.banker.call_value)
            self.banker.handle_call(player)

        elif action == "check":
            self.players_checked.append(player)
            if len(self.players_checked) == self.get_num_non_all_in_players() and self.has_all_in_players():
                self.round_cycle_finished = True

        return False

    #
    # Betting round state
    #
    def reset_round(self):
        self.round_cycle_finished = True  # can move on if no raise happened
        self.reset_ai_action_names()        # stop drawing the AI actions: they're about to change

    def reset_ai_action_names(self):
        # AI actions must not persist into the next round.
        for player in self.active_players:
            if not player.is_human:
                player.action_name = ""

    def round_ended(self):
        return self.finished_betting()

    def finished_betting(self):
        # True once every player who can still bet has matched the largest bet (or checked).
        current_round_bets = self.banker.current_round_bets

        if len(self.players_checked) == len(self.active_players):
            return True
        if not current_round_bets:
            return False

        largest_bet = max(current_round_bets.values())
        for player in self.active_players:
            if player.is_all_in:
                continue  # can't bet any more
            if current_round_bets.get(player, 0) < largest_bet:
                return False  # still owes money, even if they checked earlier

        return True

    def raise_cycle_finished(self):
        # after a raise, the round ends when play comes back round to the raiser
        return self.get_next_player_turn() == self.raiser

    def get_next_player_turn(self):
        # the active list is circular: past the end means back to the start
        if self.current_player_turn >= len(self.active_players):
            return self.active_players[0]
        return self.active_players[self.current_player_turn]

    def last_player_in_turn_order(self):
        return self.active_players[-1]

    def remove_from_check_list(self, player):
        # If a player checked earlier and then acts again, they are no longer 'checked'.
        if player in self.players_checked:
            self.players_checked.remove(player)

    def process_round_end(self):
        if self.check_post_river():
            self.post_river()  # and decide the winner
        else:
            self.start_next_round()
            self.round_cycle_finished = False
            self.raise_happened = False
            self.banker.reset_debt_list(self.active_players)
            self.banker.reset_current_round_bets()  # nobody has bet in the new round yet

    def start_next_round(self):
        self.game_turn += 1
        self.rounds_passed += 1
        self.game_turn_state[self.game_turn]()  # deal the flop / turn / river

        # everyone may check again in a new round
        self.available_actions = ["call", "check", "fold", "raise"]
        self.players_checked.clear()
        self.raise_happened = False
        self.raiser = None

    def check_post_river(self):
        return self.game_turn == 3  # the river has been dealt: end of the hand

    #
    # All-in handling and showdown
    #
    def player_is_going_all_in(self, player, bet):
        return self.banker.bet_greater_than_bank(bet, player.bank)

    def set_player_all_in(self, player):
        player.is_all_in = True

    def all_in_handling(self, player, bet):
        if self.player_is_going_all_in(player, bet):
            self.set_player_all_in(player)
            if self.should_trigger_showdown():
                self.showdown_running = True

    def skip_all_in_player_turn(self):
        self.current_player_turn += 1  # all-in players don't get a turn

    def current_player_is_all_in(self, current_player):
        return current_player.is_all_in

    def has_all_in_players(self):
        return any(player.is_all_in for player in self.active_players)

    def get_num_non_all_in_players(self):
        return sum(1 for player in self.active_players if not player.is_all_in)

    def all_players_all_in(self):
        # If only one player isn't all in it's the same thing: they have nobody left to bet against.
        return self.get_num_non_all_in_players() <= 1

    def should_trigger_showdown(self):
        if self.all_players_all_in():
            return True

        # Also when one player isn't all in but has more money. Checked players must be
        # accounted for or this triggers too early.
        if self.get_num_non_all_in_players() <= 1 and self.finished_betting() and not self.players_checked:
            return True

        return False

    def showdown(self):
        # Everyone is all in: turn the cards over and deal the remaining community cards.
        self.renderer.reveal_ai_cards()

        while not self.check_post_river():
            self.process_round_end()
            self.renderer.draw_cards()
            self.renderer.reveal_ai_cards()
            pygame.display.update()
            pygame.time.wait(1000)  # time to digest each new card

        self.process_round_end()
        self.showdown_running = False  # only run the showdown once

    #
    # Blinds and dealing
    #
    def get_next_index(self, current, list_length):
        return 0 if current >= list_length - 1 else current + 1

    def set_blinds(self):
        if len(self.active_players) == 2:
            # Heads up: the dealer is the small blind. They act first pre-flop and last after.
            dealer_index = self.dealer.dealer_button_index
            small_blind_index = dealer_index
            big_blind_index = self.get_next_index(dealer_index, len(self.players))
            small_blind_index, big_blind_index = self.validate_blind_indexes(small_blind_index, big_blind_index)

            self.small_blind = self.players[small_blind_index]
            self.big_blind = self.players[big_blind_index]
            self.current_player_turn = small_blind_index

        elif self.dealer.dealer_button in self.players:
            dealer_button_index = self.players.index(self.dealer.dealer_button)
            small_blind_index = dealer_button_index + 1  # one clockwise of the dealer button
            big_blind_index = dealer_button_index + 2    # two clockwise of the dealer button
            small_blind_index, big_blind_index = self.validate_blind_indexes(small_blind_index, big_blind_index)

            self.small_blind = self.players[small_blind_index]
            self.big_blind = self.players[big_blind_index]

            # first to act is the player after the big blind
            self.current_player_turn = big_blind_index + 1
            if self.current_player_turn == len(self.active_players):
                self.current_player_turn = 0

    def validate_blind_indexes(self, small_blind_index, big_blind_index):
        # Wrap blind indexes round the end of the (circular) player list.
        if small_blind_index == len(self.players):
            small_blind_index = 0
            big_blind_index = 1
        elif small_blind_index == len(self.players) - 1:
            big_blind_index = 0
        return small_blind_index, big_blind_index

    def rotate_dealer_button(self):
        # Pass the dealer button one place clockwise to keep the game fair.
        if self.dealer.dealer_button in self.players:
            current_index = self.players.index(self.dealer.dealer_button)
        else:  # the dealer was knocked out: carry on from where the button was
            current_index = self.dealer.dealer_button_index

        next_index = self.get_next_index(current_index, len(self.players))
        self.dealer.dealer_button = self.players[next_index]
        self.dealer.dealer_button_index = next_index

    def assign_card_positions(self, cards, x_coords, y_coord):
        for index, card in enumerate(cards):
            card.set_pos(x_coords[index], y_coord)

    def pre_flop(self):
        # Deal everyone two cards and give them screen positions.
        self.dealer.deal_player_hands(self.players)

        for player in self.active_players:
            if player.is_human:
                self.assign_card_positions(player.hand, HAND_CARD_X, HAND_CARD_Y)
            else:
                position = seat_position(player.seat)
                if position:
                    x_coords, y_coord = position
                    self.assign_card_positions(player.hand, x_coords, y_coord)

    def flop(self):
        self.dealer.deal_flop(self.community_cards)
        self.assign_card_positions(self.community_cards, COMMUNITY_CARD_X, COMMUNITY_CARD_Y)

    def turn(self):
        self.dealer.deal_turn(self.community_cards)
        self.place_newest_community_card()

    def river(self):
        self.dealer.deal_river(self.community_cards)
        self.place_newest_community_card()

    def place_newest_community_card(self):
        card_index = len(self.community_cards) - 1
        self.community_cards[-1].set_pos(COMMUNITY_CARD_X[card_index], COMMUNITY_CARD_Y)

    #
    # End of a hand
    #
    def evaluate_player_hands(self):
        # only active players: there's no need to evaluate a folded hand
        for player in self.active_players:
            player.evaluated_hand = evaluate_hand(self.community_cards + player.hand)

    def decide_winner(self):
        winner = self.active_players[0]
        for player in self.active_players:
            if HAND_VALUES[player.evaluated_hand] > HAND_VALUES[winner.evaluated_hand]:
                winner = player

        # TODO: when several players have the same hand, split the pot between them
        # (and compare kickers) instead of giving it to whoever sits first.
        return winner

    def post_river(self):
        self.evaluate_player_hands()
        winner = self.decide_winner()

        self.banker.distribute_money(self.active_players, winner)  # return surplus bets if needed
        self.banker.give_pot_to_winner(winner)

        self.renderer.reveal_ai_cards()
        self.renderer.draw_winner_text(winner)
        pygame.display.update()

        broke_players = self.banker.get_no_money_players(self.players)

        self.wait_for_click()
        if broke_players:
            self.remove_from_game(broke_players)
            if self.check_game_over(broke_players):
                return

        # start the next hand
        self.reset()
        self.rotate_dealer_button()
        self.banker.increase_blind_bet(self.rounds_passed)
        self.set_blinds()
        self.banker.take_blind_money(self.small_blind, self.small_blind, self.big_blind)
        self.all_in_handling(self.small_blind, self.banker.small_blind_bet)
        self.banker.take_blind_money(self.big_blind, self.small_blind, self.big_blind)
        self.all_in_handling(self.big_blind, self.banker.big_blind_bet)
        self.pre_flop()
        pygame.display.update()

    def wait_for_click(self):
        # After a hand the player clicks to carry on.
        self.renderer.draw_continue_prompt()
        pygame.display.update()
        self.wait_for_mouse_click()

    @staticmethod
    def wait_for_mouse_click(exit_on_input=False):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # still allow quitting while waiting
                    quit_game()
                if event.type == pygame.MOUSEBUTTONDOWN or (exit_on_input and event.type == pygame.KEYDOWN):
                    return

    def remove_from_game(self, players_to_be_removed):
        # Knock broke players out. If it's the human, check_game_over shows the loss screen.
        for player in players_to_be_removed:
            if player in self.players:
                self.players.remove(player)
                self.banker.player_to_total_money_in.pop(player, None)  # no money left in the game
                self.banker.raise_debts.pop(player, None)            # broke players can't pay debts

    def check_game_over(self, broke_players):
        if any(player.is_human for player in broke_players):
            self.display_game_over_screen(won=False)
            return True

        # Past the human check, so if only one player has money left it's the human: a win.
        if len([player for player in self.players if player.bank > 0]) == 1:
            self.display_game_over_screen(won=True)
            return True

        return False

    def display_game_over_screen(self, won):
        self.renderer.draw_game_over_screen(won)
        pygame.display.update()
        self.wait_for_mouse_click(exit_on_input=True)
        quit_game()

    def reset(self):
        # Reset every flag, debt and card ready for a new hand.
        self.dealer.recreate_deck()
        self.dealer.shuffle()  # otherwise every hand would be dealt from an unshuffled deck
        self.community_cards = []
        self.current_player_turn = 0  # set_blinds decides who really goes first
        self.game_turn = 0
        self.raiser = None
        self.raise_happened = False
        self.round_cycle_finished = False
        self.showdown_running = False
        self.active_players = self.players[:]
        self.players_checked = []
        self.available_actions = ["call", "fold", "raise"]  # no check at the start of a hand

        banker = self.banker
        banker.call_value = banker.big_blind_bet  # call value follows the big blind
        banker.previous_bet = banker.small_blind_bet
        banker.current_bet = banker.big_blind_bet
        banker.min_raise = (banker.current_bet - banker.previous_bet) + banker.current_bet
        banker.reset_current_round_bets()
        banker.reset_total_money_in()  # otherwise all-in refunds are calculated from every previous hand too
        banker.reset_debt_list(self.active_players)

        for player in self.players:
            player.is_all_in = False  # a blind can put someone all in again straight away
            player.hand = []
            player.evaluated_hand = ""
            player.is_folded = False

            if not player.is_human:
                player.action = player.check
                player.action_name = ""
