# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR BSD-3-Clause

import sys
import json

from PySide6.QtWidgets import QWidget, QApplication, QGridLayout
from PySide6.QtCore import QRect, QTimer, Qt
from PySide6.QtGui import QPainter, QColor


class EllipseWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ellipse_rect = QRect(50, 50, 100, 100)
        self.ellipse_rect_bias = QRect(50, 50, 100, 100)
        self.color = QColor(255, 165, 0, 127)  # Initial color: orange
        self.color_bias = QColor(255, 165, 0, 127)

    def update_ellipse(self, rect, color, rect_bias, color_bias):
        self.ellipse_rect = rect
        self.color = color
        self.ellipse_rect_bias = rect_bias
        self.color_bias = color_bias
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setBrush(self.color)
        painter.drawEllipse(self.ellipse_rect)
        painter_bias = QPainter(self)
        painter_bias.setBrush(self.color_bias)
        painter_bias.drawEllipse(self.ellipse_rect_bias)

class Plot(QWidget):
    def __init__(self, number_of_sensors=0, parent=None):
        super().__init__(parent)

        if number_of_sensors not in (1, 2, 3, 4):
            raise ValueError("Number of sensors should be 1, 2, 3 or 4")
        self._number_of_sensors = number_of_sensors
        
        # screen position per plot-window (x, y, width, height)
        self.top_x = 20
        self.top_y = 20
        self.width = 480
        self.height = 480
        self._screen_positions = []
        self._screen_position = None
        self.gap_x = 80
        self.gap_y = 80

        # window title
        self.sensor_device_name = "Follow touch sensor"
        self.title_text = "%s: IR minus background"
        self.title_text_bias = "%s: IR and background"
        # show bias IR from background
        self.bias = True

        # settings per sensor
        self._setting = []
        self._setting.append({"color": QColor(0, 0, 255, 127), "color_bias": QColor(0, 2, 0, 127), "grid_position": [0 , 0]})
        self._setting.append({"color": QColor(0, 0, 255, 127), "color_bias": QColor(0, 2, 0, 127), "grid_position": [0 , 3]})
        self._setting.append({"color": QColor(0, 0, 255, 127), "color_bias": QColor(0, 2, 0, 127), "grid_position": [3 , 0]})
        self._setting.append({"color": QColor(0, 0, 255, 127), "color_bias": QColor(0, 2, 0, 127), "grid_position": [3 , 3]})
        self.initUI()

        # dummy
        self.counter = 0
        self.dummy_data_list = []

        # position of ellipses
        self.x = []
        self.y = []
        for i in range(0, self._number_of_sensors):
            self.x.append(0)
            self.y.append(0)
        self.x_bias = []
        self.y_bias = []
        for i in range(0, self._number_of_sensors):
            self.x_bias.append(0)
            self.y_bias.append(0)

        # factor to in- or decrease ellipses
        self.factor = 1

        # ble service_manager, so that instance can be called
        self.bleServiceManager = None

    def closeEvent(self, event):
        try:
            print("closing plot")
            self.bleServiceManager.stop_measurement()
            self.bleServiceManager.connection_dict.__setitem__(self.bleServiceManager.device_name, "PlotWindowClosed")
        except:
            pass

    def info(self, ble_service_manager=None):
        # info from bluetooth connection of peripheral: currenct connection state, 
        # name and mac address
        self.bleServiceManager = ble_service_manager

        self.sensor_device_name = self.bleServiceManager.device_name or self.sensor_device_name
        self.set_window_title()

        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint)


        self._screen_positions.append([self.top_x                          , self.top_y                           , self.width, self.height])
        self._screen_positions.append([self.top_x + self.width + self.gap_x, self.top_y                           , self.width, self.height])
        self._screen_positions.append([self.top_x                          , self.top_y + self.height + self.gap_y, self.width, self.height])
        self._screen_positions.append([self.top_x + self.width + self.gap_x, self.top_y + self.height + self.gap_y, self.width, self.height])
        try:
            self._screen_position = self._screen_positions[int(self.bleServiceManager.device_name[-1:])]   # last charachter
            self.setGeometry(self._screen_position[0], self._screen_position[1], self._screen_position[2], self._screen_position[3])
        except:
            self._screen_position = None

    def set_window_title(self):
        if self.bias == True:
            self.setWindowTitle(self.title_text_bias % self.sensor_device_name)
        else:
            self.setWindowTitle(self.title_text % self.sensor_device_name)


    def initUI(self):
        self.set_window_title()

        self.layout = QGridLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(0)

        if not self._screen_position:
            self.setGeometry(self.top_x, self.top_y, self.width, self.height)
        else:
            self.setGeometry(self._screen_position[0], self._screen_position[1], self._screen_position[2], self._screen_position[3])

        self.ellipse_widgets = []
        for i in range(0, self._number_of_sensors):
            self.ellipse_widgets.append(EllipseWidget())
            grid_position_x = self._setting[i].get("grid_position")[0]
            grid_position_y = self._setting[i].get("grid_position")[1]
            self.layout.addWidget(self.ellipse_widgets[i], grid_position_x, grid_position_y)

        self.setLayout(self.layout)


    def update_ellipse_from_external_source(self):
        # Receiving new values from an external source
        if len(self.dummy_data_list) > 0:
            try:
                self.draw(self.dummy_data_list[self.counter])
            except:
                sys.exit(2)
        for i in range(0, self._number_of_sensors):
            new_rect = QRect(self.ellipse_widgets[i].x() - int(self.x[i] / 2), self.ellipse_widgets[i].y()  - int(self.y[i] / 2), self.x[i], self.y[i])
            new_color = QColor(self._setting[i].get("color"))
            new_rect_bias = QRect(self.ellipse_widgets[i].x() - int(self.x_bias[i] / 2), self.ellipse_widgets[i].y()  - int(self.y_bias[i] / 2), self.x_bias[i], self.y_bias[i])
            new_color_bias = QColor(self._setting[i].get("color_bias"))
            self.ellipse_widgets[i].update_ellipse(new_rect, new_color, new_rect_bias, new_color_bias)

        if len(self.dummy_data_list) > 0:
            self.counter += 1

    def dummy_draw(self, list_of_data_lines):
        self.dummy_data_list = list_of_data_lines
        
    def draw(self, data):
        self._data_to_xy(data)
        if len(self.dummy_data_list) == 0:
            # not dummy, but real data
            self.update_ellipse_from_external_source()

    def _data_to_xy(self, data):
        try:
            _data = json.loads(data)
            timestamp_data = _data.get("t")
            timestamp = list(timestamp_data.keys())[0]
            sensor_data_list = timestamp_data.get(timestamp)
            index = 0
            sensor_list = []
            for sensor_data in sensor_data_list:
                # append a tuple and put some values in it
                sensor_list.append(())
                sensor_list[int(sensor_data.get("s"))] = (int(sensor_data.get("i")), int(sensor_data.get("b")))

                self.y[index] = sensor_list[index][0] - sensor_list[index][1]   # sensor index with values on-off in a tuple
                self.x[index] = sensor_list[index][0] - sensor_list[index][1]   # sensor index with values on-off in a tuple
                
                if self.bias:
                    self.y[index] = sensor_list[index][0]                       # sensor index with values on-off in a tuple
                    self.x[index] = sensor_list[index][0]                       # sensor index with values on-off in a tuple
                    self.y_bias[index] = sensor_list[index][1]                  # sensor index with values on-off in a tuple
                    self.x_bias[index] = sensor_list[index][1]                  # sensor index with values on-off in a tuple

                self.y[index] = int(self.factor * (self.y[index] * self.height / 4096))
                self.x[index] = int(self.factor * (self.x[index] * self.width / 4096))
                self.y_bias[index] = int(self.factor * (self.y_bias[index] * self.height / 4096))
                self.x_bias[index] = int(self.factor * (self.x_bias[index] * self.width / 4096))
                index += 1

            return True

        except Exception as e:
            if data and data == "":
                return False
            return None
        
    def mousePressEvent(self, event):
        # toggle
        self.bias = not self.bias
        self.set_window_title()



