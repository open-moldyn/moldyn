import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
from ..utils.data_mng import *
from functools import wraps

def _plot_base(show=True, axis='', grid=True, figure=None):
    def plot_dec(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            if figure:
                plt.figure(figure)
            else:
                plt.figure()
            func(*args, **kwargs)
            if grid : plt.grid()
            plt.axis(axis)
        return wrap
    return plot_dec

@_plot_base(axis='equal')
def plot_T(simulation):
    plt.plot()