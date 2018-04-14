class Singleton:

    def __init__(self, decorated):
        self._decorated = decorated
        self._instance = None

    def instance(self):
        if self._instance is not None:
            return self._instance
        else:
            self._instance = self._decorated()
            return self._instance

    def __call__(self, *args, **kwargs):
        raise TypeError('Singletons must be accessed through instance()')

    def __instancecheck__(self, instance):
        return isinstance(instance, self._decorated)
