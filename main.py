import logging
import time

import BlynkLib
from Configurator import Configurator
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
    temperature = Rancilio.read_temperature_sensors('boiler')
    if temperature is not None:
        blynk.virtual_write(3, temperature)


def rancilio_heater_status_handler():
    dutyCycle = configs.heater_output
    # map down to 0-255
    led = dutyCycle / 100 * 255
    blynk.virtual_write(5, led)


def rancilio_ready_handler():
    ready = configs.RancilioHeatedUp
    blynk.virtual_write(4, ready)


def loop():
    global lastTempStatus
    global lastHeaterStatus
    global lastRacilioReadStatus
    now = time.time()
    if now - lastTempStatus > 5:
        rancilio_temperature_status_handler()
        lastTempStatus = now
    if now - lastHeaterStatus > 1:
        rancilio_heater_status_handler()
        lastHeaterStatus = now
    if now - lastRacilioReadStatus > 5:
        rancilio_ready_handler()
        lastRacilioReadStatus = now
    if time.time() - lastTempStatus > 5:
        rancilio_temperature_status_handler()
        lastTempStatus = time.time()


configs = Configurator()
Rancilio = RancilioSilvia(configs)

lastTempStatus = time.time()
lastHeaterStatus = time.time()
lastRacilioReadStatus = time.time()
blynk.set_user_task(loop, 50)

blynk.run()
