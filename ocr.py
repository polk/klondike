from sklearn.neural_network import MLPClassifier
from sklearn.externals import joblib
from PIL import Image

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os


ANNOTATION_FILE = "annotations.csv"
CLASSIFIER_FILE = "ocr.pkl"
SAMPLES_FOLDER = "samples"


def annotate():

    # create file if it does not exist
    if not os.path.isfile(ANNOTATION_FILE):
        with open(ANNOTATION_FILE, "w") as file:
            file.write("file,letter")

    df = pd.read_csv(ANNOTATION_FILE)

    last_index = df.shape[0]
    while True:
        filename = os.path.join(SAMPLES_FOLDER, "{}.png".format(last_index))
        if not os.path.isfile(filename):
            break

        # plot
        plt.title(filename)
        plt.imshow(Image.open(filename))
        plt.show(block=False)

        # read input
        letter = input(filename + "> ")

        # insert into DataFrame
        df.loc[-1] = [filename, letter]
        df.index = df.index + 1
        df = df.sort_index()
        last_index += 1

        # save it
        df.to_csv(ANNOTATION_FILE, sep=",", index=False)

def grey(array):
    return .289 * array[:,:,0] + .587 * array[:,:,1] + .114 * array[:,:,2]

def apply_threshold(image):
    r, g, b = image[:,:,0], image[:,:,1], image[:,:,2]
    output = np.zeros(r.shape)
    for i in range(len(output)):
        for j in range(len(output[0])):
            if r[i, j] > 150 and g[i, j] < 20 and b[i, j] < 20:
                output[i, j] = 1
            elif r[i, j] < 20 and g[i, j] < 20 and b[i, j] < 20:
                output[i, j] = 1
    return output

def normalize(image):
    return np.ravel(apply_threshold(image))

def generate_dataset():
    annotations = pd.read_csv(ANNOTATION_FILE)
    features, classes = [], []
    for index, row in annotations.iterrows():
        image = np.array(Image.open(row["file"]))
        features.append(normalize(image))
        classes.append(row["letter"])
    return np.array(features), classes

def train(train_test_ratio=.9):
    features, classes = generate_dataset()
    split = int(train_test_ratio * len(classes))
    x_train, y_train = features[:split], classes[:split]
    x_test, y_test = features[split:], classes[split:]
    clf = MLPClassifier()
    clf.fit(x_train, y_train)
    print("Score on test set:", clf.score(x_test, y_test))
    joblib.dump(clf, CLASSIFIER_FILE)
    return clf

clf = None
if os.path.isfile(CLASSIFIER_FILE):
    clf = joblib.load(CLASSIFIER_FILE)

def predict(image):
    return clf.predict([normalize(image)])[0]

if __name__ == "__main__":
    annotate()
    clf = train(.6)
