# Modèles à simuler

import numpy as np

class Model:

    def __init__(self):

        self.pos = np.zeros(npart,2)
        self.v = np.zeros(npart,2)

        self.params = {
            "m":1,
        }

