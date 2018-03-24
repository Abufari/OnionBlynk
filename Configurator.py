class Configurator:
    def __init__(self):
        self.heaterElementPin = 1
        self.functionList = []

    def update(self):
        for f in self.functionList:
            f(self)
