from . import data_proc as dp
import matplotlib.pyplot as plt
from functools import wraps
import matplotlib
matplotlib.use('Qt5Agg')
import numpy as np
import scipy as sp
from ..utils.data_mng import *


def _plot_base(*, show=True, axis='', grid=True, figure=None):
    """
    A wrapper designed to handle basic matplotlib configuration.

    Parameters
    ----------
    show : bool
        If True, will show the plot.
    axis : str
        Configure the plot axis ('equal, ...).
    grid : bool
        Activate the grid on True.
    figure : int
        Specify to which figure to plot. If not specified (ie. None),
        will use the last used figure.

    Returns
    -------
    The wrapped function taking the same arguments as the original.

    """
    def plot_dec(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            if figure is not None:
                plt.figure(figure)

            func(*args, **kwargs)

            if grid:
                plt.grid()
            plt.axis(axis)
            if show:
                plt.show()
        return wrap
    return plot_dec


@_plot_base(axis='equal')
def plot_T(simulation):
    plt.plot()


@_plot_base(axis='equal', grid=False)
def plot_density(model, levels=None, refinement=0):
    tri, density = dp.density(model, refinement)
    if type(levels) == int:
        levels = np.linspace(min(density), max(density), levels)
    plt.tricontour(tri, density, levels=levels)


@_plot_base(axis='equal', grid=False)
def plot_densityf(model, levels=None, refinement=0):
    tri, density = dp.density(model, refinement)
    if type(levels) == int:
        levels = np.linspace(min(density), max(density), levels)
    plt.tricontourf(tri, density, levels=levels)

