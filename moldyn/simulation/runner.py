"""
Simulator.
Simulates the dynamics of a model on the GPU.
"""

from ..utils import gl_util
import moderngl
import numpy as np
import numexpr as ne

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
    current_iter : int
        Number of iterations already computed, since initialisation.
    context : moderngl.Context
        ModernGL context used to build and run compute shader.
    F
        Last computed forces applied to atoms.
    """

    def __init__(self, model):

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
        self.compute_shader = self.context.compute_shader(gl_util.source('templates/moldyn.glsl', consts))

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

        self.current_iter = 0

        self.F = np.zeros(self.model.pos.shape) # Doit être initialisé et conservé d'une itération à l'autre

    def iter(self, n=1):
        """
        iterates one or more simulation steps

        Parameters
        ----------
        n: int
            number of iterations to perform

        Returns
        -------

        Notes
        -----
        Setting n is significantly faster than calling `iter` several times.

        Example
        -------
        .. code-block:: python

            model.iter(5)

        """

        self.current_iter += n

        betaC = False # Contrôle de la température, à délocaliser
        regEP = False

        # on crée des alias aux valeurs du modèles pour numexpr
        v = self.model.v
        pos = self.model.pos
        dt = self.model.dt
        m = self.model.m
        dt2m = dt/(2*m)
        knparts = self.model.kB * self.model.npart

        limInf = self.model.lim_inf
        limSup = self.model.lim_sup
        length = self.model.length

        F = self.F

        v2 = np.zeros(pos.shape)

        periodic = self.model.x_periodic or self.model.y_periodic

        if periodic:
            length *= (self.model.x_periodic, self.model.y_periodic)
            # on n'applique les conditions périodiques que selon le(s) axe(s) spécifié(s)

        TVOULUE = 0

        for i in range(n):

            ne.evaluate("v + F*dt2m", out=v2)
            ne.evaluate("pos + v2*dt", out=pos)

            # conditions périodiques de bord
            if periodic:
                ne.evaluate("pos + (pos<limInf)*length - (pos>limSup)*length", out=pos)

            self.BUFFER_P.write(pos.astype('f4').tobytes())

            self.compute_shader.run(group_x=self.groups_number)

            # Énergie cinétique, à mettre au conditionnel
            EC = 0.5 * ne.evaluate("sum(m*v*v)")
            T = EC / knparts

            F = np.frombuffer(self.BUFFER_F.read(), dtype=np.float32).reshape(pos.shape)

            # Énergie potentielle, à mettre au conditionnel, y compris dans le shader
            if regEP:
                EPgl = np.frombuffer(self.BUFFER_E.read(), dtype=np.float32)
                EP = 0.5 * ne.evaluate("sum(EPgl)")

            # Thermostat
            if betaC:
                beta = np.sqrt(1+self.model.gamma*(TVOULUE/T-1))
                ne.evaluate("(v2 + (F*dt2m))*beta", out=v)
            else:
                ne.evaluate("v2 + (F*dt2m)", out=v)

