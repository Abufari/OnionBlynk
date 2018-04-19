import logging

import BlynkLib
from Configurator import Configurator
from pid import PID

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

    # set Gauge to new range
    setpoint = configs.pid_configs[configs.RancilioPowerMode]['setpoint']
    blynk.setProperty(3, 'min', setpoint * 0.8)
    blynk.setProperty(3, 'max', setpoint * 1.2)

    # set Slider settings
    blynk.virtual_write(9, setpoint)
    if configs.RancilioPowerMode == configs.energy_mode.off:
        blynk.setProperty(9, 'min', 18)
        blynk.setProperty(9, 'max', 25)
    elif configs.RancilioPowerMode == configs.energy_mode.eco:
        blynk.setProperty(9, 'min', 40)
        blynk.setProperty(9, 'max', 60)
    elif configs.RancilioPowerMode == configs.energy_mode.on:
        blynk.setProperty(9, 'min', 92)
        blynk.setProperty(9, 'max', 110)
    elif configs.RancilioPowerMode == configs.energy_mode.steam:
        blynk.setProperty(9, 'min', 105)
        blynk.setProperty(9, 'max', 125)


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


@blynk.VIRTUAL_WRITE(9)
def setpoint_handler(value):
    logger = logging.getLogger('__main__.' + __name__)
    configs: Configurator = Configurator.instance()

    value = float(value)
    configs.pid_configs[configs.RancilioPowerMode]['setpoint'] = value
    configs.update()


def rancilio_temperature_status_handler():
    configs: Configurator = Configurator.instance()
    dataLogger = configs.dataLogger
    pid = PID.instance()
    logger = logging.getLogger('__main__.' + __name__)

    temperature = dataLogger.boilerTemp
    if temperature is None:
        logger.warning('Temperature is None: {}'.format(temperature))
        return

    blynk.virtual_write(3, temperature)
    blynk.virtual_write(6, pid.proportional_term)
    blynk.virtual_write(7, pid.integral_term)
    blynk.virtual_write(8, pid.derivative_term)


@blynk.VIRTUAL_READ(4)
def rancilio_ready_handler():
    configs = Configurator.instance()
    ready = configs.RancilioHeatedUp
    if ready:
        blynk.virtual_write(4, 255)
    else:
        blynk.virtual_write(4, 0)


@blynk.VIRTUAL_READ(5)
def rancilio_heater_status_handler():
    configs = Configurator.instance()
    dutyCycle = configs.heater_output
    blynk.virtual_write(5, dutyCycle)


@blynk.VIRTUAL_READ(6)
def pid_proportional_handler():
    pid = PID.instance()
    blynk.virtual_write(6, pid.proportional_term)


@blynk.VIRTUAL_READ(7)
def pid_integral_handler():
    pid = PID.instance()
    blynk.virtual_write(7, pid.integral_term)


@blynk.VIRTUAL_READ(8)
def pid_derivative_handler():
    pid = PID.instance()
    blynk.virtual_write(8, pid.derivative_term)


def blynk_check_live_connection():
    return blynk.state


def blynk_shut_down():
    blynk.virtual_write(1, 0)
    blynk.virtual_write(2, 1)
