#!/usr/bin/python3

import curses
from enum import Enum
from time import sleep
from random import choice, shuffle, random
from collections import namedtuple

room_x = 32
room_y = 12
R_COL_W = 50


class Player():
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.name = "Wanderer"
        self.money = 20
        self.marker = '@'


class Monster():
    def __init__(self, x, y, marker, max_hp, is_boss):
        self.x = x
        self.y = y
        self.marker = marker
        self.max_hp = max_hp
        self.hp = self.max_hp
        self.is_boss = is_boss
        self.cooldown = 0
        self.max_cooldown = 5
        self.spare_count = 1 if self.is_boss else 0

    def wander(self, room):
        if self.cooldown:
            self.cooldown -= 1

        if not self.is_boss:
            near_player = False
            wasd = [(-1, 0), (1, 0), (0, -1), (0, 1)]

            # if they are next to player, don't move!
            for m in wasd:
                try:
                    if isinstance(room[self.y+m[1]][self.x+m[0]], Player):
                        near_player = True
                except Exception:
                    pass

            # if they are diaganol from player, move near them
            # TODO

            # otherwise wander around
            if not near_player:
                shuffle(wasd)
                for m in wasd:
                    try:
                        if isinstance(room[self.y+m[1]][self.x+m[0]], OpenSpace):
                            tmp = room[self.y+m[1]][self.x+m[0]]
                            room[self.y+m[1]][self.x+m[0]] = room[self.y][self.x]
                            room[self.y][self.x] = tmp
                            self.x += m[0]
                            self.y += m[1]
                            break
                    except Exception:
                        pass


class SlotMachine(Monster):
    def __init__(self):
        self.marker = 's'
        self.spaces = ['#', '$', '%', '&']

    def encounter(self, player):
        clearwin(textwin)
        textwin.addstr(1, 1, 'slot machine instructions')
        textwin.addstr(2, 3, '(l) leave slot machine')
        textwin.addstr(3, 3, '(p) pull lever (cost $3)')
        textwin.refresh()

        gamewin.addstr(1, 5, "╔═════════════╗ _")
        gamewin.addstr(2, 5, "║ SUPER SLOTS ║(_)")
        gamewin.addstr(3, 5, "╠═════════════╣ ┃")
        gamewin.addstr(4, 5, "║ ┌─┐ ┌─┐ ┌─┐ ║ ┃")
        gamewin.addstr(5, 5, "║ │$│ │$│ │$│ ║ ┃")
        gamewin.addstr(6, 5, "║ └─┘ └─┘ └─┘ ║━┛")
        gamewin.addstr(7, 5, "║             ║")
        gamewin.addstr(8, 5, "╚═════════════╝")
        gamewin.refresh()

        playing = True
        while playing:
            key = gamewin.getkey()

            if key == 'l':
                playing = False
                clearwin(gamewin)
                clearwin(textwin)
                break

            elif key == 'p':
                textwin.addstr(5, 3, "                               ")
                textwin.refresh()
                player.money -= 3
                update_status()
                for _ in range(10):
                    x, y, z = choice(self.spaces), choice(self.spaces), choice(self.spaces)
                    gamewin.addch(5, 8, x)
                    gamewin.addch(5, 12, y)
                    gamewin.addch(5, 16, z)
                    gamewin.refresh()
                    sleep(0.12)
                unique = len(set([x, y, z]))
                if unique == 3:
                    textwin.addstr(5, 3, "no matches                   ")
                elif unique == 2:
                    textwin.addstr(5, 3, "two of a kind, you won $5!   ")
                    player.money += 5
                elif unique == 1:
                    textwin.addstr(5, 3, "three of a kind, you won $8!")
                    player.money += 8
                textwin.refresh()
                update_status()


