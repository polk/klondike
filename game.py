
import time

from directkeys import clic, drag
from screen import detect_cards, detect_deck
from misc import *


class Card:

    def __init__(self, value, color, location):
        self.value = value
        self.color = color
        self.location = location
        self.rank = self.get_rank()
        self.tint = self.get_tint()

    def __repr__(self):
        return str_card(self.value, self.color)

    def get_rank(self):
        if self.value == "A":
            return 1
        elif self.value == "J":
            return 11
        elif self.value == "Q":
            return 12
        elif self.value == "K":
            return 13
        else:
            return int(self.value)

    def get_tint(self):
        if self.color <= 1:
            return 0  # red
        return 1  # black

    def can_stack_on(self, other):
        return self.rank == other.rank - 1 and self.tint != other.tint


class Game:
    def __init__(self, verbose=True):
        self.verbose = verbose
        self.deck = []
        self.deck_index = -1
        self.draw_count = 0
        self.deck_size = 24
        self.stacks = [[], [], [], [], [], [], []]
        self.hidden = [0, 1, 2, 3, 4, 5, 6]
        self.foundations = [0, 0, 0, 0]
        for stack, letter, color, x, y in detect_cards():
            self.stacks[stack].append(Card(letter, color, (x, y)))

    def __str__(self):
        string = ""
        if self.deck_size > 0:
            string += "Deck ({}): {}\n".format(self.deck_size, self.deck[self.deck_index])
        else:
            string += "Empty deck\n"
        for color in range(4):
            string += "Foundation {}: {}\n".format(["D", "H", "S", "C"][color], self.foundations[color])
        for stack in range(7):
            string += "Stack {} ({} hidden): ".format(stack, self.hidden[stack])
            for card in self.stacks[stack]:
                string += "{} ".format(card)
            string += "\n"
        return string

    def log(self, message):
        if self.verbose:
            print(message)

    def draw(self, delay=.3):
        if self.deck_size == 0:
            return False
        if self.deck_index == self.deck_size - 1:  # all cards are drown
            self.log("Deck is empty, clicking to re-stack cards.")
            clic(1040, 160, 1)
            time.sleep(delay)
        clic(1040, 160, 1)
        time.sleep(delay)
        if self.draw_count < 24:
            letter, color, x, y = detect_deck()
            self.deck.append(Card(letter, color, (x, y)))
        self.deck_index += 1 % self.deck_size
        self.draw_count += 1
        self.log("Drew a card: {}".format(self.deck[self.deck_index]))
        if self.draw_count == 24 and self.verbose:
            print("All cards in deck are known.")
        return True

    def found_card(self, card):
        if card.rank == self.foundations[card.color] + 1:
            self.log("Sending {} to foundations.".format(card))
            clic(card.location[0], card.location[1], 2)
            self.foundations[card.color] += 1
            return True
        return False

    def found_stack(self, stack, delay=.5):
        if len(self.stacks[stack]) > 0:
            card = self.stacks[stack][-1]
            if self.found_card(card):
                self.stacks[stack].pop()
                time.sleep(delay)
                return True
        return False

    def found_deck(self):
        if self.deck_index >= 0:
            card = self.deck[self.deck_index]
            if self.found_card(card):
                self.deck.pop(self.deck_index)
                self.deck_size -= 1
                self.deck_index -= 1
                return True
        return False

    def reveal(self):
        cards_to_reveal = []
        for stack in range(7):
            if len(self.stacks[stack]) == 0 and self.hidden[stack] > 0:
                cards_to_reveal.append(stack)
        for stack, letter, color, x, y in detect_cards():
            if stack in cards_to_reveal:
                self.stacks[stack].append(Card(letter, color, (x, y)))
                self.hidden[stack] -= 1
                self.log("Revealing {} in on stack {}".format(self.stacks[stack][-1], stack))
        return len(cards_to_reveal) > 0

    def move_stack(self, card, source, source_index, target):
        self.log("Moving {} from {} to {}".format(card, source, target))
        drag(card.location[0], card.location[1], STACKS_VERTICALS[target], self.stacks[target][-1].location[1])
        self.stacks[target] += self.stacks[source][source_index:]
        self.stacks[source] = self.stacks[source][:source_index]

    def move_deck(self, target):
        self.log("Moving deck card to {}".format(target))
        card = self.deck[self.deck_index]
        drag(card.location[0], card.location[1], STACKS_VERTICALS[target], self.stacks[target][-1].location[1])
        self.stacks[target].append(card)
        self.deck.pop(self.deck_index)
        self.deck_size -= 1
        self.deck_index -= 1

    def find_stack_move(self, source):
        for i, source_card in enumerate(self.stacks[source]):
            for target in range(7):
                if target != source:
                    if len(self.stacks[target]) > 0:
                        target_card = self.stacks[target][-1]
                        if source_card.can_stack_on(target_card):
                            return source_card, target, i
        return None

    def find_deck_move(self):
        for target in range(7):
            if len(self.stacks[target]) > 0:
                target_card = self.stacks[target][-1]
                if self.deck[self.deck_index].can_stack_on(target_card):
                    return target


if __name__ == "__main__":
    game = Game()
    iterations = 20
    while iterations > 0:

        for stack in range(7):
            while True:
                game.found_stack(stack)
                if not game.reveal():
                    break

        while True:
            game.draw()
            if not game.found_deck():
                break

        move = game.find_deck_move()
        if move is not None:
            game.move_deck(move)
            game.reveal()

        moved_cards = []
        while True:
            moved = False
            for source in range(7):
                move = game.find_stack_move(source)
                if move is not None and str(move[0]) not in moved_cards:
                    moved_cards.append(str(move[0]))
                    game.move_stack(move[0], source, move[2], move[1])
                    moved = True
            if not moved:
                break

        iterations -= 1

    print(game)
