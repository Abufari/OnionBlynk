import logging
import time
from threading import Event

from Configurator import Configurator
from PinHandler import PinHandler
from pid import PID


class Heater(object):
    pinHandler: PinHandler

    def __init__(self):
        self.output = 0
        self.cycleStartTime = time.time()
        self.cycleMilliseconds = 1000

        self.onTime = 0

        self.configs = Configurator.instance()
        self.pinHandler = PinHandler.instance()

    def update(self, output):
        self.output = min(output, 100)
        self.heaterHandler()

    def heaterHandler(self):
        if self.configs.RancilioPoweredOn:
            self.pinHandler.setHeater(self.output)
        else:
            self.pinHandler.setHeater(0)


class RancilioSilvia:
    configs: Configurator

    def __init__(self, stopEvent: Event = None):
        self.input_value = 0
        self.configs = Configurator.instance()
        self.configs.functionList.append(self.update_configs)
        self.heater = Heater()
        self.pid = PID.instance()
        self.update_configs()
        self.isPoweredOn = False
        self.powerMode = self.configs.energy_mode.eco
        self.dataLogger = self.configs.dataLogger
        self._stopEvent = stopEvent
        self.logger = logging.getLogger('__main__.' + __name__)

    def update(self):
        temperature = self.dataLogger.boilerTemp
        output = self.pid.compute(temperature)

        setpoint = self.configs.pid_configs[
            self.configs.RancilioPowerMode]['setpoint']
        if abs(temperature - setpoint) < 1:
            self.configs.RancilioHeatedUp = True
        else:
            self.configs.RancilioHeatedUp = False

        if output is None:
            return

        if self.configs.RancilioPoweredOn:
            self.configs.heater_output = output
        else:
            self.configs.heater_output = 0
        self.setHeaterOutput(output)

    def setHeaterOutput(self, output: float):
        self.heater.update(output)

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
