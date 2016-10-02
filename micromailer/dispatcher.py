from threading import RLock
import logging

from mailservice import MailServerBase


class MailDispatcher():

    def __init__(self):
        self._services = []
        self._lock = RLock()

    def add_service(self, service):
        with self._lock:
            assert isinstance(service, MailServerBase)
            self._services.append(service)

    def send(self, email):
        service_to_use = None
        with self._lock:
            assert len(self._services) > 0
            service_to_use = max(self._services, key=lambda x: x.get_service_score())

        logging.debug("Using %s with score=%.2f for delivering email" %
                      (service_to_use.get_name(), service_to_use.get_service_score()))
        return service_to_use.send(email)
