# -*-encoding: utf-8 -*-
"""
Strain calculator.
Runs on CPU.
"""
import weakref
from pprint import pprint

from numpy.linalg import inv

"""
installer icc-rt et tbb sur les machines à processeur intel
"""

import numpy as np
import numba
import threading
import multiprocessing as mp
import ctypes



@numba.njit(nogil=True, cache=True)
def _iterate(current_pos, x, pos, posdt, NPART, rcut, LENGTH_X, LENGTH_Y, SHIFT_X, SHIFT_Y, X_PERIODIC, Y_PERIODIC):
    X = np.zeros((2,2))
    Y = np.zeros((2,2))
    eps = np.zeros((2,2))
    for n in range(NPART):
        if x==n:
            continue
        distxy = current_pos - pos[n, :]

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
                distxydt = posdt[x] - posdt[n]
                if X_PERIODIC:
                    if distxydt[0] < (-SHIFT_X):
                        distxydt[0] += LENGTH_X
                    if distxydt[0] > SHIFT_X:
                        distxydt[0] -= LENGTH_X

                if Y_PERIODIC:
                    if distxydt[1] < (-SHIFT_Y):
                        distxydt[1] += LENGTH_Y
                    if distxydt[1] > SHIFT_Y:
                        distxydt[1] -= LENGTH_Y

                for i in range(2):
                    for j in range(2):
                        X[j,i] += distxy[i]*distxydt[j]
                        Y[j,i] += distxydt[i]*distxydt[j]

    eps[:] = X*inv(Y) - np.eye(2)
    return eps


def _par_iterate(current_pos, i, RCUT, NPART, LENGTH_X, LENGTH_Y, X_PERIODIC, Y_PERIODIC, SHIFT_X, SHIFT_Y):
    #ret = np.zeros((2,2))
    pos = np.array(_pos_array).reshape(NPART,2)
    posdt = np.array(_posdt_array).reshape(NPART,2)
    #ret += _iterate(current_pos, i, pos, posdt, NPART, RCUT, LENGTH_X, LENGTH_Y, SHIFT_X, SHIFT_Y, X_PERIODIC,
    #                Y_PERIODIC)
    return _iterate(current_pos, i, pos, posdt, NPART, RCUT, LENGTH_X, LENGTH_Y, SHIFT_X, SHIFT_Y, X_PERIODIC,
                    Y_PERIODIC)
    #return ret


def _p_compute_strain(pool, _pos, _posdt, eps_arr, RCUT, NPART, LENGTH_X, LENGTH_Y, X_PERIODIC, Y_PERIODIC, SHIFT_X, SHIFT_Y,
                      offset, end):

    pos = np.array(_pos).reshape(NPART,2)

    gen = ((pos[i,:], i, RCUT, NPART, LENGTH_X, LENGTH_Y, X_PERIODIC, Y_PERIODIC, SHIFT_X, SHIFT_Y)
           for i in range(offset, end))

    sortie = np.array(pool.starmap(_par_iterate, gen))

    eps_arr[:] = sortie[:]

_pos_array = None
_posdt_array = None


def initProcess(array1, array2):
    global _pos_array, _posdt_array
    _pos_array = array1
    _posdt_array = array2

class StrainComputeCPU:

    def __init__(self, consts, compute_npart=None, compute_offset=0):

        self.consts = dict()
        for key, item in consts.items():
            self.consts[key.upper()] = item

        self.compute_offset = max(0, compute_offset)

        self.npart = self.consts["NPART"]
        self.compute_npart = compute_npart or (self.consts["NPART"] - self.compute_offset)

        self.compute_npart = min(self.compute_npart, self.npart)

        self._EPS = np.zeros((self.npart, 2, 2), dtype=np.float32)

        self._thr_run = False

        self._POS = mp.Array(ctypes.c_float, self.npart * 2, lock=False)
        self._POSDT = mp.Array(ctypes.c_float, self.npart * 2, lock=False)
        self._pool = mp.Pool(mp.cpu_count(), initializer=initProcess, initargs=(self._POS, self._POSDT))

    def __del__(self):
        self._pool.close() # pour ne pas garder des processus ouverts pour rien

    def _compute_strain(self):
        RCUT = self.consts["RCUT"]
        NPART = self.consts["NPART"]
        LENGTH_X = self.consts["LENGTH_X"]
        LENGTH_Y = self.consts["LENGTH_Y"]
        X_PERIODIC = self.consts["X_PERIODIC"]
        Y_PERIODIC = self.consts["Y_PERIODIC"]

        SHIFT_X = LENGTH_X / 2
        SHIFT_Y = LENGTH_Y / 2
        end = NPART
        _p_compute_strain(self._pool, self._POS, self._POSDT, self._EPS, RCUT, NPART, LENGTH_X, LENGTH_Y, X_PERIODIC,
                          Y_PERIODIC, SHIFT_X, SHIFT_Y, self.compute_offset, end)

    def _join_thr(self):
        if self._thr_run:
            self._thread.join()
            self._thr_run = False

    def set_post(self, pos):
        self._POS[:] = pos.reshape((self.npart * 2,))

    def set_posdt(self, pos):
        self._POSDT[:] = pos.reshape((self.npart * 2,))

    def get_eps(self):
        self._join_thr()
        return self._EPS[:]

    def compute(self):
        self._thr_run = True
        self._thread = threading.Thread(target=self._compute_strain)
        self._thread.start()