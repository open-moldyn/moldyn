from datreant import *
import numpy as np
import json


class ParamIO(dict):

    def __init__(self, dynState, file: str, **kwargs):
        super().__init__(**kwargs)
        self.dynState = dynState
        self.file_name = file

    def __enter__(self):
        with open(self.file_name, mode='r') as file:
            params = json.load(self.file_name,
                               parse_float=True, parse_int=True)
        for key, value in params.items():
            self[key] = value
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.file_name, mode='w') as file:
            json.dump(self.params, ensure_ascii=False, indent=4)

    def fromDict(self, rdict):
        for key, value in rdict.items():
            self[key] = value


class DynStateIO:
    def __init__(self, dynState, file : str, mode):
        self.dynState = dynState
        self.mode = mode
        self.file_name = file

    def __enter__(self):
        self.file = open(self.file_name, mode=self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def save(self, *args, **kwargs):
        assert self.mode != 'r'
        if self.file_name.endswith(".npy"):
            np.save(self.file, args)

    def load(self, N):
        assert self.mode == 'r'
        return np.load(self.file)


class DynState(Treant):
    POS = "pos.npy"
    VEL = "velocities.npy"
    PAR = "parameters.json"

    def __init__(self, dirpath, treant):
        super().__init__(treant)

    def open(self, file, mode='r'):
        if mode=='r':
            assert file in self.leaves()
        if file.endswith(".npy"):
            return DynStateIO(self, self.leafloc[file], mode)
        elif file.endswith(".json"):
            return ParamIO(self, self.leafloc[file])