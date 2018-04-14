import logging
import os

from Configurator import Configurator


class PinHandler(object):
    def __init__(self):
        self.configs = Configurator.instance()
        self.configs.functionList.append(self.update_configs)
        self.heatingElement = self.configs.heaterElementPin
        os.system('fast-gpio set-output {}'.format(
            self.heatingElement
            ))

        self.last_value = 0

        self.logger = logging.getLogger('__main__.' + __name__)

    def setHeater(self, value):
        value = round(value)
        if value == self.last_value:
            return
        self.last_value = value

        if value == 0:
            os.system('fast-gpio set {gpio} {value:d}'.format(
                gpio=self.heatingElement, value=value
                ))
        else:
            os.system('fast-gpio pwm {gpio} {freq} {duty_cycle:d}'.format(
                gpio=self.heatingElement, freq=1, duty_cycle=value
                ))

    def update_configs(self):
        self.heatingElement = self.configs.heaterElementPin
