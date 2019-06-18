import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

class ModelView():
    def __init__(self, model):
        self.model = model

        plt.ioff()

        plt.pause(1e-6)

    def update(self):
        self.plot_a.set_data(*self.model.pos[:self.model.n_a,:].T)
        self.plot_b.set_data(*self.model.pos[self.model.n_a:,:].T)
        plt.pause(1e-6)

    def show(self):
        plt.clf()
        plt.axis("scaled")
        plt.ylim(self.model.y_lim_inf, self.model.y_lim_sup)
        plt.xlim(self.model.x_lim_inf, self.model.x_lim_sup)
        self.plot_a, = plt.plot(*self.model.pos[:self.model.n_a,:].T, "ro", markersize=1)
        self.plot_b, = plt.plot(*self.model.pos[self.model.n_a:,:].T, "bo", markersize=1)
        plt.pause(1e-3)
        #return self