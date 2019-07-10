# -*-encoding: utf-8 -*-
import io
import os

from PIL import Image
from imageio_ffmpeg import write_frames

from moldyn.processing.data_proc import compute_strain
from . import data_proc as dp
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from functools import wraps
import matplotlib
try:
    matplotlib.use('Qt5Agg')
except:
    pass
import numpy as np


def _plot_base(*, show=False, axis='', grid=False, figure=None):
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
            keys = kwargs.keys()
            if 'figure' in keys:
                if isinstance(kwargs['figure'], plt.Figure):
                    num = kwargs['figure'].number
                else:
                    num = kwargs['figure']
                plt.figure(num)
                del kwargs['figure']
            elif figure is not None:
                plt.figure(figure)

            if 'grid' in keys and kwargs['grid']:
                plt.grid()
                del kwargs['grid']
            elif grid:
                plt.grid()

            func(*args, **kwargs)

            plt.axis(axis)
            if show:
                plt.show()
        return wrap
    return plot_dec



@_plot_base(axis='scaled', grid=False)
def plot_density(model, levels=None, refinement=0):
    """
    Compute and plot the contours of the local density of model.

    Parameters
    ----------
    model : Model
        The model to plot
    levels : int or array-like
        the number of levels or a sorted array-like object of levels
    refinement : int
        the level of refinement
    Returns
    -------

    """
    tri, density = dp.density(model, refinement)
    fig = plt.gcf()
    if type(levels) == int:
        levels = np.linspace(min(density), max(density), levels)
    CS = plt.tricontour(tri, density, levels=levels)
    cbar = fig.colorbar()
    cbar.add_lines(CS)
    cbar.ax.set_ylabel('local density')


@_plot_base(axis='scaled', grid=False)
def plot_densityf(model, levels=None, refinement=0):
    """
    Compute and plot the filled contours of the local density of model.

    Parameters
    ----------
    model : Model
        The model to plot
    levels : int or array-like
        the number of levels or a sorted array-like object of levels
    refinement : int
        the level of refinement
    Returns
    -------

    """
    tri, density = dp.density(model, refinement)
    fig = plt.gcf()
    cmap = plt.get_cmap("viridis")
    if type(levels) == int:
        levels = np.linspace(min(density), max(density), levels)
    CS = plt.tricontourf(tri, density, levels=levels, cmap=cmap)
    cbar = fig.colorbar(CS)
    cbar.ax.set_ylabel('local density')

@_plot_base(axis='scaled', grid=False)
def plot_particles(model):
    """
    Plot the position stored in model.

    Parameters
    ----------
    model : Model
        The model to plot
    """
    line1, = plt.plot(*model.pos[:model.n_a, :].T, 'ro', markersize=0.5)
    line2, = plt.plot(*model.pos[model.n_a:, :].T, 'bo', markersize=0.5)

@_plot_base(axis='scaled', grid=False)
def plot_density_surf(model,refinement=0):
    """
    Compute and plot the 3D surface of the local density of model.

    Parameters
    ----------
    model : Model
        The model to plot.
    refinement : int
        the level of refinement
    Returns
    -------

    """
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    tri, density = dp.density(model, refinement)
    ax.plot_trisurf(tri, density)



def make_movie(simulation, dynstate, name: str, pfilm=5, fps=24, callback=None):
    """
    Makes a .mp4 movie of simulation from the history saved in dynstate.

    Parameters
    ----------
    simulation : Simulation
        The simulation object
    dynstate : DynState
        The dynState object containing the position history file.
    name : str
        The path (and name) of the file to be writen.
    pfilm : int
        To make the movie, takes every pfilm position.
    fps : int
        The number of frame per seconds of the film.
    callback : function
        An optional callback function that is called every time a
        frame is made and is passed the current iteration number.

    Returns
    -------

    """
    # ouverture pour la lecture
    npas = simulation.current_iter
    YlimB = simulation.model.y_lim_inf
    YlimH = simulation.model.y_lim_sup
    XlimG = simulation.model.x_lim_inf
    XlimD = simulation.model.x_lim_sup
    if not name.endswith(".mp4"):
        name += ".mp4"
    with dynstate.open(dynstate.POS_H, 'r') as fix:
        # liste de k ou tracer le graph
        klist = set(range(0, npas, pfilm))
        # boucle pour creer le film
        figure_size = (1920, 1088)
        try:
            os.remove(name)
        except FileNotFoundError:
            pass
        gen = write_frames(name, figure_size, fps=fps, quality=9)
        gen.send(None)
        fig = plt.figure(figsize=(figure_size[0] / (72 * 2), figure_size[1] / (72 * 2)))
        plt.clf()
        # definition du domaine de dessin
        plt.ioff()  # pour ne pas afficher les graphs)
        plt.axis('scaled')
        plt.ylim(YlimB, YlimH)
        plt.xlim(XlimG, XlimD)
        pos = fix.load()
        line1, = plt.plot(*pos[:simulation.model.n_a,:].T, 'ro', markersize=0.5)
        line2, = plt.plot(*pos[simulation.model.n_a:,:].T, 'bo', markersize=0.5)
        plt.xlabel("0")
        temp = io.BytesIO()
        for k in range(1, npas):
            # dessin a chaque pas (ne s'ouvre pas: est sauvegarde de maniere incrementale)
            if k in klist:
                temp.seek(0)
                plt.xlabel("Iteration : {}".format(k))
                plt.title(f"T = {simulation.state_fct['T'][k]:.2f} K")
                line1.set_data(*pos[:simulation.model.n_a,:].T)
                line2.set_data(*pos[simulation.model.n_a:,:].T)
                fig.savefig(temp, format='raw', dpi=72 * 2)  # sauvegarde incrementale
                temp.seek(0)
                if callback: callback(k)
                gen.send(Image.frombytes('RGBA', figure_size, temp.read()).convert('RGB').tobytes())
            pos = fix.load() # on charge a chaque pas de temps
        gen.close()
        plt.close(fig)


@_plot_base(axis='scaled', grid=False)
def deformation_volume(model0, model1, rcut, levels=50):
    eps = compute_strain(model0, model1, rcut)
    fig = plt.gcf()
    cmap = plt.get_cmap("plasma")
    dV = eps.trace(axis1=1, axis2=2)
    if type(levels) == int:
        levels = np.linspace(min(dV), max(dV)+1e-30, levels)
    CS = plt.tricontourf(*model1.pos.T, dV, levels=levels, cmap=cmap)
    cbar = fig.colorbar(CS)
    cbar.ax.set_ylabel('local compression')

@_plot_base(axis='scaled', grid=False)
def deformation_dev(model0, model1, rcut, levels=50):
    eps = compute_strain(model0, model1, rcut)
    fig = plt.gcf()
    cmap = plt.get_cmap("plasma")
    dV = eps[:,0,1]
    if type(levels) == int:
        levels = np.linspace(min(dV), max(dV)+1e-30, levels)
    CS = plt.tricontourf(*model1.pos.T, dV, levels=levels, cmap=cmap)
    cbar = fig.colorbar(CS)
    cbar.ax.set_ylabel('local shear')
