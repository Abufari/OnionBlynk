import time
from threading import Thread, Event

from BlynkInterface import *
from Configurator import Configurator
from DataLogger import DataLogger
from RancilioSilvia import RancilioSilvia

# logging stuff
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)s %(levelname)s %(message)s',
                    handlers=[
                        logging.FileHandler(
                            '/root/RancilioSilviaBlynk/onionBlynk.log'),
                        logging.StreamHandler()
                        ])
logger = logging.getLogger(__name__)


class loop:
    def __init__(self, _stopEvent: Event):
        self.stopEvent = _stopEvent

    def run(self):
        while not self.stopEvent.is_set():
            rancilio_temperature_status_handler()
            Rancilio.update()
            rancilio_heater_status_handler()
            rancilio_ready_handler()
            time.sleep(1)


configs = Configurator.instance()

# Threading stuff
stopEvent = Event()
error_in_method_event = Event()
dataLogger = DataLogger(stopEvent, error_in_method_event)
dataLogger.addTemperatureSensor('boiler', configs.boilerTempSensor2)
configs.dataLogger = dataLogger
temperatureAcquisitionProcess = Thread(target=dataLogger.acquireData)
temperatureAcquisitionProcess.start()

Rancilio = RancilioSilvia()
configs.Rancilio = Rancilio

myloop = loop(stopEvent)
myloop_thread = Thread(target=myloop.run, daemon=True)
myloop_thread.start()
blynk.on_connect(blynk.sync_all)

try:
    blynk.run()
except KeyboardInterrupt:
    stopEvent.set()
