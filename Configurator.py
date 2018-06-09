from collections import namedtuple

from Singleton import Singleton


@Singleton
class Configurator:
    def __init__(self):
        self.energy_modi = namedtuple('energy_mode', 'off eco on steam')
        self.energy_mode = self.energy_modi(off=0, eco=1, on=2, steam=3)

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
                'setpoint': 20.0,
                },
            self.energy_mode.eco:   {
                'kp':       7,
                'ki':       0.1,
                'kd':       80,  # 30,
                'setpoint': 50.0,
                },
            self.energy_mode.on:    {
                'kp':       6.6,
                'ki':       0.1,
                'kd':       99,
                'setpoint': 95,
                },
            self.energy_mode.steam: {
                'kp':       8.5,
                'ki':       0.1,
                'kd':       100,
                'setpoint': 120.0,
                }
            }

        # data acquisition
        self.smoothingFactor = 2

        self.boilerTempSensor1 = '28-0000092c44f8'
        self.boilerTempSensor2 = '28-0000092d7d9f'

        # instance access
        self.dataLogger = None
        self.Rancilio = None

    def update(self):
        for f in self.functionList:
            f()
