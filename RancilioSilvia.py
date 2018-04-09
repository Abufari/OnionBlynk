import logging
import time
from threading import Event

from Configurator import Configurator
from DataLogger import DataLogger
from PinHandler import PinHandler
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
    def __init__(self, configs: Configurator, dataLogger: DataLogger,
                 stopEvent: Event = None):
        self.input_value = 0
        self.configs = configs
        self.configs.functionList.append(self.update_configs)
        self.heater = Heater(configs)
        self.pid = PID()
        self.update_configs()
        self.isPoweredOn = False
        self.powerMode = self.configs.energy_mode.eco
        self.dataLogger = dataLogger
        self._stopEvent = stopEvent
        self.logger = logging.getLogger('__main__.' + __name__)

    def update(self):
        if self.isPoweredOn:
            temperature = self.dataLogger.boilerTemp
            output = self.pid.compute(temperature)
            if output is None:
                return
        else:
            output = 0
        self.configs.heater_output = output
        self.setHeaterOutput(output)

    def setHeaterOutput(self, output: float):
        self.heater.output = output
        self.heater.heaterHandler()

    def update_configs(self):
        # Power settings
        self.isPoweredOn = self.configs.RancilioPoweredOn
        self.powerMode = self.configs.RancilioPowerMode

        # PID settings
        kp = self.configs.pid_configs[self.powerMode]['kp']
        ki = self.configs.pid_configs[self.powerMode]['ki']
        kd = self.configs.pid_configs[self.powerMode]['kd']
        self.pid.setTunings(kp, ki, kd)
        self.pid.desired_value = self.configs.pid_configs[
            self.powerMode]['setpoint']
