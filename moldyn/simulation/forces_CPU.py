# -*-encoding: utf-8 -*-
"""

"""
"""
installer icc-rt et tbb sur les machines à processeur intel
"""

import numpy as np
import numba
import threading
import multiprocessing as mp
import ctypes


@numba.njit(nogil=True)
def force(dist, epsilon, p):
    return (-4.0 * epsilon * (6.0 * p - 12.0 * p * p)) / (dist * dist)


@numba.njit(nogil=True)
def energy(dist, epsilon, p):
    return epsilon * (4.0 * (p * p - p) + 127.0 / 4096.0)


@numba.njit(nogil=True, cache=True)
def _iterate(current_pos, i, pos, a, b, epsilon, sigma, rcut, X_PERIODIC, Y_PERIODIC, SHIFT_X, SHIFT_Y, LENGTH_X, LENGTH_Y):
    f = np.zeros((2,))
    e = 0.0
    m = 0.0
    for j in range(a, b):
        if i==j:
            continue
        distxy = current_pos - pos[j, :]

        if X_PERIODIC:
            if distxy[0] < (-SHIFT_X):
                distxy[0] += LENGTH_X
            if distxy[0] > SHIFT_X:
                distxy[0] -= LENGTH_X

        if Y_PERIODIC:
            if distxy[1] < (-SHIFT_Y):
                distxy[1] += LENGTH_Y
            if distxy[1] > SHIFT_Y:
                distxy[1] -= LENGTH_Y

        if np.abs(distxy[0])<rcut and np.abs(distxy[1])<rcut:
            dist = np.sqrt(np.sum(distxy ** 2))

            if dist < rcut:
                p = (sigma / dist) ** 6
                f += force(dist, epsilon, p)*distxy
                e += energy(dist, epsilon, p)
                m += 1.0
    return np.array((f[0], f[1], e, m))


def _par_iterate(current_pos, i, EPSILON_A, EPSILON_B, EPSILON_AB, SIGMA_A, SIGMA_B, SIGMA_AB, RCUT_A, RCUT_B,
                 RCUT_AB, N_A, NPART, LENGTH_X, LENGTH_Y, X_PERIODIC, Y_PERIODIC, SHIFT_X, SHIFT_Y):
    ret = np.zeros((4,))
    pos = np.array(_pos_array).reshape(NPART,2)
    if i < N_A:
        ret += _iterate(current_pos, i, pos, 0, N_A, EPSILON_A, SIGMA_A, RCUT_A, X_PERIODIC,
                           Y_PERIODIC, SHIFT_X, SHIFT_Y, LENGTH_X, LENGTH_Y)
        ret += _iterate(current_pos, i, pos, N_A, NPART, EPSILON_AB, SIGMA_AB, RCUT_AB,
                           X_PERIODIC, Y_PERIODIC, SHIFT_X, SHIFT_Y, LENGTH_X, LENGTH_Y)
    else:
        ret += _iterate(current_pos, i, pos, 0, N_A, EPSILON_AB, SIGMA_AB, RCUT_AB, X_PERIODIC,
                           Y_PERIODIC, SHIFT_X, SHIFT_Y, LENGTH_X, LENGTH_Y)
        ret += _iterate(current_pos, i, pos, N_A, NPART, EPSILON_B, SIGMA_B, RCUT_B, X_PERIODIC,
                           Y_PERIODIC, SHIFT_X, SHIFT_Y, LENGTH_X, LENGTH_Y)
    return ret


