from collections import namedtuple

from Singleton import Singleton


@Singleton
class Configurator:
    def __init__(self):
        self.energy_modi = namedtuple('energy_mode', 'off on eco steam')
        self.energy_mode = self.energy_modi(off=0, on=1, eco=2, steam=3)

        self.functionList = []
        self.current_mode = self.energy_mode.on
        self.RancilioPoweredOn = False
        self.RancilioPowerMode = self.energy_mode.eco
        self.RancilioHeatedUp = False

        # Onion Omega Pins
        self.heaterElementPin = 18
        self.tempSensorPin = 19

        # PID variables
        self.heater_output = 0
        self.pid_configs = {
            self.energy_mode.off:   {
                'kp':       0,
                'ki':       0.0,
                'kd':       0,
                'setpoint': 0,
                },
            self.energy_mode.eco:   {
                'kp':       5,
                'ki':       0.0,
                'kd':       0,
                'setpoint': 50,
                },
            self.energy_mode.on:    {
                'kp':       20,
                'ki':       0.10,
                'kd':       10,
                'setpoint': 94,
                },
            self.energy_mode.steam: {
                'kp':       10,
                'ki':       0,
                'kd':       0,
                'setpoint': 115,
                }
            }

        # data acquisition
        self.smoothingFactor = 1

        self.boilerTempSensor1 = '28-0000092c44f8'
        self.boilerTempSensor2 = '28-0000092d7d9f'

        # instance access
        self.dataLogger = None
        self.Rancilio = None

    def update(self):
        for f in self.functionList:
            f()