class BlackJack(Monster):
    def __init__(self, x, y, marker, max_hp, is_boss, bet, hold_at=18):
        super().__init__(x, y, marker, max_hp, is_boss)
        self.bet = bet
        self.hold_at = hold_at
        self.hold_at_adj = 21 - self.hold_at

    def get_value(self, val):
        try:
            return (int(val), int(val))
        except Exception:
            if val in ('K', 'Q', 'J'):
                return (10, 10)
            else:
                return (1, 11)

    def _score_hand(self, summ):
        return 21 - summ if summ <= 21 else 22

    def score_hand(self, hand):
        vals = [self.get_value(card.value) for card in hand]
        sum1, sum2 = sum([v[0] for v in vals]), sum([v[1] for v in vals])
        score1, score2 = (sum1, self._score_hand(sum1)), (sum2, self._score_hand(sum2))
        return min(score1, score2, key=lambda x: x[1])

    def encounter(self, player):
        clearwin(textwin)
        textwin.addstr(1, 2, f'blackjack monster, Lvl 1, HP: {self.hp}/{self.max_hp}    ', curses.A_BOLD)
        textwin.addstr(3, 2, "You've been spotted by a blackjack monster...")
        textwin.refresh()

        clearwin(keyswin)
        keyswin.addstr(1, 2, 'options:', curses.A_BOLD)
        keyswin.addstr(2, 3, '(r) run away')
        keyswin.addstr(3, 3, f'(d) deal cards (costs ${self.bet})')
        keyswin.refresh()

        playing = True
        while playing:
            key = gamewin.getkey()

            if key == 'r':
                clearwin(textwin)
                if random() < 0.5:
                    textwin.addstr(1, 2, f"{f'you escaped unharmed!':<{R_COL_W-4}}")
                else:
                    textwin.addstr(1, 2, f"{f'the monster took ${self.bet} as you escaped!':<{R_COL_W-4}}")
                    p.money -= self.bet
                    update_status()
                textwin.refresh()
                playing = False
                self.cooldown = self.max_cooldown
                clearwin(gamewin)
                break

            elif key == 'd':
                clearwin(gamewin)
                clearwin(keyswin)
                keyswin.addstr(1, 2, 'options:', curses.A_BOLD)
                keyswin.addstr(2, 3, '(s) stand')
                keyswin.addstr(3, 3, '(h) hit')
                keyswin.refresh()

                textwin.addstr(1, 2, f'blackjack monster, Lvl 1, HP: {self.hp}/{self.max_hp}    ', curses.A_BOLD)
                textwin.addstr(3, 2, f"{'dealing cards...':{R_COL_W-3}}")
                textwin.addstr(4, 1, f"{'':{R_COL_W-3}}")
                textwin.refresh()

                player.money -= self.bet
                update_status()

                deck = make_deck()
                p_hand = [deck.pop(), deck.pop()]
                d_hand = [deck.pop(), deck.pop()]

                gamewin.addstr(1,  2, f"your cards ({self.score_hand(p_hand)[0]})")
                gamewin.addstr(2,  3,  "╭────╮╭────╮")
                gamewin.addstr(3,  3, f"│ {p_hand[0].value:<2} ││ {p_hand[1].value:<2} │")
                gamewin.addstr(4,  3, f"│  {p_hand[0].suit} ││  {p_hand[1].suit} │")
                gamewin.addstr(5,  3,  "╰────╯╰────╯")
                gamewin.addstr(7,  2, "dealer's cards")
                gamewin.addstr(8,  3,  "╭────╮╭────╮")
                gamewin.addstr(9,  3, f"│ {d_hand[0].value:<2} ││    │")
                gamewin.addstr(10, 3, f"│  {d_hand[0].suit} ││    │")
                gamewin.addstr(11, 3,  "╰────╯╰────╯")

                while True:
                    key = gamewin.getkey()

                    if key == 's':
                        p_score = self.score_hand(p_hand)

                        # reveal 2nd card
                        sleep(0.25)
                        gamewin.addstr(9,  9, f"│ {d_hand[len(d_hand)-1].value:<2} │")
                        gamewin.addstr(10, 9, f"│  {d_hand[len(d_hand)-1].suit} │")
                        gamewin.refresh()

                        # score dealer hand
                        d_score = self.score_hand(d_hand)
                        gamewin.addstr(7,  2, f"dealer's cards ({d_score[0]})")

                        # dealer draws cards until >= hold_at or busts
                        while d_score[1] != 22 and d_score[1] > self.hold_at_adj:
                            sleep(0.25)

                            d_hand.append(deck.pop())

                            start = (6 * len(d_hand)) - 3
                            gamewin.addstr(8,  start,  "╭────╮")
                            gamewin.addstr(9,  start, f"│ {d_hand[len(d_hand)-1].value:<2} │")
                            gamewin.addstr(10, start, f"│  {d_hand[len(d_hand)-1].suit} │")
                            gamewin.addstr(11, start,  "╰────╯")

                            d_score = self.score_hand(d_hand)
                            gamewin.addstr(7, 2, f"dealer's cards ({d_score[0]})")
                            gamewin.refresh()

                        if d_score[1] == 22:
                            textwin.addstr(3, 2, f"{f'dealer busts':{R_COL_W-4}}")
                            textwin.addstr(4, 3, f"{f'you won ${self.bet}, monster lost 1 HP':{R_COL_W-5}}")
                            p.money += (self.bet * 2)
                            self.hp -= 1
                        elif p_score[1] < d_score[1]:
                            textwin.addstr(3, 2, f"{f'you beat the dealer':{R_COL_W-4}}")
                            textwin.addstr(4, 3, f"{f'you won ${self.bet}, monster lost 1 HP':{R_COL_W-5}}")
                            p.money += (self.bet * 2)
                            self.hp -= 1
                        elif p_score[1] == d_score[1]:
                            textwin.addstr(3, 2, f"{f'push, no winner':{R_COL_W-4}}")
                            p.money += self.bet
                        else:
                            textwin.addstr(3, 2, f"{f'dealer won':{R_COL_W-4}}")
                            textwin.addstr(4, 3, f"{f'you lost ${self.bet}':{R_COL_W-5}}")

                        update_status()

                        if self.hp <= 0:
                            if self.spare_count:
                                clearwin(textwin)
                                clearwin(keyswin)
                                textwin.addstr(1, 2, f"{f'you defeated the blackjack monster!':{R_COL_W-4}}", curses.A_BOLD)
                                textwin.addstr(2, 3, f"{f'press any key to continue...':{R_COL_W-4}}")
                                key = textwin.getkey()
                                clearwin(gamewin)
                                clearwin(textwin)
                                textwin.refresh()
                                return (True, self.is_boss)

                            else:
                                textwin.addstr(1, 2, f"{f'you defeated the blackjack monster!':{R_COL_W-4}}", curses.A_BOLD)
                                keyswin.addstr(1, 2, 'options:', curses.A_BOLD)
                                keyswin.addstr(2, 3, '(k) kill monster                 ')
                                keyswin.addstr(3, 3, '(s) spare monster                ')
                                keyswin.refresh()

                                while True:
                                    key = textwin.getkey()

                                    if key == 'k':
                                        clearwin(gamewin)
                                        clearwin(textwin)
                                        textwin.addstr(1, 2, f"{f'you killed the monster':{R_COL_W-4}}")
                                        textwin.refresh()
                                        return (True, self.is_boss)

                                    elif key == 's':
                                        clearwin(gamewin)
                                        clearwin(textwin)
                                        textwin.addstr(1, 2, f"{f'you spared the monster':{R_COL_W-4}}")
                                        textwin.refresh()
                                        self.cooldown = self.max_cooldown
                                        self.hp = self.max_hp
                                        self.spare_count += 1
                                        return (None, None)

                        else:
                            textwin.addstr(1, 2, f'blackjack monster, Lvl 1, HP: {self.hp}/{self.max_hp}    ', curses.A_BOLD)

                        break

                    elif key == 'h':
                        p_hand.append(deck.pop())
                        p_score = self.score_hand(p_hand)
                        gamewin.addstr(1,  2, f"your cards ({p_score[0]})")

                        start = (6 * len(p_hand)) - 3
                        gamewin.addstr(2, start, "╭────╮")
                        gamewin.addstr(3, start, f"│ {p_hand[len(p_hand)-1].value:<2} │")
                        gamewin.addstr(4, start, f"│  {p_hand[len(p_hand)-1].suit} │")
                        gamewin.addstr(5, start, "╰────╯")
                        gamewin.refresh()

                        if p_score[1] == 22:
                            textwin.addstr(3, 2, f"{f'bust!':{R_COL_W-4}}")
                            textwin.addstr(4, 3, f"{f'you lost ${self.bet}':{R_COL_W-5}}")
                            break

                textwin.refresh()
                update_status()

                if playing:
                    keyswin.addstr(2, 3, f"{'(r) run away':<{R_COL_W-5}}")
                    keyswin.addstr(3, 3, f'(d) deal cards (costs ${self.bet})')
                    keyswin.refresh()

        return (None, None)


