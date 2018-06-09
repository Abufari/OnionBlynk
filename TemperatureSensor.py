import logging

import oneWire
from Configurator import Configurator
from RancilioError import RancilioError


class SensorInitiator:
    def __init__(self, interface=None, args=None):
        self.supportedInterfaces = ['oneWire']
        self.interface = interface
        self.ready = False
        self.logger = logging.getLogger('__main__.' + __name__)

        if self.interface not in self.supportedInterfaces:
            self.logger.warning('Unsupported interface.')
            self.listInterfaces()
            return

        # set up a driver based on the interface type
        if self.interface == 'oneWire':
            self.driver = oneWire.OneWire(args.get('address'),
                                          args.get('gpio', None))
            self.ready = self.driver.setupComplete

    def readValue(self):
        if self.ready:
            return self.__readOneWire()
        else:
            return None

    def listInterfaces(self):
        self.logger.warning('The supported interfaces are:')
        for interface in self.supportedInterfaces:
            self.logger.warning(str(interface))

    def __readOneWire(self):
        rawValue = self.driver.readDevice()

        value = rawValue[1].split()[-1].split('=')[1]
        value = int(value)

        value /= 1000
        return value


class TemperatureSensor:
    sensor: SensorInitiator

    def __init__(self, sensorAddress: str = None):
        self.logger = logging.getLogger(__name__)
        self.configs = Configurator.instance()
        self.oneWireStatus = oneWire.setupOneWire(
            self.configs.tempSensorPin)

        self.lastTemperature = None

        self.sensorAddress = sensorAddress
        self.sensor = None

    def setupSensor(self):
        if not self.oneWireStatus:
            return False
        if not self.sensorAddress:
            self.sensorAddress = oneWire.scanOneAddress()
            self.logger.info('Found logger with address: {}'.format(
                self.sensorAddress
                ))

        if not self.sensorAddress:
            return False
        self.sensor = SensorInitiator('oneWire', {
            'address': self.sensorAddress,
            'gpio':    self.configs.tempSensorPin
            })

        if not self.sensor.ready:
            self.logger.warning(
                'Sensor was not set up correctly. Please make '
                'sure that your sensor is firmly connected '
                'to the GPIO {} and try again.'.format(
                    self.configs.tempSensorPin
                    )
                )
        self.lastTemperature = self.sensor.readValue()
        return True

    def readTemperature(self):
        temperature = self.sensor.readValue()
        if temperature is None:
            rancilioError = RancilioError.instance()
            rancilioError.tempSensorFail = (True, str(self.sensorAddress))
            self.logger.error("Couldn't read temperature at all")
        elif abs(temperature - self.lastTemperature) > 5:
            rancilioError = RancilioError.instance()
            rancilioError.tempSensorFail = (True, str(self.sensorAddress))
            self.logger.error(
                'Temperature difference between readings is {}°C'.format(
                    temperature - self.lastTemperature
                    ))
        self.lastTemperature = temperature
        return temperature
