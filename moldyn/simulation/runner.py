"""
Simulator.
Simulates the dynamics of a model (on the CPU or GPU).
"""

import os

from ..utils import gl_util
import moderngl
import numpy as np
import numexpr as ne
import scipy.interpolate as inter

from .forces_CPU import ForcesComputeCPU
from .forces_GPU import ForcesComputeGPU

class Simulation:
    """
    Simulator for a model.

    Parameters
    ----------
    model : builder.Model
        Model to simulate.
        The original model object is copied, and thus preserved, which allows it to serve as a reference.

    Attributes
    ----------
    model : builder.Model
        Model that is simulated.

        -------
        Warning
        -------
        Works as usual, but changing its properties will not affect the simulation as intended.
        You should construct another simulation from this model to correctly take in account the changes.
        This is due to the fact that some values (eg. Lennard-Jones parameters) are treated as constants during shader
        initialisation, in order to speed up the calculations.
    current_iter : int
        Number of iterations already computed, since initialisation.
    context : moderngl.Context
        ModernGL context used to build and run compute shader.
    F : np.array
        Last computed forces applied to atoms. Initialized to zeros.

        Warning
        -------
        Changing the values will affect behavior of the model.
    """

    def __init__(self, model = None, simulation = None):

        if simulation:
            model = simulation.model

        self.model = model.copy()

        # Découpage de la liste en segments de taille acceptable par le GPU
        #max_layout_size = gl_util.testMaxSizes()
        max_layout_size = 256 # Probablement optimal (en tout cas d'après essais et guides de bonnes pratiques)
        self.groups_number = int(np.ceil(self.model.npart / max_layout_size))
        self.layout_size = int(np.ceil(self.model.npart / self.groups_number))

        # Chargement et paramétrage du compute shader
        consts = {
            "LAYOUT_SIZE": self.layout_size,
            "X_PERIODIC": 1,
            "Y_PERIODIC": 1,
        }
        for k in model.params:
            consts[k.upper()] = model.params[k]

        self.compute_GPU = ForcesComputeCPU(consts)
        #self.compute_CPU = ForcesComputeCPU(consts)

        self.T_f = lambda t:model.T

        if simulation :
            self.current_iter = simulation.current_iter

            self.state_fct = simulation.state_fct

            self.T_cntl = simulation.T_cntl
            if self.T_cntl:
                self.T_f = simulation.T_f

            self.F = simulation.F
        else:
            self.current_iter = 0

            self.state_fct = dict()

            self.state_fct["T"] = []
            self.state_fct["T_ctrl"] = []
            self.state_fct["T_ramps"] = [[],[]]

            self.state_fct["EC"] = []
            self.state_fct["EP"] = []
            self.state_fct["ET"] = []
            self.state_fct["bonds"] = []

            self.state_fct["time"] = []
            self.state_fct["iters"] = []

            self.T_cntl = False

            self.F = np.zeros(self.model.pos.shape) # Doit être initialisé et conservé d'une itération à l'autre

        for s in self.state_fct:
            self.__setattr__(s, self.state_fct[s])

    def iter(self, n=1, callback=None):
        """
        Iterates one or more simulation steps.

        Basically, follows the Position-Verlet method to update positions and speeds, and computes inter-atomic forces
        derived from Lennard-Jones potential.

        Parameters
        ----------
        n: int
            Number of iterations to perform.
        callback : callable
            A callback function that must take the Simulation object as first argument.
            It is called at the end of each iteration.

        Note
        ----
        Setting n is significantly faster than calling :py:meth:`iter` several times.

        Example
        -------
        .. code-block:: python

            model.iter(5)

        Returns
        -------

        """

        for s in self.state_fct:
            self.__setattr__(s, self.state_fct[s])

        betaC = self.T_cntl # Contrôle de la température

        # on crée des alias aux valeurs du modèles pour numexpr
        v = self.model.v
        pos = self.model.pos
        dt = self.model.dt
        dt2 = dt/2.0
        m = self.model.m
        dtm = dt/m
        npart = self.model.npart
        inv2npart = 0.5/npart
        knparts = self.model.kB * npart

        limInf = self.model.lim_inf
        limSup = self.model.lim_sup
        length = self.model.length

        F = self.F
        bondsGL = np.zeros(self.model.npart)

        periodic = self.model.x_periodic or self.model.y_periodic

        if periodic:
            length *= (self.model.x_periodic, self.model.y_periodic)
            # on n'applique les conditions périodiques que selon le(s) axe(s) spécifié(s)

        TVOULUE = 0

        for i in range(n):

            t = self.current_iter * dt # l'heure, qui sert pour le calcul de température

            ne.evaluate("pos + v*dt2", out=pos)  # half drift

            # conditions périodiques de bord
            if periodic:
                ne.evaluate("pos + (pos<limInf)*length - (pos>limSup)*length", out=pos)

            self.compute_GPU.set_pos(pos)

            # Énergie cinétique et température
            EC = 0.5 * ne.evaluate("sum(m*v*v)")
            T = EC / knparts
            self.EC.append(EC)
            self.T.append(T)

            F[:] = self.compute_GPU.get_F()

            # Énergie potentielle
            EPgl = self.compute_GPU.get_PE()
            EP = 0.5 * ne.evaluate("sum(EPgl)")
            self.EP.append(EP)
            self.ET.append(EC + EP)

            # Thermostat
            self.T_ctrl.append(self.T_f(t))
            if betaC:
                beta = np.sqrt(1+self.model.gamma*(self.T_f(t)/T-1))
                ne.evaluate("(v + (F*dtm))*beta", out=v) # kick

            else:
                ne.evaluate("v + (F*dtm)", out=v)  # kick

            ne.evaluate("pos + v*dt2", out=pos)  # half drift

            bondsGL[:] = self.compute_GPU.get_COUNT()
            self.bonds.append(inv2npart*ne.evaluate("sum(bondsGL)"))

            self.iters.append(self.current_iter)
            self.time.append(t)

            if callback:
                callback(self)

            self.current_iter += 1

    def set_T_f(self, f):
        """
        Sets function that controls temperature.

        Parameters
        ----------
        f : callable
            Must take time (float) as an argument and return temperature (in K, float).

        Returns
        -------

        """
        self.T_cntl = True
        self.T_f = f
        self.model.T = f(self.current_iter*self.model.dt)

    def set_T_ramps(self, t, T):
        """
        Creates a function based on ramps and uses it for temperature control.
        Values of the function are interpolated between points given in `t` and `T`.
        Temperature is supposed constant before the first point and after the last one.

        Parameters
        ----------
        t : array
            Time.
        T : array
            Associated temperatures.

        Returns
        -------

        """
        f2 = inter.interp1d(t, T)
        self.state_fct["T_ramps"] = [list(t), list(T)]
        self.T_ramps = self.state_fct["T_ramps"]

        def f(x):
            if x<t[0]:
                return T[0]
            elif x>t[-1]:
                return T[-1]
            else:
                return float(f2(x)) # pour la consistance des types
        self.set_T_f(f)