import time

from PinHandler import PinHandler


class Heater(object):
    def __init__(self, configs):
        self.output = 0
        self.cycleStartTime = time.time()
        self.cycleMilliseconds = 1000

        self.onTime = 0

        self.pinHandler = PinHandler(configs)

    def heaterHandler(self):
        onDuration = self.output / 100 * self.cycleMilliseconds
        now = time.time()
        if now - self.cycleStartTime < onDuration:
            self.pinHandler.setHeater(1)
        elif now - self.cycleStartTime < self.cycleMilliseconds:
            self.pinHandler.setHeater(0)
        else:
            self.cycleStartTime = time.time()

    def update(self, output):
        self.output = min(output, 100)
        self.heaterHandler()


class RancilioSilvia:
    def __init__(self, configs):
        self.heater = Heater(configs)

    def setHeaterOutput(self, output):
        self.heater.output = output
