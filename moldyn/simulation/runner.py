# Classe effectuant les simulations

from ..utils import gl_util
import moderngl
import numpy as np
import numexpr as ne

class Simulation:

    def __init__(self, model):

        self.model = model

        self.npart = np.shape(model.pos)[0]

        # Découpage de la liste en segments de taille acceptable par le GPU
        max_layout_size = gl_util.testMaxSizes()
        self.groups_number = int(np.ceil(self.npart / max_layout_size))
        self.layout_size = int(np.ceil(self.npart / self.groups_number))

        self.elements_number = np.array([self.layout_size] * self.groups_number)
        if self.npart % self.layout_size:
            self.elements_number[-1] = self.npart % self.layout_size

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
        self.BUFFER_P = self.context.buffer(reserve=2*4 * self.layout_size)
        self.BUFFER_P.bind_to_storage_buffer(0);

        # Buffer de forces
        self.BUFFER_F = self.context.buffer(reserve=2*4 * self.layout_size)
        self.BUFFER_F.bind_to_storage_buffer(1);

        # Buffer d'énergies potentielles
        self.BUFFER_E = self.context.buffer(reserve=4 * self.layout_size)
        self.BUFFER_E.bind_to_storage_buffer(2);

        # Buffer de compteurs de liaisons
        self.BUFFER_COUNT = self.context.buffer(reserve=4 * self.layout_size)
        self.BUFFER_COUNT.bind_to_storage_buffer(3);

        # Buffer de paramètres
        self.BUFFER_PARAMS = self.context.buffer(reserve=4 * 5)
        self.BUFFER_PARAMS.bind_to_storage_buffer(4)

    def iters(self,n):
        for i in range(n):
            self.iter()

    def iter(self):
        pass
