from collections import namedtuple


class Configurator:
    energy_modi = namedtuple('energy_mode', 'on eco')
    energy_mode = energy_modi(on=1, eco=2)

    def __init__(self):
        self.heaterElementPin = 1
        self.functionList = []
        self.current_mode = Configurator.energy_mode.on
        self.RancilioPoweredOn = False
        self.RancilioPowerMode = Configurator.energy_mode.eco

        # PID variables
        self.pid_configs = {
            Configurator.energy_mode.on: {
                'kp': 0,
                'ki': 0,
                'kd': 0,
                'setpoint': 98,
            },
            Configurator.energy_mode.eco: {
                'kp': 0,
                'ki': 0,
                'kd': 0,
                'setpoint': 50,
            }
        }

    def update(self):
        for f in self.functionList:
            f()
