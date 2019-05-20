from datreant import *
import numpy as np
import json


class ParamIO(dict):

    def __init__(self, dynState, file: str, **kwargs):
        super().__init__(**kwargs)
        self.dynState = dynState
        self.file_name = file

    def __enter__(self):
        try:
            with open(self.file_name, mode='r') as file:
                params = json.load(self.file_name,
                                   parse_float=True, parse_int=True)

            for key, value in params.items():
                self[key] = value

        except FileNotFoundError:
            print("File does not YET exists")
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.file_name, mode='w') as file:
            json.dump(dict(self), file, ensure_ascii=False, indent=4)

    def fromDict(self, rdict):
        for key, value in rdict.items():
            self[key] = value


class DynStateIO:
    def __init__(self, dynState, file : Leaf, mode):
        self.dynState = dynState
        self.mode = mode
        self.file_name = file

    def __enter__(self):
        self.file = open(self.file_name, mode=self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def save(self, arr, **kwargs):
        assert self.mode != 'r'
        np.save(self.file, arr)

    def load(self):
        assert 'r' in self.mode
        return np.load(self.file, allow_pickle=True)


class DynState(Treant):
    POS = "pos.npy"
    VEL = "velocities.npy"
    PAR = "parameters.json"

    def __init__(self, treant):
        super().__init__(treant)

    def open(self, file, mode='r'):
        if file.endswith(".npy"):
            if not(mode.endswith("+b")):
                mode += "+b"
            return DynStateIO(self, self.leafloc[file], mode)
        elif file.endswith(".json"):
            return ParamIO(self, self.leafloc[file])


t = 0
def test(dirpath):
    global t
    t = DynState(dirpath)
    with t.open(t.POS, 'w') as IO:
        IO.save(np.ones(5))

    with t.open(t.POS, 'r') as IO:
        print(IO.load())