class OpenSpace():
    def __init__(self):
        self.marker = ' '


class OtherObject():
    def __init__(self, marker):
        self.marker = marker


class Door():
    def __init__(self, x, y, marker):
        self.x = x
        self.y = y
        self.marker = marker


Card = namedtuple('Card', ['value', 'suit'])
suits = ['♥', '♦', '♠', '♣']
values = [
    'A', '2', '3', '4', '5', '6', '7',
    '8', '9', '10', 'J', 'Q', 'K'
]


def make_deck() -> list:
    deck = [Card(v, s) for v in values for s in suits]
    shuffle(deck)
    return deck


class Room():
    def __init__(self, name, str_map, object_map):
        self.name = name
        self.str_map = str_map
        self.object_map = object_map

    def build_room(self):
        room, enemies = [], []
        rows = [r for r in self.str_map.split('\n') if r]
        for i in range(room_y):
            spaces = []
            for j_idx, j in enumerate(rows[i]):
                if j in self.object_map:
                    if self.object_map[j][0] == BlackJack:
                        args = object_map[j][1]
                        args["x"] = j_idx
                        args["y"] = i
                        obj = BlackJack(**args)
                        enemies.append(obj)
                        spaces.append(obj)
                    elif self.object_map[j][0] == Door:
                        args = object_map[j][1]
                        args["x"] = j_idx
                        args["y"] = i
                        obj = Door(**args)
                        spaces.append(obj)
                    else:
                        spaces.append(object_map[j][0](**object_map[j][1]))
                else:
                    spaces.append(OtherObject(j))
            room.append(spaces)
        return room, enemies


