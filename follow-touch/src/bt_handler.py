from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication


class ObservableDict(QObject):
    """
    This observable keeps track of changes in bluetooth connections, services and other
    events that influences the behaviour of the class instances
    """

    valueChanged = Signal(
        str, object
    )  # Signal that will be emitted when a value changes

    def __init__(self, initial_data=None):
        super().__init__()
        self._data = initial_data if initial_data is not None else {}

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        if key in self._data and self._data[key] != value:
            self._data[key] = value
            self.valueChanged.emit(key, value)
        elif key not in self._data:
            self._data[key] = value
            self.valueChanged.emit(key, value)


class DictionaryObserver(QObject):
    @Slot(str, object)
    def on_value_changed(self, key, value):
        print(f"Value for key '{key}' has changed to {value}")


if __name__ == "__main__":
    app = QApplication([])

    my_dict = ObservableDict({"key1": "value1"})
    observer = DictionaryObserver()

    # Connect the signal to the slot
    my_dict.valueChanged.connect(observer.on_value_changed)

    # Change a value to trigger the signal
    my_dict["key1"] = "new_value"
    my_dict["key2"] = "value2"

    app.exec()
