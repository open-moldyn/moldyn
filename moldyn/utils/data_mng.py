# -*-encoding: utf-8 -*-
import os, sys
from functools import wraps

import numpy as np
import json
import datetime
try:
    import fcntl
except ImportError:
    sys.path.append(os.path.dirname(__file__))

from . import datreant as dt
from zipfile import *
from . import appdirs

data_path = appdirs.user_data_dir("open-moldyn")
tmp_path = data_path + "/tmp_sim"
tmp1_path = data_path + "/tmp_mdl"

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
            with open(self.file_name, mode='r') as file:
                params = json.load(self.file_name)
            for key, value in params.items():
                self[key] = value
        except json.decoder.JSONDecodeError:
            print("File corrupted")
            pass
        except FileNotFoundError:
            #print("File does not YET exists")
            pass

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
            with open(self.file_name, mode='r') as file:
                params = json.load(self.file_name)
                param_exists = True
        except json.decoder.JSONDecodeError:
            print("File corrupted")
            pass
        except FileNotFoundError:
            #print("File does not YET exists")
            pass
        if not param_exists or self != params:
            with open(self.file_name, mode='w') as file:
                json.dump(self, file, ensure_ascii=False, indent=4)
            #self.dynState.categories['last modified'] = datetime.datetime.now().strftime('%d/%m/%Y-%X')
        #self._update_categories()

    def from_dict(self, rdict: dict):
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

    def to_dict(self, rdict : dict):
        """
        Copy itself into the remote dictionary
        Parameters
        ----------
        rdict : dict
            The remot dictionary to which to copy

        Returns
        -------

        """
        for key, value in self.items():
            rdict[key] = value

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

class NumpyIO:
    """
    An interface to interact with numpy save files with a context manager.

    Attributes
    ----------
    dynState : datreant.Treant
        The treant that support the leaf (file) associated with it.
    mode : str
        The access mode of the file (usually 'r' or 'w' or 'a')
    file_name : datreant.Leaf
        The file name of the .npy file associated with it.
    file : file object
        the file that is opened (contains None until entering a context manager)

    Example
    -------
    .. code-block:: python

        t = DynState(dirpath)
        # here t.open returns a NumpyIO object as the file is .npy
        with t.open("pos.npy", 'r') as IO:
            arr = IO.load() #load an array
        with t.open("pos.npy", 'w') as IO:
            IO.save(arr) #save an array
    """
    def __init__(self, dynState, file : dt.Leaf, mode):
        self.dynState = dynState
        self.mode = mode
        self.file_name = file
        self.file = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        """
        Open the internal file.
        """
        self.file = open(self.file_name, mode=self.mode)

    def close(self):
        """
        Close the internal file.
        """
        self.file.close()

    def save(self, arr):
        """
        Save an array to the opened file.

        Parameters
        ----------
        arr : ndarray (numpy)
            The array to be stored
        Returns
        -------

        """
        np.save(self.file, arr)

    def load(self):
        """
        Load an array stored in the file.

        Returns
        -------
        arr : ndarray
            the array loaded
        """
        return np.load(self.file, allow_pickle=True)


class DynState(dt.Treant):
    """
    A Treant specialized for handling .npy and .json files for moldyn

    Attributes
    ----------
    POS: str
        standard name of the position file ("pos.npy")
    POS_H: str
        standard name of the position history file ("pos_history.npy")
    VEL: str
        standard name of the velocity file ("velocities.npy")
    STATE_FCT: str
        standard name of the state function file ("state_fct.json")
    PAR: str
        standard name of the parameter file ("parameters.json")
    """
    POS = "pos.npy"  # position of particles
    POS_H = "pos_history.npy"  # history of position
    VEL = "velocities.npy"  # final velocities
    STATE_FCT = "state_fct.json"  # state functions (energy, temperature...)
    PAR = "parameters.json"  # parameters of model and simulation

    def __init__(self, treant, *, extraction_path : str = data_path+'/tmp'):
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
        """
        Open the file in this tree (ie. directory and subdir).
        Return the appropriate IO class depending of the type of the file.

        If the type is not recognize, it opens the file and return the
        BytesIO or StringIO object.

        Parameters
        ----------
        file: str
            The name of the file. This file must be in this tree (ie. directory and subdir).
        mode: str (default='r')
            The mode with which to open the file :
                - 'r' to read
                - 'w' to write
                - 'a' to append
                - 'b' to read or write bytes (eg. 'w+b' to write bytes)

        Returns
        -------
        If file is a .npy file, return a NumpyIO object.
        If file is a .json file, return a ParamIO object.
        Else, return a StringIO or a BytesIO depending on mode.

        Note
        ----

        This method is designed to be used wih a context manager like this

        .. code-block:: python

            t = DynState(dirpath)
            # here t.open returns a NumpyIO object as the file is .npy
            with t.open("pos.npy", 'r') as IO:
                arr = IO.load() #load an array
            with t.open("pos.npy", 'w') as IO:
                IO.save(arr) #save an array
        """
        if file.endswith(".npy"):
            if not(mode.endswith("+b")):
                mode += "+b"
            return NumpyIO(self, self.leafloc[file], mode)
        elif file.endswith(".json"):
            return ParamIO(self, self.leafloc[file])
        else:
            return open(self.leafloc[file].abspath, mode)

    def add_tag(self,*tags):
        self.tags.add(*tags)

    def to_zip(self, path: str):
        """
        Zip every leaf (aka. file) of the dynState treant into an archive at path.

        Parameters
        ----------
        path : str
            The path of the archive.
        """
        with ZipFile(path, "w") as archive:
            for leaf in self.leaves():
                if leaf.exists:
                    leaf_path = str(leaf.abspath).replace('\\', '/').split('/')[-1]
                    archive.write(leaf.relpath, arcname=leaf_path)

    def save_model(self, model):
        """
        Save the positions, the velocities and the parameters of the model.

        The position and velocity arrays are saved as numpy files and
        the parameter dictionary as a .json file

        Parameters
        ----------
        model : simulation.builder.Model
            The model to be saved.
        """

        # position of particles
        with self.open(self.POS, 'w') as IO:
            IO.save(model.pos)
        # parameters
        with self.open(self.PAR, 'w') as IO:
            IO.from_dict(model.params)
        # velocity
        with self.open(self.VEL, 'w') as IO:
            IO.save(model.v)

@wraps(dt.discover)
def discover(dirpath=data_path, *args, **kwargs):
    return dt.discover(dirpath=dirpath, *args, **kwargs)