_room2 = """
┏━━━━━━━━━━━━━━━━━━━━━━━━┄┄┄━━━┓
┃                         B    ┃
┃                              ┃
┃    │            ────┐        ┃
┃    │     │          └────────┨
┃    │     │                   ┃
┃ b  │     ├─────┘       │     ┃
┃    │     │   b         │     ┃
┠────┘     └─────────────┤  b  ┃
┃                        │     ┃
┃                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""

_room3 = """
┏━━━━━━━━━━┄┄┄━━━━━━━━━━━━━━━━━┓
┃           B                  ┃
┃                              ┃
┃    │            ────┐        ┃
┃    │     │          └────────┨
┃    │     │                   ┃
┃ b  │     ├─────┘       │     ┃
┃    │     │   b         │     ┃
┠────┘     └─────────────┤     ┃
┃                              ┃
┃                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""


object_map = {
    "┄": (Door, {"marker": "┄"}),
    "b": (BlackJack, {"marker": "b", "bet": 3, "max_hp": 1, "is_boss": False, "hold_at": 20}),
    "B": (BlackJack, {"marker": "B", "bet": 5, "max_hp": 1, "is_boss": True}),
    " ": (OpenSpace, {}),
}

rooms = [
    Room("Room 1", _room2, object_map),
    Room("Room 2", _room3, object_map)
]

current_room = 0
room, enemies = rooms[current_room].build_room()

p = Player(2, room_y-2)
room[p.y][p.x] = p


