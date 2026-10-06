# Poker

Texas Hold'em against five AI opponents, built with Python and pygame. Each AI estimates its chance of winning with a Monte Carlo simulation, then plays according to a randomised personality (aggression, confidence, bluffing).

## Run

```
uv sync
python main.py
```

Keep your `assets/` folder (table, card faces, card back, dealer button) next to `main.py`.

## Project layout

| File | Responsibility |
| --- | --- |
| `main.py` | Entry point: builds the screens and starts the game |
| `poker/settings.py` | Constants, colours and screen-layout maths |
| `poker/resources.py` | Pygame init, fonts, images (card images are cached) |
| `poker/cards.py` | `Card`, deck creation and the `Dealer` |
| `poker/hand_evaluator.py` | Pure hand-ranking functions, shared by the game and the AI |
| `poker/banker.py` | Pot, blinds, bets, debts and refunds |
| `poker/players.py` | `Player` and `AIPlayer` (Monte Carlo decision making) |
| `poker/ui.py` | `Button`, `TextField`, `ButtonManager` |
| `poker/renderer.py` | All drawing of the table (reads state, never changes it) |
| `poker/game_controller.py` | Game loop, turn order and betting rounds |
| `poker/screens.py` | `ScreenManager`, start screen and game screen |

`cards`, `hand_evaluator`, `banker` and `players` don't import pygame, so the game logic can be tested without opening a window.

## Known limitations / ideas

- Tied hands go to the first player rather than splitting the pot, and there are no kickers.
- Two pair is not detected when a player has three pairs.
- Straight flush detection can depend on card order when the cards contain a duplicate value.
