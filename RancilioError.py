from Singleton import Singleton


@Singleton
class RancilioError:
    def __init__(self):
        self.tempSensorFail = (False, '')

        self.blynkShutDownFcn = None
        self.blynkAliveFcn = None
