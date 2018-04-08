import logging
import time
from threading import Event
from typing import List

from Configurator import Configurator
from TemperatureSensor import TemperatureSensor


class DataLogger:
    """Class for aquiring sensor data and return a smoothed value"""
    _boilerTempSensors: List[TemperatureSensor]
    _steamTempSensors: List[TemperatureSensor]

    def __init__(self, configs: Configurator, boilerTemp: float,
                 steamTemp: float, stopEvent: Event,
                 error_in_method_event: Event):
        self.boilerTemp = boilerTemp
        self.steamTemp = steamTemp
        self._boilerTempSensors = []
        self._steamTempSensors = []
        self.configs = configs
        self.configs.functionList.append(self.update_configs)
        self._smoothingFactor = configs.smoothingFactor
        self._stopEvent = stopEvent
        self._error_in_method_event = error_in_method_event

        self.logger = logging.getLogger('__main__.' + __name__)

    def newTemperatureSensor(self, sensor_type='boiler',
                             sensoridentifier='28-0000092c44f8'):
        temperatureSensor = TemperatureSensor(
            sensorAddress=sensoridentifier,
            configs=self.configs)
        temperatureSensor.setupSensor()
        if sensor_type == 'boiler':
            self._boilerTempSensors.append(temperatureSensor)
        elif sensor_type == 'steam':
            self._steamTempSensors.append(temperatureSensor)
        else:
            raise ValueError('sensor_type must be "boiler" or "steam"')

    def acquireData(self):
        while not self._stopEvent.is_set():
            raw_value = self._acquire_temperature_of_sensor_list(
                self._boilerTempSensors)
            # smoothing values by applying Infinite Impulse Response Filter
            self.boilerTemp += (raw_value - self.boilerTemp
                                ) / self._smoothingFactor

            raw_value = self._acquire_temperature_of_sensor_list(
                self._steamTempSensors)
            self.steamTemp += (raw_value - self.steamTemp
                               ) / self._smoothingFactor
            time.sleep(0.1)

    def _acquire_temperature_of_sensor_list(self, sensor_type: list):
        raw_value = 0
        number_of_tempSensors = len(sensor_type)
        for i in range(number_of_tempSensors):
            tempSensor: TemperatureSensor = sensor_type[i]
            temperature = tempSensor.readTemperature()
            if temperature is not None:
                raw_value += temperature / number_of_tempSensors
            else:
                self.logger.warning("Couldn't read temperature sensor {}".
                                    format(tempSensor.sensorAddress))
                self._error_in_method_event.set()
                # raw_value gets not influenced by unreadable sensor
                raw_value += raw_value / number_of_tempSensors
                number_of_tempSensors -= 1
        return raw_value

    def update_configs(self):
        self._smoothingFactor = self.configs.smoothingFactor
