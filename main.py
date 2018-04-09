import logging
import time
from threading import Thread, Event

import BlynkLib
from Configurator import Configurator
from DataLogger import DataLogger
from RancilioSilvia import RancilioSilvia

BLYNK_AUTH = 'ed56b3aa45b2416f9982452da05becad'

blynk = BlynkLib.Blynk(BLYNK_AUTH)

# logging stuff
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler(
                            '/root/RancilioSilviaBlynk/onionBlynk.log'),
                        logging.StreamHandler()
                        ])
logger = logging.getLogger(__name__)


@blynk.VIRTUAL_WRITE(1)
def rancilio_main_switch_handler(value):
    powerOn = int(value)
    configs.RancilioPoweredOn = bool(powerOn)
    configs.update()
    status = 'on' if bool(powerOn) else 'off'
    logger.info('Rancilio is powered {}'.format(status))


@blynk.VIRTUAL_WRITE(2)
def rancilio_power_mode_handler(value):
    value = int(value)
    if value == 0:
        configs.RancilioPowerMode = configs.energy_mode.eco
    else:
        configs.RancilioPowerMode = configs.energy_mode.on
    configs.update()
    status = 'on' if bool(value) else 'eco'
    logger.info('Rancilio is powered in {} mode'.format(status))


@blynk.VIRTUAL_WRITE(0)
def debug_handler(value):
    value = int(value)
    if value == 0:
        logger.setLevel(logging.INFO)
        logger.info('Setting logger to INFO')
    elif value == 1:
        logger.setLevel(logging.DEBUG)
        logger.debug('Setting logger to DEBUG')


def rancilio_temperature_status_handler():
    temperature = dataLogger.boilerTemp
    if temperature is not None:
        blynk.virtual_write(3, temperature)


def rancilio_heater_status_handler():
    dutyCycle = configs.heater_output
    # map down to 0-255
    led = int(dutyCycle / 100 * 255)
    blynk.virtual_write(5, led)


def rancilio_ready_handler():
    ready = configs.RancilioHeatedUp
    blynk.virtual_write(4, ready)


class loop():
    def __init__(self, _stopEvent: Event):
        self.stopEvent = _stopEvent

    def run(self):
        while not self.stopEvent.is_set():
            rancilio_temperature_status_handler()
            Rancilio.update()
            rancilio_heater_status_handler()
            rancilio_ready_handler()
            time.sleep(1)


configs = Configurator()

# Threading stuff
stopEvent = Event()
error_in_method_event = Event()
dataLogger = DataLogger(configs, stopEvent, error_in_method_event)
dataLogger.newTemperatureSensor('boiler', configs.boilerTempSensor1)
temperatureAcquisitionProcess = Thread(target=dataLogger.acquireData)
temperatureAcquisitionProcess.start()

Rancilio = RancilioSilvia(configs, dataLogger)

myloop = loop(stopEvent)
myloop_thread = Thread(target=myloop.run, daemon=True)
myloop_thread.start()
blynk.on_connect(blynk.sync_all)

try:
    blynk.run()
except KeyboardInterrupt:
    stopEvent.set()
