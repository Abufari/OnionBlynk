import logging

import BlynkLib
from Configurator import Configurator

BLYNK_AUTH = 'ed56b3aa45b2416f9982452da05becad'
blynk = BlynkLib.Blynk(BLYNK_AUTH)


@blynk.VIRTUAL_WRITE(1)
def rancilio_main_switch_handler(value):
    logger = logging.getLogger('__main__.' + __name__)

    configs = Configurator.instance()
    powerOn = int(value)
    configs.RancilioPoweredOn = bool(powerOn)
    configs.update()
    status = 'on' if bool(powerOn) else 'off'
    logger.info('Rancilio is powered {}'.format(status))


@blynk.VIRTUAL_WRITE(2)
def rancilio_power_mode_handler(value):
    configs = Configurator.instance()
    logger = logging.getLogger('__main__.' + __name__)

    value = int(value)
    if value == 1:
        configs.RancilioPowerMode = configs.energy_mode.off
    elif value == 2:
        configs.RancilioPowerMode = configs.energy_mode.eco
    elif value == 3:
        configs.RancilioPowerMode = configs.energy_mode.on
    elif value == 4:
        configs.RancilioPowerMode = configs.energy_mode.steam
    else:
        configs.RancilioPowerMode = configs.energy_mode.off
        logger.error('Power Mode Handler: undefined value: {}'.format(
            value
            ))
        return
    configs.update()
    status = configs.energy_mode._fields[configs.RancilioPowerMode]
    logger.info('Rancilio is powered in {} mode'.format(status))


@blynk.VIRTUAL_WRITE(0)
def debug_handler(value):
    logger = logging.getLogger('__main__')

    value = int(value)
    if value == 0:
        logger.setLevel(logging.INFO)
        logger.info('Setting logger to INFO')
    elif value == 1:
        logger.setLevel(logging.DEBUG)
        logger.debug('Setting logger to DEBUG')


def rancilio_temperature_status_handler():
    configs: Configurator = Configurator.instance()
    dataLogger = configs.dataLogger
    logger = logging.getLogger('__main__.' + __name__)

    temperature = dataLogger.boilerTemp
    if temperature is None:
        logger.warning('Temperature is None: {}'.format(temperature))
        return

    blynk.virtual_write(3, temperature)


def rancilio_heater_status_handler():
    configs = Configurator.instance()
    dutyCycle = configs.heater_output
    # map down to 0-255
    led = int(dutyCycle / 100 * 255)
    blynk.virtual_write(5, led)


def rancilio_ready_handler():
    configs = Configurator.instance()
    ready = configs.RancilioHeatedUp
    if ready:
        blynk.virtual_write(4, 255)
    else:
        blynk.virtual_write(4, 0)
