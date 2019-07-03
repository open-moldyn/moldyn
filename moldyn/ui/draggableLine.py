import matplotlib
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (QDialog, QLineEdit, QApplication, QGridLayout,
                             QPushButton, QLabel)
from matplotlib.widgets import Button
import sys


class MultiInputDialog(QDialog):
    def __init__(self, labels, vals, format_dict, parent=None):
        super().__init__(parent)
        self.vals = list(vals)
        self.labels = []
        self.edits = []
        for key, value in zip(labels, vals):
            if key in format_dict:
                value = format_dict[key].format(value)
            else:
                value = str(value)
            self.labels.append(QLabel(key))
            edit = QLineEdit()
            edit.setText(value)
            self.edits.append(edit)
        
        self.accept_button = QPushButton("Accept")
        self.accept_button.clicked.connect(self.accept)
        # Create layout and add widgets

        layout = QGridLayout()
        for i, label, edit in zip(range(len(self.labels)), self.labels, self.edits):
            layout.addWidget(label, i, 0)
            layout.addWidget(edit, i, 1)
        layout.addWidget(self.accept_button, i+1, 1)

        # Set dialog layout

        self.setLayout(layout)

    def exec(self) -> int:
        self.show()
        self.edits[0].setFocus()
        return super().exec()

    def result(self):
        print("result", super().result())
        if super().result():
            for i, edit in enumerate(self.edits):
                self.vals[i] = edit.text()
        return self.vals


