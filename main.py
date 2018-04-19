import time
from threading import Thread, Event

from BlynkInterface import *
from Configurator import Configurator
from DataLogger import DataLogger
from RancilioError import RancilioError
from RancilioSilvia import RancilioSilvia
# logging stuff
from SystemHealthMonitor import SystemHealthMonitor

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

        # stop event is set
        Rancilio.setHeaterOutput(0)


configs = Configurator.instance()

# Threading stuff
stopEvent = Event()
error_in_method_event = Event()
dataLogger = DataLogger(stopEvent, error_in_method_event)
dataLogger.addTemperatureSensor('boiler', configs.boilerTempSensor1)
dataLogger.addTemperatureSensor('boiler', configs.boilerTempSensor2)
configs.dataLogger = dataLogger
temperatureAcquisitionProcess = Thread(target=dataLogger.acquireData)
temperatureAcquisitionProcess.start()

Rancilio = RancilioSilvia()
configs.Rancilio = Rancilio

rancilioError = RancilioError.instance()
rancilioError.blynkShutDownFcn = blynk_shut_down
rancilioError.blynkAliveFcn = blynk_check_live_connection

shm = SystemHealthMonitor()
shm.stopEvent = stopEvent
shm_thread = Thread(target=shm.run, daemon=True)
shm_thread.start()

myloop = loop(stopEvent)
myloop_thread = Thread(target=myloop.run, daemon=True)
myloop_thread.start()
blynk.on_connect(blynk.sync_all)

try:
    blynk.run()
except KeyboardInterrupt:
    stopEvent.set()
