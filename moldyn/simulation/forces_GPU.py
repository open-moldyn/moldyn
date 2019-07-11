# -*-encoding: utf-8 -*-

from ..utils import gl_util
import os
import moderngl
import numpy as np

if not gl_util.testGL():
    os.environ["MESA_GL_VERSION_OVERRIDE"] = "4.3"
    os.environ["MESA_GLSL_VERSION_OVERRIDE"] = "430"


class ForcesComputeGPU:
    """
    Compute module. Runs on GPU.


    Parameters
    ----------
    consts : dict
        Dictionary containing constants used for calculations.

    Attributes
    ----------
    npart : int
        Number of atoms.
    consts : dict
        Dictionary containing constants used for calculations, and some parameters to run the compute shader.

    """

    def __init__(self, consts, compute_npart=None):

        self.npart = consts["NPART"]
        self.compute_npart = compute_npart or consts["NPART"]

        max_layout_size = 256  # Probablement optimal (en tout cas d'après essais et guides de bonnes pratiques)
        self.groups_number = int(np.ceil(self.compute_npart / max_layout_size))
        self.layout_size = int(np.ceil(self.compute_npart / self.groups_number))

        consts["LAYOUT_SIZE"] = self.layout_size

        self.compute_npart = min(self.compute_npart, self.npart)
        self.compute_offset = 0

        self.context = moderngl.create_standalone_context(require=430)
        self.compute_shader = self.context.compute_shader(gl_util.source(os.path.dirname(__file__)+'/templates/moldyn.glsl', consts))


        self.consts = consts

        # Buffer de positions 1
        self._BUFFER_P = self.context.buffer(reserve=2 * 4 * self.npart)
        self._BUFFER_P.bind_to_storage_buffer(0)

        # Buffer de forces
        self._BUFFER_F = self.context.buffer(reserve=2 * 4 * self.npart)
        self._BUFFER_F.bind_to_storage_buffer(1)

        # Buffer d'énergies potentielles
        self._BUFFER_E = self.context.buffer(reserve=4 * self.npart)
        self._BUFFER_E.bind_to_storage_buffer(2)

        # Buffer de compteurs de liaisons
        self._BUFFER_COUNT = self.context.buffer(reserve=4 * self.npart)
        self._BUFFER_COUNT.bind_to_storage_buffer(3)

        # Buffer de paramètres, inutilisé pour l'instant
        self._BUFFER_PARAMS = self.context.buffer(reserve=4 * 5)
        self._BUFFER_PARAMS.bind_to_storage_buffer(4)

        self.array_shape = (self.npart, 2)

    def set_pos(self, pos):
        """
        Set position array and start computing forces.

        Parameters
        ----------
        pos : np.ndarray
            Array of positions.

        Returns
        -------

        """
        self._BUFFER_P.write(pos.astype('f4').tobytes())
        self.compute_shader.run(group_x=self.groups_number)

    def get_F(self):
        """

        Returns
        -------
        np.ndarray
            Computed inter-atomic forces.
        """
        return np.frombuffer(self._BUFFER_F.read(), dtype=np.float32).reshape(self.array_shape)

    def get_PE(self):
        """

        Returns
        -------
        np.ndarray
            Computed potential energy.
        """
        return np.frombuffer(self._BUFFER_E.read(), dtype=np.float32)

    def get_COUNT(self):
        """

        Returns
        -------
        np.ndarray
            Near atoms (one could count this as bonds).
        """
        return np.frombuffer(self._BUFFER_COUNT.read(), dtype=np.float32)