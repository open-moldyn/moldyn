"""
Model builder.
Stores and defines physical properties of a group of atoms.
"""

import numpy as np
import numexpr as ne

class Model:
    """

    Attributes
    ----------
    T : float
        Temperature.
        Is calculated from the average kinetic energy of the atoms.
        May be set to any value, in which case atoms' speed will be scaled to match the desired temperature.
    EC : float
        Total kinetic energy. Cannot be changed as-is.
    kB : float
        Boltzmann constant. If changed, will affect the way the model behaves regarding temperature.
    pos
    v : np.array
        List of atom positions and speeds. First axis represents the atom, second axis the dimension (x or y).
    dt : float
        Timestep used for simulation.
        An acceptable value is calculated when species are defined, but it may be set to anything else.
    npart : int
        Total number of atoms.
    x_a : float
        Mole fraction of species A.
    n_a : int
        Atom number for species A, calculated from `x_a` and `npart` If set, `x_a` will be recalculated.
    epsilon_a
    epsilon_b : float
        Epsilon value (J, in Lennard-Jones potential) for species a or b.
    sigma_a
    sigma_b : float
        Sigma value (m, in Lennard-Jones potential) for species a or b.
    epsilon_ab
    sigma_ab : float
        Inter-species epsilon and sigma values. Cannot be set as-is. If you want to change these values, modify the
        corresponding items in the `params` dict.
    re_a
    re_b
    re_ab : float
        Estimated radius of minimum potential energy.
    rcut_fact : float
        When the model is simulated, atoms further than :code:`rcut_fact*re` do not interact. Defaults to 2.0.
    params : dict
        Model parameters, needed for the simulation. Changing directly these values may lead to unpredicted behaviour
        if ot documented.
    kong : dict
        Kong rules to estimate inter-species sigma and epsilon parameters.
    inter_species_rule : dict
        Rules to automatically estimate inter-species sigma and epsilon parameters. Defaults to `kong`.
    x_lim_inf
    y_lim_inf : float
        Lower x and y position of the box boundaries.
    x_lim_sup
    y_lim_sup : float
        Upper x and y position of the box boundaries.
    length_x
    length_y : float
        Size of the box along x and y axis. Those parameter are tied with `*_lim_***` and any change on one of them is
        correctly taken in account.
    lim_inf
    lim_sup
    length : np.array
        2 elements wide array containing corresponding :code:`(x_*, y_*)` values. Cannot be changed as-is.
    x_periodic
    y_periodic : int
        Defines periodic conditions for x and y axis. Set to 1 to define periodic boundary condition or 0 to live in
        an infinite empty space.
    mass : float
        Total mass in the model. Cannot be changed as-is.
    m : np.array
        Mass of each atom. Shape is :code:`(npart, 2)` in order to facilitate calculations of kinetic energy and
        Newton's second law. You should not change those values unless you know what you are doing.

    """

    kong = {
        "sigma":"(  (epsilon_a * sigma_a**12 * (1 + ((epsilon_b*sigma_b**12)/(epsilon_a*sigma_a**12))**(1/13))**13)  /   (2**13 * np.sqrt(epsilon_b*sigma_b**6*epsilon_a*sigma_a**6)) )**(1/6)",
        "epsilon":"np.sqrt(epsilon_b*sigma_b**6*epsilon_a*sigma_a**6)/sigma_ab**6",
    }

    kB = 1.38064852e-23 # en unités SI

    def __init__(self, pos=None, v=None, npart=0, x_a=1.0):

        if pos:
            self.pos = pos
            npart = len(pos)
        else:
            self.pos = np.zeros((npart,2))

        if v and pos:
            self.v = v
        else:
            self.v = np.zeros((npart,2))

        self.inter_species_rule = self.kong

        self.params = {
            "npart":npart,
            "n_a":npart,
            "rcut_fact":2.0,
            "x_periodic":0,
            "y_periodic":0,
            "x_lim_inf":0,
            "y_lim_inf":0,
        }

        self.x_lim_sup = 0
        self.y_lim_sup = 0
        self.set_ab((1,1,1),(1,1,1))
        self.x_a = x_a
        self.set_dt()
        self.set_periodic_boundary(0,0)

        self._derived_values_f = {}
        for f in self._derived_values:
            self._derived_values_f[f] = eval("self.get_" + f)

    def copy(self):
        """

        Returns
        -------
        model.Model
            Copy of the current model
        """
        m = Model()
        m.pos = self.pos.copy()
        m.v = self.v.copy()
        m.params = self.params.copy()
        m._m()
        return m

    __copy__ = copy

    _derived_values = [  # Les valeurs calculables à partir des autres
        "T",
        "EC",
        "mass",
        "length",
        "lim_sup",
        "lim_inf",
    ]

    def __getattr__(self, item):
        if item in self._derived_values:
            return self._derived_values_f[item]()
        elif item in self.params:
            return self.params[item]
        else:
            raise AttributeError(item)

    _special_values=[ # Les valeurs à vérifier ou  à transformer avant enregistrement
        "T",
        "x_a",
        "n_a",
        "x_periodic",
        "y_periodic",
        "x_lim_sup",
        "x_lim_inf",
        "y_lim_sup",
        "y_lim_inf",
        "length_x",
        "length_y",
        "dt",
    ]

    def __setattr__(self, key, value):
        if key in self._special_values:
            f = eval("self.set_"+key)
            f(value)
        else:
            super(Model, self).__setattr__(key, value)

    def _set_species(self, epsilon : float, sigma : float, m : float, sp : str):
        self.params["epsilon_"+sp] = epsilon
        self.params["sigma_"+sp] = sigma
        self.params["re_"+sp] = 2.0**(1.0/6.0)*sigma
        self.params["rcut_"+sp] = self.rcut_fact*self.params["re_"+sp]
        self.params["m_"+sp] = m

    def set_a(self, epsilon : float, sigma : float, m : float):
        """
        Sets species a parameters.

        Parameters
        ----------
        epsilon : float
            Epsilon in Lennard-Jones potential.
        sigma : float
            Sigma in Lennard-Jones potential.
        m : float
            Mass of the atom.

        Returns
        -------

        """
        self._set_species(epsilon, sigma, m, "a")

    def set_b(self, epsilon : float, sigma : float, m : float):
        """
        Same as `set_a`.

        Returns
        -------

        """
        self._set_species(epsilon, sigma, m, "b")

    def calc_ab(self):
        epsilon_a = self.epsilon_a
        epsilon_b = self.epsilon_b
        sigma_a = self.sigma_a
        sigma_b = self.sigma_b

        rule = self.inter_species_rule
        sigma_ab = eval(rule["sigma"]) # on en a besoin pour le calcul d'epsilon_ab
        epsilon_ab = eval(rule["epsilon"])
        self._set_species(epsilon_ab, sigma_ab, 0, "ab")

        self.params["re"] = max(self.re_a, self.re_b)

        self._m()

    def set_ab(self, a : tuple, b : tuple):
        """
        Sets species a and b parameters, and calculates inter-species parameters.

        Parameters
        ----------
        a : tuple
            First species parameters, under the form :code:`(epsilon, sigma, mass)`
        b : tuple
            Second species parameters, under the same form.
        Returns
        -------

        """
        self.set_a(*a)
        self.set_b(*b)

        self.calc_ab()

    def set_n_a(self,n_a : int):
        self.x_a = n_a/self.npart

    def atom_grid(self, n_x : int, n_y : int, d : float):
        """
        Creates a grid containing :code:`n_x*n_y` atoms.

        Parameters
        ----------
        n_x : int
            number of columns
        n_y : int
            number of rows
        d : float
            inter-atomic distance

        Returns
        -------

        """
        self.params["npart"] = n_x*n_y
        self.params["n_a"] = int(self.x_a*self.npart)

        posx = np.concatenate([np.arange(0,n_x,1.0) for i in range(n_y)])*d
        posy = np.concatenate([i*np.ones(n_x) for i in range(n_y)])*d
        self.pos = np.transpose([posx, posy])

        self.v = np.zeros(self.pos.shape)

        self._m()

        self.x_lim_sup = (n_x - 0.5)*d
        self.y_lim_sup = (n_y - 0.5)*d
        self.x_lim_inf = -0.5*d
        self.y_lim_inf = -0.5*d

        self.set_dt()

    def set_x_lim_inf(self,x_lim_inf : float):
        self.params["x_lim_inf"] = x_lim_inf
        self.params["length_x"] = self.x_lim_sup - self.x_lim_inf

    def set_y_lim_inf(self,y_lim_inf : float):
        self.params["y_lim_inf"] = y_lim_inf
        self.params["length_y"] = self.y_lim_sup - self.y_lim_inf

    def get_lim_inf(self):
        return np.array([self.x_lim_inf, self.y_lim_inf])

    def get_lim_sup(self):
        return np.array([self.x_lim_sup, self.y_lim_sup])

    def set_x_lim_sup(self,x_lim_sup : float):
        self.params["x_lim_sup"] = x_lim_sup
        self.params["length_x"] = self.x_lim_sup - self.x_lim_inf

    def set_y_lim_sup(self,y_lim_sup : float):
        self.params["y_lim_sup"] = y_lim_sup
        self.params["length_y"] = self.y_lim_sup - self.y_lim_inf

    def set_length_x(self,length_x : float):
        self.x_lim_sup = self.x_lim_inf + length_x

    def set_length_y(self,length_y : float):
        self.y_lim_sup = self.y_lim_inf + length_y

    def get_length(self):
        return np.array([self.length_x, self.length_y])

    def shuffle_atoms(self): # mélange les atomes aléatoirement pour répartir les 2 espèces dans l'espace
        """
        Shuffle atoms' position in order to easily create a homogeneous repartition of the two species.
        Should be called just right after the positions are defined. Atoms' speed is not taken in account.

        Returns
        -------

        """
        np.random.shuffle(self.pos)

    def random_speed(self): # donne une vitesse aléatoire aux atomes pour une température non nulle
        """
        Gives a random speed to the atoms, following a normal law, in order to have a striclty positive temperature.

        Returns
        -------

        """
        self.v = np.random.normal(size=(self.npart,2))

    def _m(self): # vecteur de masses
        """
        Constructs `m`

        Returns
        -------
        m : np.array
        """
        m = np.concatenate((self.m_a*np.ones(self.n_a), self.m_b*np.ones(self.npart - self.n_a)))
        self.m = np.transpose([m,m])
        return self.m

    def get_EC(self): # énergie cinétique
        v = self.v
        m = self.m
        return 0.5*ne.evaluate("sum(m*v*v)")

    def get_T(self):
        return self.EC/(self.kB*self.npart)

    def set_T(self, T : float):
        if not self.T:
            self.random_speed()
        self.v *= np.sqrt(T/self.T)

    def get_mass(self):
        return self.n_a*self.m_a + (self.npart-self.n_a)*self.m_b

    def set_x_a(self,x_a : float):
        self.params["x_a"] = min(max(x_a,0.0),1.0)
        self.params["n_a"] = int(x_a*self.npart)
        self._m()

    def set_x_periodic(self, x : int = 1):
        self.params["x_periodic"] = x

    def set_y_periodic(self, y : int = 1):
        self.params["y_periodic"] = y

    def set_periodic_boundary(self, x : int = 1, y : int = 1): # conditions périodiques de bord : 1, sinon 0
        self.x_periodic = x
        self.y_periodic = y

    def set_dt(self, dt : int = None):
        if not dt: # période d'oscillation pour pouvoir calibrer le pas de temps
            freq0 = np.sqrt((57.1464 * self.epsilon_a / (self.sigma_a**2)) / self.m_a) / (2*np.pi)
            peri0 = 1 / freq0
            dt = peri0 / 75

        self.params["dt"] = abs(dt)