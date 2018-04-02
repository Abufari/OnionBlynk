import logging
import time

from Configurator import Configurator
from PinHandler import PinHandler
from TemperatureSensor import TemperatureSensor
from pid import PID


class Heater(object):
    def __init__(self, configs):
        self.output = 0
        self.cycleStartTime = time.time()
        self.cycleMilliseconds = 1000

        self.onTime = 0

        self.pinHandler = PinHandler(configs)

    def heaterHandler(self):
        self.pinHandler.setHeater(self.output)

    def update(self, output):
        self.output = min(output, 100)
        self.heaterHandler()


class RancilioSilvia:
    def __init__(self, configs: Configurator):
        self.input_value = 0
        self.configs = configs
        self.configs.functionList.append(self.update_configs)
        self.configs.functionList.append(self.update_pid_configs)
        self.heater = Heater(configs)
        self.pid = PID()
        self.update_pid_configs()
        self.isPoweredOn = False
        self.powerMode = self.configs.energy_mode.eco
        self.logger = logging.getLogger('__main__.' + __name__)

        # Temperature sensors
        self.boilerTempSensor = TemperatureSensor(
            sensorAddress='28-0000092c44f8',
            configs=self.configs)
        self.boilerTempSensor.setupSensor()

    def update(self):
        if self.isPoweredOn:
            output = self.pid.compute(self.input_value)
            self.configs.heater_output = output
            self.setHeaterOutput(output)
        else:
            self.setHeaterOutput(0)

    def setHeaterOutput(self, output: float):
        self.heater.output = output
        self.heater.heaterHandler()

    def update_pid_configs(self):
        # Power settings
        self.isPoweredOn = self.configs.RancilioPoweredOn
        self.powerMode = self.configs.RancilioPowerMode
        kp = self.configs.pid_configs[self.powerMode]['kp']
        ki = self.configs.pid_configs[self.powerMode]['ki']
        kd = self.configs.pid_configs[self.powerMode]['kd']
        self.pid.setTunings(kp, ki, kd)
        self.pid.desired_value = self.configs.pid_configs[
            self.powerMode]['setpoint']

    def read_temperature_sensors(self, whichSensor: str):
        if whichSensor == 'boiler':
            return self.boilerTempSensor.readTemperature()
        return None

    def update_configs(self):
        self.logger.debug('updating configs')
        self.isPoweredOn = self.configs.RancilioPoweredOn
        self.powerMode = self.configs.RancilioPowerMode
