# -*-encoding: utf-8 -*-
"""
Simulator.
Simulates the dynamics of a model (on the CPU or GPU).
"""

import numpy as np
import numexpr as ne
import scipy.interpolate as inter
import warnings

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
    simulation : Simulation
        Simulation to copy.
        The simulation is copied, and the computing module reinitialized.
    prefer_gpu : bool
        Specifies if GPU should be used to compute inter-atomic forces.
        Defaults to `True`, as it generally results in a significant speed gain.

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
    F : numpy.ndarray
        Last computed forces applied to atoms. Initialized to zeros.

        Warning
        -------
        Changing the values will affect behavior of the model.
    """

    def __init__(self, model = None, simulation = None, prefer_gpu = True):

        if simulation:
            model = simulation.model

        self.model = model.copy()

        # paramétrage du module de calcul
        consts = dict()
        for k in model.params:
            consts[k.upper()] = model.params[k]

        if prefer_gpu:
            try:
                self._compute = ForcesComputeGPU(consts)
            except:
                warnings.warn("GPU not available, falling back on CPU. GPU compute needs OpenGL >=4.3.")
                self._compute = ForcesComputeCPU(consts)
        else:
            self._compute = ForcesComputeCPU(consts)

        self.T_f = lambda t:self.T[-1]
        self.Fx_f = lambda t:0.0
        self.Fy_f = lambda t:0.0

        if simulation :
            self.current_iter = simulation.current_iter

            self.state_fct = simulation.state_fct

            self.T_cntl = simulation.T_cntl
            if self.T_cntl:
                self.T_f = simulation.T_f
            self.Fx_f = simulation.Fx_f
            self.Fy_f = simulation.Fy_f

            self.F = simulation.F
        else:
            self.current_iter = 0

            self.state_fct = dict()

            self.state_fct["T"] = []
            self.state_fct["T_ctrl"] = []
            self.state_fct["T_ramps"] = [[],[]]

            self.state_fct["Fx_ramps"] = [[],[]]
            self.state_fct["Fy_ramps"] = [[],[]]

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
        gamma = self.model.gamma

        limInf = self.model.lim_inf
        limSup = self.model.lim_sup
        length = self.model.length

        F = self.F
        bondsGL = np.zeros(self.model.npart)

        periodic = self.model.x_periodic or self.model.y_periodic

        apply_up_zone_forces = self.model.up_apply_force_x or self.model.up_apply_force_y
        #up_zone_force = self.model.up_forces
        up_zone_limit = self.model.up_zone_lower_limit
        low_zone_block = self.model.low_block
        low_zone_limit = self.model.low_zone_upper_limit

        if periodic:
            length *= (self.model.x_periodic, self.model.y_periodic)
            # on n'applique les conditions périodiques que selon le(s) axe(s) spécifié(s)

        kick = "F"
        micro_ke = "sum(m*(v-v_avg)**2)"
        if apply_up_zone_forces:
            kick = "(F+up_mask*up_zone_force)"
            up_mask = np.zeros(pos.shape)

        compute_rotative_term = apply_up_zone_forces and not(self.model.y_periodic)
        if compute_rotative_term:
            micro_ke = "sum(m*(v-v_avg-rotative_term)**2)"
            rotative_term = np.zeros(pos.shape)
            y_middle = (self.model.y_lim_sup + self.model.y_lim_inf)/2
            from_y_middle = np.zeros(npart)
        kick = "(v + ("+kick+"*dtm))"
        if betaC:
            kick += "*sqrt(1 + gamma*(T_v/T - 1))"
        if low_zone_block:
            # On présélectionne les atomes bloqués, afin que leur nombre ne change pas
            low_block_mask = pos[:,1] > low_zone_limit
            low_block_mask = np.array([low_block_mask]*2).T
            kick += "*low_block_mask"

        for i in range(n):

            t = self.current_iter * dt # l'heure, qui sert pour le calcul de température

            ne.evaluate("pos + v*dt2", out=pos)  # half drift

            # conditions périodiques de bord
            if periodic:
                ne.evaluate("pos + (pos<limInf)*length - (pos>limSup)*length", out=pos)

            self._compute.set_pos(pos)

            v_avg = np.average(v, axis=0)

            if apply_up_zone_forces: # recalcul du masque, parce que ça bouge
                up_zone_force = self.F_f(t)
                up_mask[:,:] = np.array([pos[:,1] > up_zone_limit]*2).T
            if compute_rotative_term:
                from_y_middle[:] = pos[:,1]-y_middle
                rotative_term[:,0] = (np.sum(v[:,0]/from_y_middle)/npart)*from_y_middle

            # Énergie cinétique et température
            EC = 0.5 * ne.evaluate(micro_ke)
            T = EC / knparts
            self.EC.append(EC)
            self.T.append(T)

            F[:] = self._compute.get_F()

            # Énergie potentielle
            EPgl = self._compute.get_PE()
            EP = 0.5 * ne.evaluate("sum(EPgl)")
            self.EP.append(EP)
            self.ET.append(EC + EP)

            # Thermostat
            T_v = self.T_f(t)
            self.T_ctrl.append(T_v)
            ne.evaluate(kick, out=v) # kick

            ne.evaluate("pos + v*dt2", out=pos)  # half drift

            bondsGL[:] = self._compute.get_COUNT()
            self.bonds.append(inv2npart*ne.evaluate("sum(bondsGL)"))

            self.iters.append(self.current_iter)
            self.time.append(t)

            if callback:
                callback(self)

            self.current_iter += 1

    def _f(self, t, y):
        f2 = inter.interp1d(t, y)

        def f(x):
            if x<t[0]:
                return y[0]
            elif x>t[-1]:
                return y[-1]
            else:
                return float(f2(x)) # pour la consistance des types

        return f

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
        if len(t)>1:
            self.state_fct["T_ramps"] = [list(t), list(T)]
            self.T_ramps = self.state_fct["T_ramps"]
            self.set_T_f(self._f(t, T))

    def F_f(self, t):
        """

        Parameters
        ----------
        t
            Time in seconds.
        Returns
        -------
        numpy.ndarray
              External forces applied at time `t` (2-component vector).
        """
        return np.array((self.Fx_f(t), self.Fy_f(t)))

    def set_Fx_ramps(self, t, Fx):
        """
        Creates a function based on ramps and uses it for external forces control along axis x.
        See `set_T_ramps` for further details.

        Parameters
        ----------
        t : array
            Time.
        Fx : array
            Associated forces.
        """
        if len(t)>1:
            self.state_fct["Fx_ramps"] = [list(t), list(Fx)]
            self.Fx_ramps = self.state_fct["Fx_ramps"]
            self.Fx_f = self._f(t, Fx)

    def set_Fy_ramps(self, t, Fy):
        """
        Creates a function based on ramps and uses it for external forces control along axis y.
        See `set_T_ramps` for further details.

        Parameters
        ----------
        t : array
            Time.
        Fy : array
            Associated forces.
        """
        if len(t)>1:
            self.state_fct["Fy_ramps"] = [list(t), list(Fy)]
            self.Fy_ramps = self.state_fct["Fy_ramps"]
            self.Fy_f = self._f(t, Fy)