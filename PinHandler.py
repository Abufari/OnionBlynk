import Configurator


class PinHandler(object):
    def __init__(self, configs: Configurator.Configurator):
        self.configs = configs
        configs.functionList.append(self.update_configs)
        self.heatingElement = onionGpio.OnionGpio(
            self.configs.heaterElementPin)
        status = self.heatingElement.setOutputDirection(0)
        if status == 0:
            raise ValueError

    def setHeater(self, value):
        self.heatingElement.setValue(value)

    def update_configs(self, other: Configurator.Configurator):
        self.heatingElement = onionGpio.OnionGpio(other.heaterElementPin)
