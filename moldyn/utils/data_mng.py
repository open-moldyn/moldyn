import numpy as np
import json
import datetime

try:
    import fcntl
except ImportError:
    import os, sys
    sys.path.append(os.path.dirname(__file__))

import datreant as dt
from zipfile import *

CATEGORY_LIST = [
    "npart",
    "spc1",
    "spc2",
    "x_a",
    "timestep",
    "border_x_type",
    "border_y_type"
]

class ParamIO(dict):
    """
    An interface to interact with json files as a dictionary.

    Designed to be used with context manager (the with statement)
    and datreant.
    Upon entering the with statement it will attempt to load the json
    file at self.file_name into itself (as a dict).
    When leaving this context, it will store itself into the json file.

    Inherits dict.

    It will try to update the tags and categories of the treant dynState.

    Attributes
    ----------
    dynState : datreant.Treant
        The treant that support the leaf (file) associated with it.
    file_name : datreant.Leaf
        The file name of the json file associated with it.

    Example
    -------
    .. code-block:: python

        t = DynState(dirpath)
        # here t.open returns a ParamIO object as the file is .json
        with t.open("params.json") as IO:
            IO["my_key"] = "my_value"
            random_var = IO[some_key]
        # upon exiting the with block, the content of IO is stored
        # in the .json file
    """

    def __init__(self, dynState : dt.Treant, file: dt.Leaf, **kwargs):
        """

        Parameters
        ----------
        dynState
        file
        kwargs
        """
        super().__init__(**kwargs)
        self.dynState = dynState
        self.file_name = file

    def __enter__(self):
        """
        Try to load the content of the json file into itself

        Try to open the json file from file_name and load the informtions
        it contains into itself.
        Will catch FileNotFoundError and JSONDecodeError

        Returns
        -------
        self : ParamIO
        """
        try:
            try:
                with open(self.file_name, mode='r') as file:
                    params = json.load(self.file_name)
                for key, value in params.items():
                    self[key] = value
            except json.decoder.JSONDecodeError:
                print("File corrupted")
        except FileNotFoundError:
            print("File does not YET exists")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Open the json file file_name and dump itself into it.

        Open the json file file_name and dump itself into it +
        update the tags and categories of dynState according to
        the CATEGORY_LIST of the module.

        Parameters
        ----------
        exc_type
        exc_val
        exc_tb
        """
        param_exists = False
        try:
            try:
                with open(self.file_name, mode='r') as file:
                    params = json.load(self.file_name)
                    param_exists = True
            except json.decoder.JSONDecodeError:
                print("File corrupted")
        except FileNotFoundError:
            print("File does not YET exists")
        if not param_exists or self != params:
            with open(self.file_name, mode='w') as file:
                json.dump(self, file, ensure_ascii=False, indent=4)
            #self.dynState.categories['last modified'] = datetime.datetime.now().strftime('%d/%m/%Y-%X')
        #self._update_categories()

    def from_dict(self, rdict : dict):
        """
        Copy rdict into itself

        Parameters
        ----------
        rdict : dict
            The remote dictionary from which to copy

        Returns
        -------

        """
        for key, value in rdict.items():
            self[key] = value

    def to_attr(self, obj):
        """
        Dump the parameter dictionary in the object (obj) as attributes of said object.

        Warning
        -------
        Will change the value of each attribute of obj that have a name
        corresponding to a key of ParamIO.

        Parameters
        ----------
        obj : an object
            The object to which it will dump its content as attributes

        """
        for key, value in self.items():
            obj.__setattr__(str(key), value)

    def _update_categories(self):
        if self["x_a"] != 0:
            self.dynState.categories["nb_species"] = 2
        for key, value in self.items():
            if key in CATEGORY_LIST:
                self.dynState.categories[key] = value

class DynStateIO:
    """
    An interface to interact with numpy save files with a context manager.


    """
    def __init__(self, dynState, file : dt.Leaf, mode):
        self.dynState = dynState
        self.mode = mode
        self.file_name = file

    def __enter__(self):
        self.file = open(self.file_name, mode=self.mode)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        if False and self.file.readable():
            self.dynState.categories['last modified'] = datetime.datetime.now().strftime('%d/%m/%Y-%X')
        """
        self.file.close()

    def save(self, arr, **kwargs):
        assert self.mode != 'r'
        np.save(self.file, arr)

    def load(self):
        assert 'r' in self.mode
        return np.load(self.file, allow_pickle=True)


class DynState(dt.Treant):
    POS = "pos.npy" # position of particles
    VEL = "velocities.npy" # final velocities
    PAR = "parameters.json" # parameters of model and simulation

    def __init__(self, treant, *, extraction_path : str = './data/tmp'):
        if isinstance(treant, dt.Treant):
            super().__init__(treant)
        elif isinstance(treant, str) and is_zipfile(treant) :
            try:
                with ZipFile(treant, 'r') as archive:
                    archive.extractall(extraction_path)
                    super().__init__(extraction_path)
            except BadZipFile:
                pass
        else:
            super().__init__(treant)


    def open(self, file, mode='r'):
        if file.endswith(".npy"):
            if not(mode.endswith("+b")):
                mode += "+b"
            return DynStateIO(self, self.leafloc[file], mode)
        elif file.endswith(".json"):
            return ParamIO(self, self.leafloc[file])
        else:
            return open(self.leafloc[file].abspath, mode)

    def add_tag(self,*tags):
        self.tags.add(*tags)

    def to_zip(self, path):
        with ZipFile(path, "w") as archive:
            for leaf in self.leaves():
                if leaf.exists:
                    print(leaf.relpath)
                    if '/' in leaf.relpath:
                        sep = '/'
                    else:
                        sep = '\\'
                    archive.write(leaf.relpath, arcname=leaf.relpath.split(sep)[-1])

    def save_model(self, model):

        # position of particles
        with self.open(self.POS, 'w') as IO:
            IO.save(model.pos)
        # parameters
        with self.open(self.PAR, 'w') as IO:
            IO.from_dict(model.params)
        # velocity
        with self.open(self.VEL, 'w') as IO:
            IO.save(model.v)

def discover(dirpath='./data', *args, **kwargs):
    return dt.discover(dirpath=dirpath, *args, **kwargs)


t = 0
def test(dirpath):
    global t
    t = DynState(dirpath)
    with t.open(t.POS, 'w') as IO:
        IO.save(np.ones(5))

    with t.open(t.POS, 'r') as IO:
        print(IO.load())

    IO = t.open(t.POS, 'w')
    IO.__enter__()

    IO.__exit__()

