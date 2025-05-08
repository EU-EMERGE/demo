import sys
import signal
import os
import platform
from functools import partial
from datetime import datetime
from pathlib import Path
from src.service import BLEServiceManager

from PySide6.QtCore import (QStringListModel,
                            QDir,
                            QItemSelectionModel,
                            Qt
                            )
from PySide6.QtBluetooth import (QBluetoothDeviceDiscoveryAgent, 
                                 QBluetoothDeviceInfo,
                                 QBluetoothAddress,
                                 QBluetoothLocalDevice,
                                 )

from PySide6.QtWidgets import (QApplication, 
                               QWidget, 
                               QVBoxLayout, 
                               QHBoxLayout,
                               QPushButton, 
                               QListWidget,
                               QMessageBox,
                               QLabel,
                               QInputDialog,
                               QLineEdit,
                               QCheckBox,
                               QListWidgetItem,
                               QFileDialog
                               )

from PySide6.QtGui import (QColor,
                           )

from src.detect_dict_change import DictionaryObserver, ObservableDict

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    sys.stderr.write('\r')
    sys.stdout.write("stopping\n")
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)


class FollowTouch(QWidget):
    def __init__(self):
        super().__init__()

        (self.width, self.height) = app.screens()[0].size().toTuple()

        self.localDevice = QBluetoothLocalDevice()
        self.localDevice.setHostMode(QBluetoothLocalDevice.HostDiscoverable)
        self.bluetooth_available = False

        if self.localDevice.address().toString() == "00:00:00:00:00:00":
            self.no_bluetooth()
        else:
            self.bluetooth_available = True

            self.initUI()
            self.discoveryAgent = QBluetoothDeviceDiscoveryAgent()

            self.discoveryAgent.deviceDiscovered.connect(self.deviceDiscovered)
            self.discoveryAgent.finished.connect(self.scanFinished)

            self.bleServiceManagers = {}      # Dictionary of bleSerivManagers
            self.selected_device_info = None  # QBluetoothDeviceInfo object

            self.measurement_pace = "100"
            self.file_timestamp = ""
            self.file_output = False
            self.connection_dict = ObservableDict({})
            self.observer = DictionaryObserver()
            # Connect the signal to the slot
            self.connection_dict.valueChanged.connect(self.bt_connection_changed)         # keeps track if a BLE connection is active or not

            self.set_file_output()
            self.startScan()

    def no_bluetooth(self):
        checkBluetooth = QMessageBox()
        checkBluetooth.warning(self, 'Bluetooth failure', f'Bluetooth is off\n\nTurn it on in Settings\nand start again', buttons=QMessageBox.Close)
        self.close()
    
    def initUI(self):
        self.setWindowTitle('Bluetooth Touch sensors')
        self.setGeometry(self.width - 800, 300, 400, 300)

        self.layout = QVBoxLayout()
        self.scanLayout = QHBoxLayout()
        self.measurementDirectoryLayout = QHBoxLayout()
        self.measurementFileLayout = QHBoxLayout()
        self.measurementSampleLayout = QHBoxLayout()
        self.measurementButtonsLayout = QHBoxLayout()

        self.helpButton = QPushButton(self)
        self.helpButton.clicked.connect(self.help)
        self.helpButton.setText("Help")

        self.filterLabel = QLabel(self)
        self.filterLabel.setText("Filter on:")
        self.scanFilter = QLineEdit(self)
        self.scanFilter.setPlaceholderText("Filter")
        self.scanFilter.setText("touch")
        self.scanFilter.setEnabled(False)
        self.scanFilter.textChanged.connect(self.scan_filter)

        self.scanButton = QPushButton('Refresh scan', self)
        self.scanButton.clicked.connect(self.startScan)
        self.scanButton.setEnabled(False)

        self.scanLayout.addWidget(self.scanButton)
        self.scanLayout.addWidget(self.filterLabel)
        self.scanLayout.addWidget(self.scanFilter)

        self.deviceList = QListWidget(self)
        self.deviceList.setStyleSheet("""QListWidget::item {padding-left:5px;}""")
        self.deviceList.itemSelectionChanged.connect(self.item_style)

        #'''
        self.dirButton = QPushButton("Directory")
        self.dirButton.clicked.connect(self.get_directory)


        out_path = Path(Path.home(), "follow_touch_output")
        if out_path.exists() == False:
            out_path.mkdir(parents=True)

        absolutePath = str(out_path) #QDir.currentPath()
        self.directoryPath = QLabel(self)
        self.directoryPath.setText(absolutePath)
        self.directoryPath.setWordWrap(False)

        self.measurementDirectoryLayout.addWidget(self.dirButton)
        self.measurementDirectoryLayout.addWidget(self.directoryPath)
        #'''

        self.fileOutputcheckbox = QCheckBox("Write output to file", self)
        self.fileOutputcheckbox.stateChanged.connect(self.set_file_output)

        self.fileLabel = QLabel(self)
        self.fileLabel.setText("Filename:")

        # get current date and time
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
         # convert datetime obj to string
        self.file_timestamp = str(current_datetime)        
        self.fileNameContent = QLabel(self)
        self.fileNameContent.setText("%s_%s.json" % ("follow_touch_[0-3]", self.file_timestamp))

        self.measurementFileLayout.addWidget(self.fileLabel)
        self.measurementFileLayout.addWidget(self.fileNameContent)


        self.sampleRateButton = QPushButton("Sample rate (ms)", self)
        self.sampleRate = QLineEdit(self)
        self.sampleRate.setText(str(100))
        self.sampleRate.setDisabled(True)
        self.sampleRateButton.setDisabled(True)
        self.sampleRateButton.clicked.connect(self.getTextInputDialog)    

        self.measurementSampleLayout.addWidget(self.sampleRateButton)
        self.measurementSampleLayout.addWidget(self.sampleRate)

        self.startMeasurementButton = QPushButton('Start measurement', self)
        self.startMeasurementButton.setDisabled(True)
        self.startMeasurementButton.clicked.connect(self.start_measurement)

        self.stopMeasurementButton = QPushButton('Stop measurement', self)
        self.stopMeasurementButton.setDisabled(True)
        self.stopMeasurementButton.clicked.connect(self.stop_measurement)

        self.measurementButtonsLayout.addLayout(self.measurementSampleLayout)
        self.measurementButtonsLayout.addWidget(self.startMeasurementButton)
        self.measurementButtonsLayout.addWidget(self.stopMeasurementButton)

        self.layout.addWidget(self.helpButton)
        self.layout.addLayout(self.scanLayout)
        self.layout.addWidget(self.deviceList)
        self.layout.addWidget(self.fileOutputcheckbox)
        self.layout.addLayout(self.measurementFileLayout)
        self.layout.addLayout(self.measurementDirectoryLayout)
        self.layout.addLayout(self.measurementButtonsLayout)

        self.setLayout(self.layout)

    def bt_connection_changed(self, key, value):
        '''
        PySide6.QtBluetooth.QLowEnergyController.ControllerState.ConnectingState
        PySide6.QtBluetooth.QLowEnergyController.ControllerState.ConnectedState
        PySide6.QtBluetooth.QLowEnergyController.ControllerState.DiscoveringState
        PySide6.QtBluetooth.QLowEnergyController.ControllerState.DiscoveredState
        PySide6.QtBluetooth.QLowEnergyController.ControllerState.ClosingState
        PySide6.QtBluetooth.QLowEnergyController.ControllerState.UnconnectedState
        
        PySide6.QtBluetooth.QLowEnergyService.ServiceState.RemoteServiceDiscovering
        PySide6.QtBluetooth.QLowEnergyService.ServiceState.RemoteServiceDiscovered
        PySide6.QtBluetooth.QLowEnergyService.ServiceState.InvalidService

        and from Plot:
            PlotWindowClosed
        '''
        state_green = ["DiscoveredState", "RemoteServiceDiscovered"]
        state_orange = ["ConnectingState", "ConnectedState", "DiscoveringState", "RemoteServiceDiscovering"]
        state_red = ["ClosingState", "UnconnectedState", "InvalidService", "PlotWindowClosed"]
        state_error = ["InvalidBluetoothAdapterError"]
        item =  self.deviceList.currentItem()
        checkBox = self.deviceList.itemWidget(self.deviceList.currentItem())

        items = self.deviceList.findItems("*", Qt.MatchWildcard)
        for item in items:
            checkBox = self.deviceList.itemWidget(item)

            if key == checkBox.text():
                if value.split(".")[-1] in state_green:
                    item.setBackground(QColor(0,255,0))
                    self.sampleRateButton.setEnabled(True)
                    self.startMeasurementButton.setEnabled(True)
                    #self.stopMeasurementButton.setEnabled(True)
                    checkBox.setChecked(True)
                    
                elif value.split(".")[-1] in state_orange:
                    item.setBackground(QColor(255, 165, 0))
                    checkBox.setChecked(True)

                elif value.split(".")[-1] in state_red:
                    item.setBackground(QColor(255,0,0))
                    checkBox.setChecked(False)
                
                elif value.split(".")[-1] in state_error:
                    self.no_bluetooth()

        show_buttons_flag = False
        for item_key in self.connection_dict._data.keys():
            if self.connection_dict.__getitem__(item_key).split(".")[-1] in state_green:
                show_buttons_flag = True

        if show_buttons_flag == False:
            self.sampleRateButton.setDisabled(True)
            self.startMeasurementButton.setDisabled(True)
            self.stopMeasurementButton.setDisabled(True)

    def item_style(self):
        # clear default selection color
        self.deviceList.setCurrentRow(self.deviceList.currentRow(), QItemSelectionModel.Clear)

    def set_file_output(self):
        if self.fileOutputcheckbox.isChecked():
            current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
            # convert datetime obj to string
            self.file_timestamp = str(current_datetime)    
            self.fileNameContent.setText("%s_%s.json" % ("follow_touch_[0-3]", self.file_timestamp))
            self.file_output = True
            self.dirButton.setEnabled(True)
        else:
            self.file_output = False
            self.dirButton.setDisabled(True)

    def get_directory(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        self.directory = QStringListModel()
            
        if dialog.exec():
            self.directory = dialog.directory()
            self.directoryPath.setText(self.directory.absolutePath())

    def has_bluetooth(self):
        return self.bluetooth_available
    
    #-- User Interface signals start -------------------------------------------------------------------
    def closeEvent(self, event):
        try:
            for device_name in list(self.bleServiceManagers.keys()):
                self.bleServiceManagers.get(device_name).close()
                self.bleServiceManagers.pop(device_name, None)
            print("closing bluetooth service manager")
        except:
            pass
        print("closing follow touch central")
 
    def startScan(self):
        self.scanFilter.setEnabled(False)
        self.scanButton.setEnabled(False)
        self.deviceList.clear()
        self.discoveryAgent.start()

    def deviceDiscovered(self, device):
        # filtered devices which are showed
        if device.name().__contains__(self.scanFilter.text()):
            # Create a QCheckBox
            checkbox = QCheckBox(f"{device.name()}", self)

            # Create a QListWidgetItem
            item = QListWidgetItem(self.deviceList)
            # Set the QListWidgetItem size hint to accommodate the checkbox
            item.setSizeHint(checkbox.sizeHint())
            item.setBackground(QColor(255,255,255))

            self.deviceList.setItemWidget(item, checkbox)

            enable_slot = partial(self.enable_device, device, item)
            disable_slot = partial(self.disable_device, device, item)
            checkbox.stateChanged.connect(lambda x: enable_slot() if x else disable_slot())

    def getTextInputDialog(self):
        text, okPressed = QInputDialog.getInt(None, 
                                              "Get values in ms ",
                                              "Sample every:", 
                                              100,
                                              55,
                                              1000)   
        if okPressed: 
            self.sampleRate.setText(str(text))
            self.measurement_pace = str(text)     

    #-- User Interface signals end -------------------------------------------------------------------

    def scan_filter(self):
        self.deviceList.clear()
    
    def enable_device(self, device, item):
        item.setBackground(QColor(255,255,255))

        # workaround platform depending uncategorizedDevice
        uncategorizedDevice = None
        if platform.system() in ("Windows"):
            uncategorizedDevice = QBluetoothDeviceInfo.UncategorizedDevice.value
        else:  # only tested for platform.system() in ('Linux'):
            uncategorizedDevice = QBluetoothDeviceInfo.UncategorizedDevice
        self.selected_device_info = QBluetoothDeviceInfo(QBluetoothAddress(device.address()), device.name(), uncategorizedDevice)
        self.localDevice.requestPairing(QBluetoothAddress(device.address()), QBluetoothLocalDevice.AuthorizedPaired)
        QMessageBox.information(self, 'Pairing', f'Pairing initiated to connect to {device.name()}\n\nYou have about 30 seconds to allow pairing\nusing the Bluetooth settings')
        self.connect_to_service(self.selected_device_info)

    def disable_device(self, device, item):
        item.setBackground(QColor(255,255,255))
        bleServiceManager = self.bleServiceManagers.get(device.name())
        bleServiceManager.close()
        self.bleServiceManagers.pop(device.name(), None)

    def help(self):
        QMessageBox.information(None, 'Help', \
                                'Bluetooth is used to make a connection from this Central device with Peripheral devices. \
                                \nTurn Bluetooth on and when asked, allow pairing. \
                                \nWhile scanning is busy, some buttons are greyed-out. \
                                \nThis takes about 30 seconds. \
                                \n \
                                \nDevices will give a value every 100 milliseconds, \
                                \nyou can set this from 55 to 1000 milliseconds \
                                \n \
                                \nResults of an experiment can be written as files to a \
                                \ndirectory of your choice. \
                                \nPer device in JSON format and all together in a XLS file. \
                                \nAll files have a timestamp in their name. \
                                \n \
                                \nAbbreviations used in the JSON files are: \
                                \nt: timestamp \
                                \ns: sensor, \
                                \ni: infrared LED on \
                                \nb: background, IR LED off \
                                \n \
                                \nIf something unexpected happen just restart everything')

    def scanFinished(self):
        self.scanFilter.setEnabled(True)
        self.scanButton.setEnabled(True)
        #QMessageBox.information(self, 'Scan Finished', 'Device scan finished.')

    def start_measurement(self):
        self.startMeasurementButton.setDisabled(True)
        self.stopMeasurementButton.setEnabled(True)

        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        # convert datetime obj to string
        self.file_timestamp = str(current_datetime)    
        self.fileNameContent.setText("%s_%s.json" % ("follow_touch_[0-3]", self.file_timestamp))

        filename = os.path.sep.join((self.directoryPath.text(), self.file_timestamp))
        for bleServiceManager in self.bleServiceManagers.values():
            bleServiceManager.start_measurement(self.measurement_pace, self.file_output, filename)

    def stop_measurement(self):
        self.stopMeasurementButton.setDisabled(True)
        self.startMeasurementButton.setEnabled(True)

        for bleServiceManager in self.bleServiceManagers.values():
            bleServiceManager.stop_measurement()
 
    def connect_to_service(self, device_info):
        # for each device a BLEServiceManager instance and a filehandler
        _bleServiceManager = BLEServiceManager()
        self.bleServiceManagers[device_info.name()] = _bleServiceManager
        self.connection_dict.__setitem__(device_info.name(), str(False))        # default set to "False"
        _bleServiceManager.do_service(device_info, self.connection_dict)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    follow_touch_central = FollowTouch()
    if follow_touch_central.has_bluetooth():
        follow_touch_central.show()
        sys.exit(app.exec())

