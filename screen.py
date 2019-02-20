"""screen.py

Handle screen capture procedures.

"""

from PIL import Image, ImageGrab

import matplotlib.pyplot as plt
import numpy as np
import glob
import time
import cv2
import os

from directkeys import clic
from misc import *
from ocr import predict, apply_threshold


def load_template(filename):
    im = Image.open(os.path.join(TEMPLATE_FOLDER, filename))
    im.load()
    return np.array(im)


TEMPLATE_CARD = load_template("card.png")
TEMPLATE_SPADE = load_template("spade.png")
TEMPLATE_CLUB = load_template("club.png")
TEMPLATE_HEART = load_template("heart.png")
TEMPLATE_DIAMOND = load_template("diamond.png")
TEMPLATE_COLORS = [
    ('diamond', TEMPLATE_DIAMOND),
    ('heart', TEMPLATE_HEART),
    ('spade', TEMPLATE_SPADE),
    ('club', TEMPLATE_CLUB)
]

BBOX_BOARD = (960, 270, 1920, 1044)
BBOX_DECK = (1121, 92, 1300, 136)


def generate_template_card(center=(562, 197), radius=10, filename="card.png"):
    screen = np.array(ImageGrab.grab(BBOX_BOARD))
    template = screen[
        center[1] - radius : center[1] + radius,
        center[0] - radius : center[0] + radius,
        :]
    Image.fromarray(template).save(os.path.join(TEMPLATE_FOLDER, filename))


def generate_template_colors():
    for stack, image_letter, image_color, x, y in locate_cards():
        Image.fromarray(image_color).save("{}.png".format(time.time()))


def generate_samples(rounds):
    index = len(glob.glob(os.path.join(SAMPLES_FOLDER, "*.png")))
    for round in range(rounds):
        clic(1018, 1006, 1)
        time.sleep(2)
        for stack, image_letter, image_color, x, y in locate_cards():
            Image.fromarray(image_letter).save(os.path.join(SAMPLES_FOLDER, "{}.png".format(index)))
            index += 1


def detect_color(image):

    def keep_maximum(output):
        maximum = -1
        for element in list(output):
            if element > maximum:
                maximum = element
        return maximum

    color_detection = [
        (i, keep_maximum(cv2.matchTemplate(image, item[1], cv2.TM_CCOEFF_NORMED)))
        for i, item in enumerate(TEMPLATE_COLORS)
    ]

    return sorted(color_detection, key=lambda item: -item[1])[0][0]


def locate_cards(threshold=.95, margin=10, plot=False):

    screen = np.array(ImageGrab.grab(BBOX_BOARD))

    matches = cv2.matchTemplate(screen, TEMPLATE_CARD, cv2.TM_CCOEFF_NORMED)
    matches_pruned = np.where(matches >= threshold)

    cards = []
    last_pt = -margin, -margin
    for pt in zip(*matches_pruned[::-1]):
        if pt[0] - last_pt[0] >= margin:
            last_pt = pt

            # extract images
            x1, x2 = pt[0] + 8, pt[0] + 29
            y1, y2 = pt[1] - 122, pt[1] - 102
            image_letter = screen[y1:y2, x1:x2, :]
            image_color = screen[y2-2:y2+15, x1+2:x2, :]

            # detect column
            min_dist = None
            stack = None
            for i, dist in enumerate(map(lambda x: (x - x1)**2, STACK_POSITIONS)):
                if i == 0 or dist < min_dist:
                    stack = i
                    min_dist = dist

            if plot:
                plt.figure()
                plt.subplot(1, 2, 1)
                plt.title("stack: {}".format(stack + 1))
                plt.imshow(image_letter)
                plt.subplot(1, 2, 2)
                plt.imshow(image_color)
                plt.show(block=False)

            cards.append((stack, image_letter, image_color, x2, y2))

    return cards


def detect_cards(threshold=.95, margin=10, plot=False):

    located_cards = locate_cards(threshold, margin)
    detected_cards = []

    for stack, image_letter, image_color, x, y in located_cards:

        detected_cards.append(
            (stack,
            predict(image_letter),
            detect_color(image_color),
            x + BBOX_BOARD[0],
            y + BBOX_BOARD[1]))

        if plot:
            plt.figure()
            plt.subplot(1, 2, 1)
            plt.title("stack: {}".format(stack + 1))
            plt.imshow(image_letter)
            plt.subplot(1, 2, 2)
            plt.title(str_card(detected_cards[-1][1], detected_cards[-1][2]))
            plt.imshow(image_color)
            plt.show(block=False)

    return detected_cards


def detect_deck(plot=False):

    screen = np.array(ImageGrab.grab(BBOX_DECK))

    root = 9, 5
    if screen[10, 128, 0] > 100:
        root = 9, 27
    if screen[10, 140, 0] > 100:
        root = 9, 48
    image_letter = screen[root[0]:root[0]+20, root[1]:root[1]+21, :]
    image_color = screen[root[0]+18:root[0]+35, root[1]+2:root[1]+21, :]

    letter, color = predict(image_letter), detect_color(image_color)

    if plot:
        plt.subplot(1, 2, 1)
        plt.title("deck")
        plt.imshow(image_letter)
        plt.subplot(1, 2, 2)
        plt.title(str_card(letter, color))
        plt.imshow(image_color)
        plt.show()

    return letter, color, BBOX_DECK[0]+root[1]+21, BBOX_DECK[1]+root[0]+20


if __name__ == "__main__":
    # generate_template_card()
    # generate_template_colors()
    # generate_samples(10)
    detect_cards(plot=True)
    # detect_deck(plot=True)
    plt.show(block=True)
