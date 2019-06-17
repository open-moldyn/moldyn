import io
from PIL import Image
from imageio_ffmpeg import write_frames
from . import data_proc as dp
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from functools import wraps
import matplotlib
matplotlib.use('Qt5Agg')
import numpy as np
import scipy as sp


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



@_plot_base(axis='equal', grid=False)
def plot_density(model, levels=None, refinement=0):
    tri, density = dp.density(model, refinement)
    fig = plt.gcf()
    if type(levels) == int:
        levels = np.linspace(min(density), max(density), levels)
    CS = plt.tricontour(tri, density, levels=levels)
    cbar = fig.colorbar()
    cbar.add_lines(CS)
    cbar.ax.set_ylabel('local density')


@_plot_base(axis='equal', grid=False)
def plot_densityf(model, levels=None, refinement=0):
    tri, density = dp.density(model, refinement)
    fig = plt.gcf()
    if type(levels) == int:
        levels = np.linspace(min(density), max(density), levels)
    CS = plt.tricontourf(tri, density, levels=levels)
    cbar = fig.colorbar(CS)
    cbar.ax.set_ylabel('local density')

@_plot_base(axis='equal', grid=False)
def plot_density_surf(model,refinement=0):
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    tri, density = dp.density(model, refinement)
    ax.plot_trisurf(tri, density)

def make_movie(simulation, ds, name:str, pfilm=5, fps=24, callback=None):
    # ouverture pour la lecture
    imgs = []
    npas = simulation.current_iter
    YlimB = simulation.model.y_lim_inf
    YlimH = simulation.model.y_lim_sup
    XlimG = simulation.model.x_lim_inf
    XlimD = simulation.model.x_lim_sup
    if not name.endswith(".mp4"):
        name += "+mp4"
    with ds.open(ds.POS_H, 'r') as fix:
        # liste de k ou tracer le graph
        klist = range(0, npas, pfilm)
        # boucle pour creer le film
        figure_size = (1920, 1088)
        gen = write_frames(name, figure_size, fps=fps, quality=9)
        gen.send(None)
        for k in range(npas):
            pos = np.load(fix) # on charge a chaque pas de temps
            # dessin a chaque pas (ne s'ouvre pas: est sauvegarde de maniere incrementale)
            if k in klist:
                plt.figure(0, figsize=(figure_size[0] / (72 * 2), figure_size[1] / (72 * 2)))
                # definition du domaine de dessin
                plt.ioff()  # pour ne pas afficher les graphs)
                plt.ylim(YlimB, YlimH)
                plt.xlim(XlimG, XlimD)
                plt.xlabel(k)
                plt.plot(*pos[:simulation.model.n_a,:].T, 'ro', markersize=0.5)
                plt.plot(*pos[simulation.model.n_a:,:].T, 'bo', markersize=0.5)
                temp = io.BytesIO()
                plt.savefig(temp, format='raw', dpi=72 * 2)  # sauvegarde incrementale
                plt.clf()
                temp.seek(0)
                # imgs.append(Image.frombytes('RGBA', figure_size, temp.read()).convert('RGB'))
                if callback: callback(k)
                gen.send(Image.frombytes('RGBA', figure_size, temp.read()).convert('RGB').tobytes())
        # imageio.mimwrite(f"./debug.gif", imgs, "GIF", duration=0.05,subrectangles=True)
        gen.close()