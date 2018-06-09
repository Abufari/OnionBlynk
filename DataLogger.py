import logging
import time
from itertools import cycle
from threading import Event
from typing import List

from Configurator import Configurator
from TemperatureSensor import TemperatureSensor


class DataLogger:
    """Class for aquiring sensor data and return a smoothed value"""
    _boilerTempSensors: List[TemperatureSensor]
    _steamTempSensors: List[TemperatureSensor]

    def __init__(self, stopEvent: Event, error_in_method_event: Event):
        self.boilerTemp = 21
        self.steamTemp = 21
        self._boilerTempSensors = []
        self._boilerTempSensorsIter = None
        self._steamTempSensors = []
        self.configs = Configurator.instance()
        self.configs.functionList.append(self.update_configs)
        self._smoothingFactor = self.configs.smoothingFactor
        self._stopEvent = stopEvent
        self._error_in_method_event = error_in_method_event

        self.lastValue = 23

        self.logger = logging.getLogger('__main__.' + __name__)

    def addTemperatureSensor(self, sensor_type='boiler',
                             sensoridentifier='28-0000092c44f8'):
        temperatureSensor = TemperatureSensor(sensorAddress=sensoridentifier)
        temperatureSensor.setupSensor()
        if sensor_type == 'boiler':
            self._boilerTempSensors.append(temperatureSensor)
            self._boilerTempSensorsIter = cycle(self._boilerTempSensors)
        elif sensor_type == 'steam':
            self._steamTempSensors.append(temperatureSensor)
        else:
            raise ValueError('sensor_type must be "boiler" or "steam"')

    def acquireData(self):
        while not self._stopEvent.is_set():
            raw_value = self._acquire_temperature_of_sensor(
                next(self._boilerTempSensorsIter))
            # smoothing values by applying Infinite Impulse Response Filter
            if raw_value is not None:
                new_value = (self.lastValue + raw_value) / 2
                self.lastValue = raw_value
                self.boilerTemp += (new_value - self.boilerTemp
                                    ) / self._smoothingFactor

            time.sleep(0.1)

    def _acquire_temperature_of_sensor(self, sensor: TemperatureSensor):
        tempSensor = sensor
        temperature = tempSensor.readTemperature()
        if temperature is not None:
            return temperature
        else:
            self.logger.warning("Couldn't read temperature sensor {}".
                                format(tempSensor.sensorAddress))
            self._error_in_method_event.set()
            # raw_value gets not influenced by unreadable sensor
            return None

    def update_configs(self):
        self._smoothingFactor = self.configs.smoothingFactor
