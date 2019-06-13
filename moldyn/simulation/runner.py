"""
Simulator.
Simulates the dynamics of a model on the GPU.
"""

import os

from ..utils import gl_util
import moderngl
import numpy as np
import numexpr as ne
import scipy.interpolate as inter

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

        self.elements_number = np.array([self.layout_size] * self.groups_number)
        if self.model.npart % self.layout_size:
            self.elements_number[-1] = self.model.npart % self.layout_size

        # Chargement et paramétrage du compute shader
        consts = {
            "LAYOUT_SIZE": self.layout_size,
            "X_PERIODIC": 1,
            "Y_PERIODIC": 1,
        }
        for k in model.params:
            consts[k.upper()] = model.params[k]

        self.context = moderngl.create_standalone_context(require=430)
        self.compute_shader = self.context.compute_shader(gl_util.source(os.path.dirname(__file__)+'/templates/moldyn.glsl', consts))

        # Buffer de positions 1
        self.BUFFER_P = self.context.buffer(reserve=2*4 * self.model.npart)
        self.BUFFER_P.bind_to_storage_buffer(0)

        # Buffer de forces
        self.BUFFER_F = self.context.buffer(reserve=2*4 * self.model.npart)
        self.BUFFER_F.bind_to_storage_buffer(1)

        # Buffer d'énergies potentielles
        self.BUFFER_E = self.context.buffer(reserve=4 * self.model.npart)
        self.BUFFER_E.bind_to_storage_buffer(2)

        # Buffer de compteurs de liaisons
        self.BUFFER_COUNT = self.context.buffer(reserve=4 * self.model.npart)
        self.BUFFER_COUNT.bind_to_storage_buffer(3)

        # Buffer de paramètres
        self.BUFFER_PARAMS = self.context.buffer(reserve=4 * 5)
        self.BUFFER_PARAMS.bind_to_storage_buffer(4)

        self.T_f = lambda t:model.T

        if simulation :
            self.current_iter = simulation.current_iter

            self.T = simulation.T
            self.T_ctrl = simulation.T_ctrl
            self.EC = simulation.EC
            self.EP = simulation.EP
            self.ET = simulation.ET
            self.bonds = simulation.bonds

            self.time = simulation.time
            self.iters = simulation.iters

            self.T_cntl = simulation.T_cntl
            if self.T_cntl:
                self.T_f = simulation.T_f
            self.T_ramps = simulation.T_ramps

            self.F = simulation.F
        else:
            self.current_iter = 0

            self.T = []
            self.T_ctrl = []
            self.T_ramps = ([],[])

            self.EC = []
            self.EP = []
            self.ET = []
            self.bonds = []

            self.time = []
            self.iters = []

            self.T_cntl = False

            self.F = np.zeros(self.model.pos.shape) # Doit être initialisé et conservé d'une itération à l'autre

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

            self.BUFFER_P.write(pos.astype('f4').tobytes())

            self.compute_shader.run(group_x=self.groups_number)

            # Énergie cinétique et température
            EC = 0.5 * ne.evaluate("sum(m*v*v)")
            T = EC / knparts
            self.EC.append(EC)
            self.T.append(T)

            F[:] = np.frombuffer(self.BUFFER_F.read(), dtype=np.float32).reshape(pos.shape)

            # Énergie potentielle
            EPgl = np.frombuffer(self.BUFFER_E.read(), dtype=np.float32)
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

            bondsGL[:] = np.frombuffer(self.BUFFER_COUNT.read(), dtype=np.float32)
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
        self.T_ramps = (t, T)

        def f(x):
            if x<t[0]:
                return np.array(T[0]) # pour la consistance des types
            elif x>t[-1]:
                return np.array(T[-1])
            else:
                return f2(x)
        self.set_T_f(f)