if __name__ == "__main__":
    
    data = '''{"follow_touch_1":[{"t":{"000106":[{"s":"0","i":"2202","b":"0195"},{"s":"1","i":"2342","b":"0435"},{"s":"2","i":"1365","b":"0247"},{"s":"3","i":"1483","b":"0295"}]}},
{"t":{"000205":[{"s":"0","i":"2202","b":"0279"},{"s":"1","i":"2373","b":"0549"},{"s":"2","i":"1361","b":"0303"},{"s":"3","i":"1471","b":"0386"}]}}]}
'''
    data = []
    data.append('''{"t":{"000106":[{"s":"0","i":"2202","b":"0195"},{"s":"1","i":"2342","b":"0435"},{"s":"2","i":"1365","b":"0247"},{"s":"3","i":"1483","b":"0295"}]}}''')
    data.append('''{"t":{"000205":[{"s":"0","i":"2212","b":"0279"},{"s":"1","i":"2333","b":"0549"},{"s":"2","i":"1361","b":"0303"},{"s":"3","i":"1471","b":"0386"}]}}''')
    data.append('''{"t":{"000305":[{"s":"0","i":"2222","b":"0279"},{"s":"1","i":"2353","b":"0549"},{"s":"2","i":"1371","b":"0303"},{"s":"3","i":"1421","b":"0386"}]}}''')
    data.append('''{"t":{"000405":[{"s":"0","i":"2232","b":"0279"},{"s":"1","i":"2323","b":"0549"},{"s":"2","i":"1391","b":"0303"},{"s":"3","i":"1751","b":"0386"}]}}''')
    data.append('''{"t":{"000505":[{"s":"0","i":"2242","b":"0279"},{"s":"1","i":"2313","b":"0549"},{"s":"2","i":"1331","b":"0303"},{"s":"3","i":"1471","b":"0386"}]}}''')
    data.append('''{"t":{"000605":[{"s":"0","i":"4252","b":"0549"},{"s":"1","i":"4252","b":"0549"},{"s":"2","i":"1341","b":"0303"},{"s":"3","i":"1491","b":"0386"}]}}''')
    data.append('''{"t":{"000705":[{"s":"0","i":"4262","b":"0549"},{"s":"1","i":"4262","b":"0549"},{"s":"2","i":"1371","b":"0303"},{"s":"3","i":"1471","b":"0386"}]}}''')
    data.append('''{"t":{"000805":[{"s":"0","i":"2272","b":"0279"},{"s":"1","i":"2353","b":"0549"},{"s":"2","i":"1321","b":"0303"},{"s":"3","i":"1461","b":"0386"}]}}''')
    data.append('''{"t":{"000905":[{"s":"0","i":"2282","b":"0279"},{"s":"1","i":"2343","b":"0549"},{"s":"2","i":"1311","b":"0303"},{"s":"3","i":"1431","b":"0386"}]}}''')
    data.append('''{"t":{"001005":[{"s":"0","i":"2292","b":"0279"},{"s":"1","i":"2333","b":"0549"},{"s":"2","i":"1361","b":"0303"},{"s":"3","i":"1421","b":"0386"}]}}''')
    data.append('''{"t":{"001105":[{"s":"0","i":"2342","b":"0279"},{"s":"1","i":"2383","b":"0549"},{"s":"2","i":"1371","b":"0303"},{"s":"3","i":"1411","b":"0386"}]}}''')
    data.append('''{"t":{"001205":[{"s":"0","i":"2322","b":"0279"},{"s":"1","i":"2363","b":"0549"},{"s":"2","i":"1381","b":"0303"},{"s":"3","i":"1431","b":"0386"}]}}''')

    app = QApplication(sys.argv)
    w = Plot(number_of_sensors=4)

    w.show()

    timer = QTimer(w)    

    w.dummy_draw(data)
    timer.timeout.connect(w.update_ellipse_from_external_source)
    timer.start(2000)

    sys.exit(app.exec())
    