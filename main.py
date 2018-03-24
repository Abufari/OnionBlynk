import random
import time

import BlynkLib
from Configurator import Configurator

BLYNK_AUTH = 'ed56b3aa45b2416f9982452da05becad'

blynk = BlynkLib.Blynk(BLYNK_AUTH)


class randomValue:
    def __init__(self):
        self.value = 0

    def next(self):
        self.value += random.random() * (-1) ** random.choice([0, 1]) + 0.05
        return self.value


def loop():
    blynk.virtual_write(2, time.ticks_ms() // 1000)
    blynk.virtual_write(4, rV.next())


configs = Configurator()

rV = randomValue()
blynk.set_user_task(loop, 500)

blynk.run()
