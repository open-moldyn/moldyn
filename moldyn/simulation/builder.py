# Modèles à simuler

import numpy as np
import numexpr as ne

class Model:

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

        self.interspecies_rule = self.kong

        self.params = {
            "npart":npart,
            "x_a":x_a,
            "n_a":int(x_a*npart),
        }

    def __getattr__(self, item):
        derived_values=[
            "T",
            "EC"
        ]
        if item in derived_values:
            return eval("self.get_"+item+"()")
        elif item in self.params:
            return self.params[item]
        else:
            raise AttributeError

    def set_species(self, epsilon, sigma, m, sp):
        self.params["epsilon_"+sp] = epsilon
        self.params["sigma_"+sp] = sigma
        self.params["re_"+sp] = 2.0**(1.0/6.0)*sigma
        self.params["m_"+sp] = m

    def set_a(self, epsilon, sigma, m):
        self.set_species(epsilon, sigma, m, "a")

    def set_b(self, epsilon, sigma, m):
        self.set_species(epsilon, sigma, m, "b")

    def calc_ab(self):
        epsilon_a = self.epsilon_a
        epsilon_b = self.epsilon_b
        sigma_a = self.sigma_a
        sigma_b = self.sigma_b

        rule = self.interspecies_rule
        sigma_ab = eval(rule["sigma"]) # on en a besoin pour le calcul d'epsilon_ab
        epsilon_ab = eval(rule["epsilon"])
        self.set_species(epsilon_ab, sigma_ab, 0, "ab")

        self.params["re"] = max(self.re_a, self.re_b)
        self.params["rcut"] = 2.0*self.re

        self._m()

    def set_ab(self, a, b):
        self.set_a(*a)
        self.set_b(*b)

        self.calc_ab()

    def atom_grid(self, n_x, n_y, d):
        self.params["npart"] = n_x*n_y
        self.params["n_a"] = int(self.x_a*self.npart)

        posx = np.concatenate([np.arange(0,n_x,1.0) for i in range(n_y)])*d
        posy = np.concatenate([i*np.ones(n_x) for i in range(n_y)])*d
        self.pos = np.transpose([posx, posy])

        self.v = np.zeros(self.pos.shape)

        self._m()

        self.params["x_lim_sup"] = (n_x - 0.5)*d
        self.params["y_lim_sup"] = (n_y - 0.5)*d
        self.params["x_lim_inf"] = -0.5*d
        self.params["y_lim_inf"] = -0.5*d

        self.params["length_x"] = self.x_lim_sup - self.x_lim_inf
        self.params["length_y"] = self.y_lim_sup - self.y_lim_inf

    def shuffle_atoms(self): # mélange les atomes aléatoirement pour répartir les 2 espèces dans l'espace
        np.random.shuffle(self.pos)

    def random_speed(self): # donne une vitesse aléatoire aux atomes pour une température non nulle
        self.v = np.random.normal(size=(self.npart,2))

    def _m(self): # vecteur de masses
        m = np.concatenate((self.m_a*np.ones(self.n_a), self.m_b*np.ones(self.npart - self.n_a)))
        self.m = np.transpose([m,m])
        return self.m

    def get_EC(self): # énergie cinétique
        v = self.v
        m = self.m
        return 0.5*ne.evaluate("sum(m*v**2)")

    def get_T(self):
        return self.EC/(self.kB*self.npart)

    def set_T(self, T):
        if not self.T:
            self.random_speed()
        self.v *= np.sqrt(T/self.T)

    def set_periodic_boundary(self,x=1,y=1): # conditions périodiques de bord : 1, sinon 0
        self.params["x_periodic"] = x
        self.params["y_periodic"] = y

    def set_timestep(self, dt=None):
        if not dt: # période d'oscillation pour pouvoir calibrer le pas de temps
            freq0 = np.sqrt((57.1464 * self.epsilon_a / (self.sigma_a**2)) / self.m_a) / (2*np.pi)
            peri0 = 1 / freq0
            dt = peri0 / 75

        self.params["timestep"] = abs(dt)