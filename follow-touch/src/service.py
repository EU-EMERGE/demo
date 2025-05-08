import os

from PySide6.QtCore import (
    QByteArray,
    QUuid,
)
from PySide6.QtBluetooth import (
    QBluetoothUuid,
    QLowEnergyService,
    QLowEnergyController,
)

from .plot import Plot
from .json_to_xls import FollowTouchConversion


class BLEServiceManager:
    def __init__(self):
        self.ble_controller = None
        self.ble_service = None

        self.ble_follow_touch_service_uuid = None
        self.introducing_an_error = None
        self.follow_touch_command_characteristic_uuid = (
            "{b47b6628-5fc7-4140-86c1-45f9a9be9fbc}"
        )
        self.follow_touch_result_characteristic_uuid = (
            "{fda4cdfd-0575-4f78-86d1-7de26458e0cf}"
        )
        self.follow_touch_command_characteristic = None
        self.follow_touch_result_characteristic = None

        self.value_from_server = ""

        self.filehandler = None
        self.filename = None  # device dependend
        self.full_filename = None  # directory plus filename
        self.file_output = False  # flag

        self.connection_dict = None  # keeps track of ble connections

        self.plot = Plot(number_of_sensors=4)
        self.device_name = ""  # device name needed for the filename

    def remote_address(self):
        try:
            return self.ble_controller.remoteAddress()
        except:
            return None

    def do_service(self, device_info, connection_dict):
        if device_info.address().toString():
            self.device_name = device_info.name()
            self.connection_dict = connection_dict
            if not self.ble_controller:
                # Create controller
                self.ble_controller = QLowEnergyController.createCentral(device_info)
                # Define signals
                self.ble_controller.connected.connect(self.device_connected)
                self.ble_controller.connectionUpdated.connect(self.device_updated)
                self.ble_controller.disconnected.connect(self.device_disconnected)
                self.ble_controller.discoveryFinished.connect(
                    self.service_discovery_finished
                )
                self.ble_controller.errorOccurred.connect(self.controller_error)
                # signal mtuChanged()
                # signal rssiRead()
                self.ble_controller.serviceDiscovered.connect(self.service_discovered)
                self.ble_controller.stateChanged.connect(self.controller_status_change)

                # Connect to device
                self.ble_controller.connectToDevice()

                # give bluetooth device info to Plot instance to set window title and position
                self.plot.info(self)

                # make a file per device/instance
                self.filename = device_info.name()

    def close(self):
        self.plot.close()
        print("closing BLE servicemanager")
        try:
            self.ble_controller.disconnectFromDevice()
        except:
            pass

    # -- Controller signals start ---------------------------------------------------------------------------------------------------

    def device_connected(self):
        print("Device connected, discovering services...")
        self.ble_controller.discoverServices()

    def device_updated(self, parameters):
        print("Device have send an update", parameters)

    def device_disconnected(self):
        print("Device disconnected")
        if self.filehandler and self.filehandler.closed == False:
            self.filehandler.close()
        self.ble_controller = None

    def service_discovery_finished(self):
        print("Service discovery finished")
        for _char in self.ble_service.characteristics():
            self.ble_service.readCharacteristic(_char)
            # print(_char.uuid().toString())

    def descriptor_read(self, descriptor):
        print("descriptor read", descriptor)

    def descriptor_written(self, descriptor):
        print("descriptor written:", descriptor.name())

    def controller_error(self, error):
        print("controller error", self.ble_controller.errorString(), error, type(error))
        # if error == QLowEnergyController.InvalidBluetoothAdapterError:
        self.connection_dict.__setitem__(self.device_name, str(error))
        # self.close()

    def service_discovered(self, service_uuid):
        print(f"Service discovered: {service_uuid.toString()}")
        if service_uuid.toString().__contains__("00001849-0000-1000-8000-00805f9b34fb"):
            # !!! Only a pre-defined GATT Service works at expected !!! with self.ble_service.discoverDetails
            # !!! and using SkipValueDiscovery instead of FullDiscovery !!!
            self.ble_service = self.ble_controller.createServiceObject(
                QUuid(service_uuid.toString())
            )
            if self.ble_service:
                # Define signals
                self.ble_service.characteristicChanged.connect(
                    self.characteristic_changed
                )
                self.ble_service.characteristicRead.connect(self.characteristic_read)
                self.ble_service.characteristicWritten.connect(
                    self.characteristic_written
                )
                self.ble_service.descriptorRead.connect(self.descriptor_read)
                self.ble_service.descriptorWritten.connect(self.descriptor_written)
                self.ble_service.errorOccurred.connect(self.service_error)
                self.ble_service.stateChanged.connect(self.service_state_changed)

                # Discover details about the service
                self.ble_service.discoverDetails(
                    mode=QLowEnergyService.DiscoveryMode.SkipValueDiscovery
                )
                # self.ble_service.discoverDetails(mode=QLowEnergyService.DiscoveryMode.FullDiscovery)

    def controller_status_change(self, state):
        print("controller state:", state)
        # set controller state in connnection_dict so the calling method can check the connection
        try:
            self.connection_dict.__setitem__(self.device_name, str(state))
        except:
            pass

    # -- Controller signals end ---------------------------------------------------------------------------------------------------

    # -- Service signals start ---------------------------------------------------------------------------------------------------
    def service_state_changed(self, state):
        # Due to a bug in QBluetooth one MUST use a pre-defined service-uuid on the peripheral
        # set service state in connection_dict so the calling method can check the connection
        try:
            self.connection_dict.__setitem__(self.device_name, str(state))
        except:
            pass

        if state == QLowEnergyService.ServiceState.RemoteServiceDiscovering:
            print("Discovering ...")

        if state == QLowEnergyService.ServiceState.RemoteServiceDiscovered:
            for _characteristic in self.ble_service.characteristics():
                if (
                    _characteristic.uuid().toString()
                    == self.follow_touch_command_characteristic_uuid
                ):
                    self.follow_touch_command_characteristic = _characteristic
                elif (
                    _characteristic.uuid().toString()
                    == self.follow_touch_result_characteristic_uuid
                ):
                    self.follow_touch_result_characteristic = _characteristic

            # make sure notification is on for both used characteristics
            characteristic_command = self.ble_service.characteristic(
                QUuid(self.follow_touch_command_characteristic_uuid)
            )
            if characteristic_command.isValid():
                self.enable_notifications(characteristic_command)
            else:
                print("invalid")

            characteristic_result = self.ble_service.characteristic(
                QUuid(self.follow_touch_result_characteristic_uuid)
            )
            if characteristic_result.isValid():
                self.enable_notifications(characteristic_result)
            else:
                print("invalid")
            # notification is set

            # send 'standby' command
            try:
                self.ble_service.writeCharacteristic(
                    self.follow_touch_command_characteristic,
                    "standby".encode("utf8"),
                    mode=QLowEnergyService.WriteWithResponse,
                )
            except:
                pass

    def characteristic_read(self, info, value):
        print(f"Characteristic read {info.uuid().toString()} value: {value}")

    def characteristic_changed(self, info, value):
        # get results from peripheral through notifications
        try:
            if self.file_output == True:
                self.filehandler.write(value.data().decode("utf8"))
            self.plot.draw(
                value.data().decode("utf8")[:-2]
            )  # minus last 2 characters (,\n)
        except Exception as e:
            if not self.filehandler.closed:
                print("No filehandler available yet", e)

    def characteristic_written(self, info, value):
        print(f"Characteristic writtten {info.uuid().toString()} value: {value}")

    def service_error(self, error):
        print("Error in service_error:", error)

    # -- Service signals end ---------------------------------------------------------------------------------------------------

    def enable_notifications(self, characteristic):
        cccd = characteristic.descriptor(
            QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration
        )
        if cccd.isValid():
            self.ble_service.writeDescriptor(cccd, QByteArray.fromHex(b"0100"))

    def disable_notifications(self, characteristic):
        cccd = characteristic.descriptor(
            QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration
        )
        if cccd.isValid():
            self.ble_service.writeDescriptor(cccd, QByteArray.fromHex(b"0000"))

    # -- Act on user interface action -------------------------------------------------------------------------------------------
    def start_measurement(self, measurement_pace, file_output=False, filename=None):
        print("start command", measurement_pace)
        self.file_output = file_output

        if self.filename != None:  # got a name in do_service method
            # combine filename(=device name) with argument filename which contain directory and datetime
            if filename != None:
                dirname, basename = os.path.split(filename)
                self.full_filename = "%s%s%s" % (
                    dirname,
                    os.path.sep,
                    "%s_%s.json" % (self.filename, basename),
                )

        self.plot.show()
        if self.file_output == True:
            self.start_file()

        start_command = "start ms:%s" % measurement_pace
        self.ble_service.writeCharacteristic(
            self.follow_touch_command_characteristic,
            start_command.encode("utf8"),
            mode=QLowEnergyService.WriteWithResponse,
        )

    def stop_measurement(self):
        print("stop command")
        try:
            self.ble_service.writeCharacteristic(
                self.follow_touch_command_characteristic,
                "stop".encode("utf8"),
                mode=QLowEnergyService.WriteWithResponse,
            )
        except:
            pass
        if self.file_output == True:
            self.stop_file()
            try:
                follow_touch_conversion = FollowTouchConversion(
                    json_file=self.full_filename
                )
                follow_touch_conversion.convert()
            except:
                pass

    def start_file(self):
        self.filehandler = open(self.full_filename, "a+")
        start_json = (
            '{"%s":[' % self.filename
        )  # start of json file with basename of written file
        self.filehandler.write(start_json)

    def stop_file(self):
        try:
            # remove last characters (\n and comma)
            self.filehandler.seek(
                0, os.SEEK_END
            )  # seek to end of file; f.seek(0, 2) is legal
            self.filehandler.seek(
                self.filehandler.tell() - 2, os.SEEK_SET
            )  # go backwards 2 bytes
            self.filehandler.truncate()
        except Exception as e:
            pass
        finally:
            # Write the end of the JSON file
            end_json = "]}\n"  # end of json file
            if not self.filehandler.closed:
                self.filehandler.write(end_json)
                self.filehandler.close()
                # Reopen and clean trailing comma before closing JSON
        try:
            with open(self.full_filename, "rb+") as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                if file_size >= 3:
                    f.seek(file_size - 3)
                    last_bytes = f.read(3)
                    if last_bytes == b",]}":
                        f.seek(file_size - 3)
                        f.write(b"]}")
                        f.truncate()
        except Exception as e:
            print("Failed to clean up trailing comma in JSON file:", e)