def clearwin(win) -> None:
    y, x = win.getmaxyx()
    s = ' ' * (x - 2)   
    for i in range(1, y-1):
        win.addstr(i, 1, s)
    win.refresh()


def draw_room() -> None:
    for i in range(room_y):
        for j in range(room_x):
            mapwin.addch(i, j+1, room[i][j].marker)


def update(player: Player):
    for e in enemies:
        e.wander(room)

    draw_room()
    mapwin.refresh()

    wasd = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    encounter = None
    for m in wasd:
        try:
            if isinstance(room[player.y+m[1]][player.x+m[0]], BlackJack):
                enemy = room[player.y+m[1]][player.x+m[0]]
                if not enemy.cooldown:
                    if not enemy.is_boss or (enemy.is_boss and len(enemies) == 1):
                        encounter = enemy
                        break
        except Exception:
            pass

    return encounter


def update_status() -> None:
    clearwin(statuswin)
    statuswin.addstr(1, 2, f"Player: {p.name}")
    statuswin.addstr(2, 2, f" Money: {p.money}")
    statuswin.refresh()


stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
curses.curs_set(0)
stdscr.keypad(True)

statuswin = curses.newwin(4, 35, 1, 1)
statuswin.border(0)

update_status()

mapwin = curses.newwin(14, 35, 5, 1)
mapwin.border(' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ')
draw_room()

gamewin = curses.newwin(13, 50, 1, 36)
gamewin.border(0)
gamewin.refresh()

textwin = curses.newwin(7, 50, 14, 36)
textwin.border()
textwin.refresh()

keyswin = curses.newwin(7, 50, 21, 36)
keyswin.border()
keyswin.refresh()


class Position(Enum):
    OPEN = 1
    BLOCKED = 2
    NEXT_ROOM = 3


def check_pos(posY, posX) -> Position:
    if posY < 0 or posX >= room_x or posY >= room_y or posX < 0:
        return Position.NEXT_ROOM

    try:
        if isinstance(room[posY][posX], OpenSpace):
            return Position.OPEN
        else:
            return Position.BLOCKED
    except Exception:
        return Position.BLOCKED


keyswin.addstr(1, 2, "controls:", curses.A_BOLD)
keyswin.addstr(2, 3, "(wasd) move around")
keyswin.addstr(3, 3, "(e) interact / use")
keyswin.addstr(4, 3, "(q) quit")
keyswin.refresh()

# main game loop!
while True:
    key = mapwin.getkey()

    if key == 'q':
        break

    if key == 'e':
        pass

    elif key in 'wasd':
        posX, posY = p.x, p.y
        if key == 'w':
            newY, newX = posY-1, posX
        elif key == 's':
            newY, newX = posY+1, posX
        elif key == 'a':
            newY, newX = posY, posX-1
        elif key == 'd':
            newY, newX = posY, posX+1

        pos = check_pos(newY, newX)
        if pos == Position.OPEN:
            room[posY][posX] = OpenSpace()
            p.x, p.y = newX, newY
            room[p.y][p.x] = p
        elif pos == Position.NEXT_ROOM:
            current_room += 1
            room, enemies = rooms[current_room].build_room()
            p.x, p.y = p.x, room_y-2  # TODO more dynamic?
            room[p.y][p.x] = p

    draw_room()

    if obj := update(p):
        died, boss = obj.encounter(p)
        if died:
            room[obj.y][obj.x] = OpenSpace()
            enemies = [e for e in enemies if e != obj]
            del obj
            if boss:
                doors = [x for y in room for x in y if isinstance(x, Door)]
                for d in doors[:]:
                    room[d.y][d.x] = OpenSpace()
                    del d
            draw_room()

    clearwin(keyswin)
    keyswin.addstr(1, 2, "controls:", curses.A_BOLD)
    keyswin.addstr(2, 3, "(wasd) move around")
    keyswin.addstr(3, 3, "(e) interact / use")
    keyswin.addstr(4, 3, "(q) quit")
    keyswin.refresh()


curses.curs_set(1)
curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
