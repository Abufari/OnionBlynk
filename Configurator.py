from collections import namedtuple


class Configurator:
    energy_modi = namedtuple('energy_mode', 'on eco steam')
    energy_mode = energy_modi(on=1, eco=2, steam=3)

    def __init__(self):
        self.functionList = []
        self.current_mode = Configurator.energy_mode.on
        self.RancilioPoweredOn = False
        self.RancilioPowerMode = Configurator.energy_mode.eco
        self.RancilioHeatedUp = False

        # Onion Omega Pins
        self.heaterElementPin = 18
        self.tempSensorPin = 19

        # PID variables
        self.heater_output = 0
        self.pid_configs = {
            Configurator.energy_mode.on:    {
                'kp':       2,
                'ki':       0.01,
                'kd':       0,
                'setpoint': 98,
                },
            Configurator.energy_mode.eco:   {
                'kp':       0,
                'ki':       0,
                'kd':       0,
                'setpoint': 50,
                },
            Configurator.energy_mode.steam: {
                'kp':       0,
                'ki':       0,
                'kd':       0,
                'setpoint': 115,
                }
            }

        # data acquisition
        self.smoothingFactor = 8

        self.boilerTempSensor1 = '28-0000092c44f8'
        self.boilerTempSensor2 = '28-0000092d7d9f'

    def update(self):
        for f in self.functionList:
            f()