def _p_compute_forces(
        pool,
        _array,
        F,
        PE,
        counts,
        EPSILON_A,
        EPSILON_B,
        EPSILON_AB,
        SIGMA_A,
        SIGMA_B,
        SIGMA_AB,
        RCUT_A,
        RCUT_B,
        RCUT_AB,
        N_A,
        NPART,
        LENGTH_X,
        LENGTH_Y,
        X_PERIODIC,
        Y_PERIODIC,
        SHIFT_X,
        SHIFT_Y,
        offset,
        end):
    pos = np.array(_array).reshape(NPART,2)

    gen = ((pos[i,:], i, EPSILON_A,EPSILON_B,EPSILON_AB,SIGMA_A,SIGMA_B,SIGMA_AB,RCUT_A,RCUT_B,
            RCUT_AB,N_A,NPART,LENGTH_X,LENGTH_Y,X_PERIODIC,Y_PERIODIC, SHIFT_X, SHIFT_Y) for i in range(offset, end))

    sortie = np.array(pool.starmap(_par_iterate, gen))

    F[:,:] = sortie[:,:2]
    PE[:] = sortie[:,2]
    counts[:] = sortie[:,3]

_pos_array = None

def initProcess(array):
    global _pos_array
    _pos_array = array

class ForcesComputeCPU:
    """
    Compute module.
    Runs on CPU.
    Uses `numba` for JIT compilation and `multiprocessing` for multicore.
    See `ForcesComputeGPU` for documentation.
    """

    def __init__(self, consts, compute_npart=None, compute_offset=0):

        self.consts = consts

        self.compute_offset = max(0, compute_offset)

        self.npart = consts["NPART"]
        self.compute_npart = compute_npart or (consts["NPART"] - self.compute_offset)

        self.compute_npart = min(self.compute_npart, self.npart)

        self.array_shape = (self.npart, 2)
        self._F = np.zeros(self.array_shape, dtype=np.float32)
        self._PE = np.zeros((self.npart,), dtype=np.float32)
        self._COUNT = np.zeros((self.npart,), dtype=np.float32)

        self._thr_run = False

        self._POS = mp.Array(ctypes.c_float, self.npart * 2, lock=False)
        self._pool = mp.Pool(mp.cpu_count(), initializer=initProcess, initargs=(self._POS,))

    def __del__(self):
        self._pool.close() # pour ne pas garder des processus ouverts pour rien

    def _compute_forces(self):
        EPSILON_A = self.consts["EPSILON_A"]
        EPSILON_B = self.consts["EPSILON_B"]
        EPSILON_AB = self.consts["EPSILON_AB"]
        SIGMA_A = self.consts["SIGMA_A"]
        SIGMA_B = self.consts["SIGMA_B"]
        SIGMA_AB = self.consts["SIGMA_AB"]
        RCUT_A = self.consts["RCUT_A"]
        RCUT_B = self.consts["RCUT_B"]
        RCUT_AB = self.consts["RCUT_AB"]
        N_A = self.consts["N_A"]
        NPART = self.consts["NPART"]
        LENGTH_X = self.consts["LENGTH_X"]
        LENGTH_Y = self.consts["LENGTH_Y"]
        X_PERIODIC = self.consts["X_PERIODIC"]
        Y_PERIODIC = self.consts["Y_PERIODIC"]

        SHIFT_X = LENGTH_X / 2
        SHIFT_Y = LENGTH_Y / 2
        end = NPART
        _p_compute_forces(
            self._pool,
            self._POS,
            self._F,
            self._PE,
            self._COUNT,
            EPSILON_A,
            EPSILON_B,
            EPSILON_AB,
            SIGMA_A,
            SIGMA_B,
            SIGMA_AB,
            RCUT_A,
            RCUT_B,
            RCUT_AB,
            N_A,
            NPART,
            LENGTH_X,
            LENGTH_Y,
            X_PERIODIC,
            Y_PERIODIC,
            SHIFT_X,
            SHIFT_Y,
            self.compute_offset,
            end)

    def _join_thr(self):
        if self._thr_run:
            self._thread.join()
            self._thr_run = False

    def set_pos(self, pos):
        self._POS[:] = pos.reshape((self.npart * 2,))
        self._thr_run = True
        self._thread = threading.Thread(target=self._compute_forces)
        self._thread.start()

    def get_F(self):
        self._join_thr()
        return self._F[:,:]

    def get_PE(self):
        self._join_thr()
        return self._PE[:]

    def get_COUNT(self):
        self._join_thr()
        return self._COUNT[:]