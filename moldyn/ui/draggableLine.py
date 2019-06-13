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
    def __init__(self, line):
        self.line = line
        self.press = None
        self.obj = None
        

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
        #sys.stdout.flush()
        if event.key == 'control':
            self.new_key_press = not self.new_key_press
            print("New point :", self.new_key_press)
        elif event.key ==  "alt":
            self.del_key_press = not self.del_key_press
            print("Del point :", self.del_key_press)

    def key_release(self, event):
        print('release', event.key)
        #sys.stdout.flush()
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
            print("new point")
            x, y = event.xdata, event.ydata
            x_data = list(self.line.get_xdata())
            y_data = list(self.line.get_ydata())
            i = 0
            while i<len(x_data) and x > x_data[i]:
                i += 1
            x_data = x_data[:i] + [x] + x_data[i:]
            y_data = y_data[:i] + [max(y, 0)] + y_data[i:]
            ax = self.line.axes
            axis = ax.axis()
            ax.cla()
            line, = ax.plot(x_data, y_data, 'o--', color='r', picker=5)
            ax.axis(axis)
            ax.grid()
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Temperature (K)')
            self.__init__(line)
            self.on_release(event)
            self.new_pending = False
            return            

        # double-click edit
        if event.dblclick and self.obj is not None:
            print("double clique")
            x0, y0, ind = self.obj
            d = MultiInputDialog(('x', 'y'), (x0, y0), {'x': '{:.3e}', 'y': '{:.3e}'})
            d.exec()
            x, y = map(float, d.result())
            x_data = self.line.get_xdata()
            y_data = self.line.get_ydata()
            x_data[ind], y_data[ind] = x, max(y, 0)
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
        print('onpick points:', points)
##        print('event contains', ind)

        # delete points
        if self.del_key_press or self.del_pending:
            xdata = list(xdata)
            ydata = list(ydata)
            del xdata[ind[0]], ydata[ind[0]]
            ax = self.line.axes
            axis = ax.axis()
            ax.cla()
            line, = ax.plot(xdata, ydata, 'o--', color='r', picker=5)
            ax.axis(axis)
            ax.grid()
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Temperature (K)')
            self.__init__(line)
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
        print("disconnect")
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
    #app = QApplication(sys.argv)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.subplots_adjust(bottom=0.2)
    plt.grid()
    plt.xlabel('Time (s)')
    plt.ylabel('Temperature (K)')
    t, T = queue.get()
    plt.axis([0, t, 0, T])
    line, = ax.plot([],[], 'o--', color='r', picker=5)
    axnew = plt.axes([0.65, 0.02, 0.25, 0.05])
    bnew = Button(axnew, 'New point (ctrl)')
    axdel = plt.axes([0.39, 0.02, 0.25, 0.05])
    bdel = Button(axdel, 'Delete point (alt)')
    axsetaxis = plt.axes([0.13, 0.02, 0.25, 0.05])
    bsetaxis = Button(axsetaxis, 'Set axis')
    dr = DraggableLine(line)
    bnew.on_clicked(dr.new)
    bdel.on_clicked(dr.del_point)
    bsetaxis.on_clicked(dr.set_axis)
    dr.init_connect()
    plt.show()
    queue.put(dr.line.get_data())


if __name__ == "__main__":
    main()
