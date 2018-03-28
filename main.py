import logging
import time

import BlynkLib
from Configurator import Configurator
from RancilioSilvia import RancilioSilvia
from pid import PID

BLYNK_AUTH = 'ed56b3aa45b2416f9982452da05becad'

blynk = BlynkLib.Blynk(BLYNK_AUTH)

# logging stuff
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s', )


@blynk.VIRTUAL_WRITE(1)
def rancilio_main_switch_handler(value):
    configs.RancilioPoweredOn = bool(value)


@blynk.VIRTUAL_WRITE(2)
def rancilio_power_mode_handler(value):
    if value == 0:
        configs.RancilioPowerMode = configs.energy_mode.eco
    else:
        configs.RancilioPowerMode = configs.energy_mode.on
    configs.update()


@blynk.VIRTUAL_READ(3)
def rancilio_heat_status_handler():
    temperature = Rancilio.read_temperature_sensors()
    blynk.virtual_write(3, temperature)


def loop():
    blynk.virtual_write(2, time.ticks_ms() // 1000)


configs = Configurator()
Rancilio = RancilioSilvia(configs)
pid = PID()

blynk.set_user_task(loop, 50)

blynk.run()