class DraggableLine:
    def __init__(self, x_data, y_data, picker, x_label, y_label, axis, y_min=None, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.y_min = y_min
        self.picker = picker
        self.fig = plt.figure()
        ax = self.fig.add_subplot(111)
        plt.subplots_adjust(bottom=0.2)
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid()
        self.x_label = x_label
        self.y_label = y_label
        ax.axis(axis)
        self.line, = ax.plot(x_data, y_data, *args, picker=picker, **kwargs)
        self.axnew = plt.axes([0.65, 0.02, 0.25, 0.05])
        self.bnew = Button(self.axnew, 'New point (ctrl)')
        self.axdel = plt.axes([0.39, 0.02, 0.25, 0.05])
        self.bdel = Button(self.axdel, 'Delete point (alt)')
        self.axsetaxis = plt.axes([0.13, 0.02, 0.25, 0.05])
        self.bsetaxis = Button(self.axsetaxis, 'Set axis')
        self.bnew.on_clicked(self.new)
        self.bdel.on_clicked(self.del_point)
        self.bsetaxis.on_clicked(self.set_axis)
        self.press = None
        self.obj = None
        self.init_connect()

    def _redraw(self, x_data, y_data):
        ax = self.line.axes
        axis = ax.axis()
        ax.cla()
        self.line, = ax.plot(x_data, y_data, *self.args, picker=self.picker, **self.kwargs)
        ax.axis(axis)
        ax.grid()
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)


    def connect(self):
        'connect to all the events we need'
        self.cidpress = self.line.figure.canvas.mpl_connect(
            'button_press_event', self.on_press)
        self.cidpick = self.line.figure.canvas.mpl_connect(
            'pick_event', self.on_pick)
        self.cidrelease = self.line.figure.canvas.mpl_connect(
            'button_release_event', self.on_release)
        self.cidmotion = self.line.figure.canvas.mpl_connect(
            'motion_notify_event', self.on_motion)

    def init_connect(self):
        self.new_pending = False
        self.new_key_press = False
        self.del_key_press = False
        self.del_pending = False
        self.cidaxes_enter = self.line.figure.canvas.mpl_connect(
            'axes_enter_event', self.on_enter)
        self.cidaxes_leave = self.line.figure.canvas.mpl_connect(
            'axes_leave_event', self.on_leave)
        self.cidkpress = self.line.figure.canvas.mpl_connect(
            'key_press_event', self.key_press)
        self.cidkrelease = self.line.figure.canvas.mpl_connect(
            'key_release_event', self.key_press)

    def key_press(self, event):
        if event.key == 'control':
            self.new_key_press = not self.new_key_press
            print("New point :", self.new_key_press)
        elif event.key ==  "alt":
            self.del_key_press = not self.del_key_press
            print("Del point :", self.del_key_press)

    def key_release(self, event):
        print('release', event.key)
        if event.key == 'control':
            self.new_key_press = False
        elif event.key ==  "alt":
            self.del_key_press = False

    def new(self, event):
        self.new_pending = not self.new_pending

    def del_point(self, event):
        self.del_pending = not self.del_pending
        
    def on_enter(self, event):
        self.connect()

    def on_leave(self, event):
        self.disconnect()
    
    def on_press(self, event):
        '''on button press we will see if the mouse is over us
            and store some data'''
        if event.inaxes != self.line.axes:
            print('!=axes')
            return

        # create new point
        if self.new_pending or self.new_key_press:
            #print("new point")
            x, y = event.xdata, event.ydata
            x_data = list(self.line.get_xdata())
            y_data = list(self.line.get_ydata())
            i = 0
            while i<len(x_data) and x > x_data[i]:
                i += 1
            x_data = x_data[:i] + [x] + x_data[i:]
            if self.y_min is None:
                y_data = y_data[:i] + [y] + y_data[i:]
            else:
                y_data = y_data[:i] + [max(y, self.y_min)] + y_data[i:]
            self._redraw(x_data, y_data)
            self.on_release(event)
            self.new_pending = False
            return            

        # double-click edit
        if event.dblclick and self.obj is not None:
            #print("double clique")
            x0, y0, ind = self.obj
            d = MultiInputDialog(('x', 'y'), (x0, y0), {'x': '{:.3e}', 'y': '{:.3e}'})
            d.exec()
            x, y = map(float, d.result())
            x_data = self.line.get_xdata()
            y_data = self.line.get_ydata()
            if self.y_min is None:
                x_data[ind], y_data[ind] = x, y
            else:
                x_data[ind], y_data[ind] = x, max(y, self.y_min)
            self.line.set_xdata(x_data)
            self.line.set_ydata(y_data)
            self.on_release(event)
            return
        self.press = event.xdata, event.ydata

    def on_pick(self, event):
        '''on button press we will see if the mouse is over us
            and store some data'''
        #if event.inaxes != self.rect.axes: return
        thisline = event.artist
        xdata = thisline.get_xdata()
        ydata = thisline.get_ydata()
        ind = event.ind
        points = tuple(zip(xdata[ind], ydata[ind]))
        #print('onpick points:', points)
        #print('event contains', ind)

        # delete points
        if self.del_key_press or self.del_pending:
            xdata = list(xdata)
            ydata = list(ydata)
            del xdata[ind[0]], ydata[ind[0]]
            self._redraw(xdata, ydata)
            self.on_release(event)
            self.del_pending = False
            return
        
        self.obj = *points[-1], ind

    def on_motion(self, event):
        '''on motion we will move the rect
            if the mouse is over us'''
        if self.press is None or self.obj is None: return
        if event.inaxes != self.line.axes:
            print('!=axes')
            return
        x0, y0, ind = self.obj
        xpress, ypress = self.press
        dx = event.xdata - xpress
        dy = event.ydata - ypress
        #print('x0=%f, xpress=%f, event.xdata=%f, dx=%f, x0+dx=%f' %
        #      (x0, xpress, event.xdata, dx, x0+dx))
        x_data = self.line.get_xdata()
        y_data = self.line.get_ydata()
        x_data[ind] = x0 + dx
        y_data[ind] = y0 + dy
        self.line.set_xdata(x_data)
        self.line.set_ydata(y_data)

        self.line.figure.canvas.draw()


    def on_release(self, event):
        '''on release we reset the press data'''
        self.press = None
        self.obj = None
        self.line.figure.canvas.draw()

    def set_axis(self, event):
        self.key_disconnect()
        ax = self.line.axes
        axis = ax.axis()
        d = MultiInputDialog(('x', "x'", 'y', "y'"), axis,
                             {'x':'{:.3e}', "x'":'{:.3e}', 'y':'{:.3e}', "y'":'{:.3e}'})
        d.exec()
        axis = list(map(float, d.result()))
        ax.axis(axis)
        self.init_connect()

    def key_disconnect(self):
        #print("disconnect")
        self.line.figure.canvas.mpl_disconnect(self.cidkpress)
        self.line.figure.canvas.mpl_disconnect(self.cidkrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidaxes_enter)
        self.line.figure.canvas.mpl_disconnect(self.cidaxes_leave)
        self.disconnect()


    def disconnect(self):
        '''disconnect all the stored connection ids'''
        self.line.figure.canvas.mpl_disconnect(self.cidpress)
        self.line.figure.canvas.mpl_disconnect(self.cidpick)
        self.line.figure.canvas.mpl_disconnect(self.cidrelease)
        self.line.figure.canvas.mpl_disconnect(self.cidmotion)


def main(queue):
    """


    The queue must contain a list containing the following elements in order:
        - axis : (tuple) a four element tuple defining the axis of the figure
        - x_data : (1d-array) the data for the x axis
        - y_data : (1d-array) the data for the y axis
        - xlabel : (str) the label for the x axis
        - ylabel : (str) the label for the y axis
    Parameters
    ----------
    queue

    Returns
    -------

    """
    #app = QApplication(sys.argv)
    axis, x_data, y_data, xlabel, ylabel, y_min = queue.get()
    dr = DraggableLine(x_data, y_data, 5, xlabel, ylabel, axis, y_min, 'o--', color='r')
    plt.show()
    queue.put(dr.line.get_data())


if __name__ == "__main__":
    main()
