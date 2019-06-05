import numpy as np
import numexpr as ne
from matplotlib.tri import TriAnalyzer, Triangulation, UniformTriRefiner
from scipy.spatial import Voronoi, ConvexHull

def PDF(pos, nb_samples, rcut, bin_count):
    """
    Pair Distribution Function. Returns normalized histogram of distance between atoms.

    Parameters
    ----------
    pos : np.array
        Array containing atoms position
    nb_samples : int
        Number of atoms from which to generate the histogram
    rcut : number
        Maximum distance to consider
    bin_count : int
        Number of bins of the histogram

    Returns
    -------
    bins, hist : tuple(np.array, np.array)
        `bins` being the distances, `hist` the normalized (regarding radius) histogram

    """
    bins = np.linspace(0, rcut, bin_count)
    samples = np.random.choice(range(len(pos)), nb_samples)
    hist = np.zeros(len(bins)-1)
    for s in samples:
        sample = pos[s,:]
        dists = np.array([a for a in np.sqrt(ne.evaluate("sum((pos-sample)**2,axis=1)")) if a])
        hist += np.histogram(dists, bins=bins, weights=1/dists)[0]
    return bins[:-1], hist/nb_samples


def density(model, refinement=0):
    """
    Create a Voronoi mesh and calculate the local density on its vertices.

    The local density is calculated as follows:
    for each vertex, compute the density of each neighbour region as
    the mass of the particle over the area and assign the average of
    the neighbouring density to the vertex.

    Parameters
    ----------
    model : simulation.builder.Model
        the Model object containing
    refinement : int (defaults : 0)
        number of subdivision for refining the mesh (0 == None)
    Returns
    -------
    tri : matplotlib.tri.Triangulation
        the triangulation mesh (refined if set as)
    vert_density : numpy.array
        the array containing the local denstity associated with the tri mesh

    Examples
    -----
    To plot the result using matplotlib use :
    .. code-block:: python
        import matplotlib.pyplot as plt
        tri, density = data_proc.density(model)
        plt.tricontour(tri, density) # to draw contours
        plt.tricontourf(tri, density) # ot draw filled contours
        plt.show()

    Note
    ----
    As of now, the numerical results may not be quantitatively accurate
    but should qualitatively represent the density.
    """
    vor = Voronoi(model.pos)
    vert_density = np.zeros(max(vor.vertices.shape)) # density vector
    reg_num = np.zeros(max(vor.vertices.shape)) # nbr of regions per vertex --> averaging
    for point_index, reg in enumerate(vor.point_region):
        vertices = vor.regions[reg]
        if vertices:
            if -1 not in vertices:
                area = ConvexHull(vor.vertices[vertices]).area # gets the area
                vert_density[vertices] += model.m[point_index, 0] / area # makes it a density (sort-of)
                reg_num[vertices] += 1
    vert_density /= reg_num # averaging

    # getting rid of really ugly border points
    new_vert, vert_density = (vor.vertices[vor.vertices[:, 0] >= np.min(model.pos[:, 0])],
                              vert_density[vor.vertices[:, 0] >= np.min(model.pos[:, 0])])

    new_vert, vert_density = (new_vert[new_vert[:, 0] <= np.max(model.pos[:, 0])],
                              vert_density[new_vert[:, 0] <= np.max(model.pos[:, 0])])

    new_vert, vert_density = (new_vert[new_vert[:, 1] >= np.min(model.pos[:, 1])],
                              vert_density[new_vert[:, 1] >= np.min(model.pos[:, 1])])

    new_vert, vert_density = (new_vert[new_vert[:, 1] <= np.max(model.pos[:, 1])],
                              vert_density[new_vert[:, 1] <= np.max(model.pos[:, 1])])

    # for triangulation refinement
    tri2 = Triangulation(*new_vert.T)
    if refinement:
        tri2.set_mask(TriAnalyzer(tri2).get_flat_tri_mask(0.1))
        refiner = UniformTriRefiner(tri2)
        print(len(tri2.neighbors), vert_density.shape)
        tri, vert_density = refiner.refine_field(vert_density, subdiv=refinement)
    else:
        tri, vert_density = tri2, vert_density

    return tri, vert_density
