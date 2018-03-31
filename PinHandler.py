import os

from Configurator import Configurator


class PinHandler(object):
    def __init__(self, configs: Configurator):
        self.configs = configs
        configs.functionList.append(self.update_configs)
        self.heatingElement = self.configs.heaterElementPin
        os.system('fast-gpio set-output {}'.format(
            self.heatingElement
        ))

    def setHeater(self, value):
        os.system('fast-gpio pwm {gpio} {freq} {duty_cycle}'.format(
            gpio=self.heatingElement, freq=1, duty_cycle=value
        ))

    def update_configs(self):
        self.heatingElement = self.configs.heaterElementPin
