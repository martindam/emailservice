# Integration tests that tests the communication between the webservice
# and the workers with the micromailer dispatcher.
# Does not test the integration with external mail services

import context
import unittest
import time
import json
import threading

from celery.bin import worker
from celery.signals import worker_ready

import tasks
import webservice
from micromailer import mailservice


class FakeMailService(mailservice.BackoffOnFailureMailServiceBase):

    def __init__(self, service_score, name):
        super(FakeMailService, self).__init__(service_score)
        self._name = name
        self._should_fail = False

    def _do_send(self, email):
        if self._should_fail:
            raise mailservice.ServerException("Fake failure")
        return {"status": "success", "_service": self.get_name()}

    def get_name(self):
        return self._name


# Use fake mail services for integration tests
tasks.dispatcher._services = []
prefered_service = FakeMailService(50, "prefered")  # Prefered service
secondary_service = FakeMailService(49, "secondary")
tasks.dispatcher.add_service(secondary_service)
tasks.dispatcher.add_service(prefered_service)


class IntegrationTests(unittest.TestCase):

    def setUp(self):
        if getattr(self, '_worker', None) is None:
            tasks.celeryApp.conf.update(
                BROKER_URL="memory://",
                BROKER_TRANSPORT_OPTIONS={"polling_interval": .01},
                CELERY_RESULT_BACKEND="cache",
                CELERY_CACHE_BACKEND="memory",
                CELERYD_CONCURRENCY=1,
                CELERYD_POOL="solo"
            )

            self._worker = worker.worker(app=tasks.celeryApp)

            self._worker_ready = False
            self._thread = threading.Thread(target=self._worker.run, kwargs={"loglevel": "DEBUG"})
            self._thread.setDaemon(True)
            self._thread.start()

            @worker_ready.connect
            def on_worker_ready(**kargs):
                self._worker_ready = True

            self._wait_for_worker()

        # Reset the services to avoid interference between tests
        prefered_service.reset_score()
        prefered_service._should_fail = False
        secondary_service.reset_score()
        secondary_service._should_fail = False

    def _wait_for_worker(self):
        timeout_at = time.time() + 30
        while not self._worker_ready:
            time.sleep(0.1)
            if time.time() > timeout_at:
                raise Exception("Worker did not start")

    def test_simple_email(self):
        web_app = webservice.app.test_client()

        payload = {"to": "martinslothdam@gmail.com", "subject": "Test", "content": "Integration testing"}
        resp = web_app.post("/email", data=payload)

        assert resp.status_code == 200

        # Get the result
        result = web_app.get("/email/%s" % json.loads(resp.get_data())["emailId"])
        result_json = json.loads(result.get_data())
        assert result.status_code == 200
        assert result_json["status"] == "success"
        assert result_json["result"]["_service"] == "prefered"

    def test_nonexisting_email(self):
        web_app = webservice.app.test_client()

        resp = web_app.get("/email/359df1ed-c91e-471f-9fa2-7aaf38a26a01")
        resp_json = json.loads(resp.get_data())
        assert resp.status_code == 200
        assert resp_json["status"] == "notfound"

    # Test that a task is retried if the first attempt fails
    def test_retry_service(self):
        prefered_service._should_fail = True

        web_app = webservice.app.test_client()

        payload = {"to": "martinslothdam@gmail.com", "subject": "Test", "content": "Integration testing"}
        resp = web_app.post("/email", data=payload)

        assert resp.status_code == 200

        # Sleep for 11 seconds as the retry takes 10 sec
        time.sleep(11)

        # Get the result
        result = web_app.get("/email/%s" % json.loads(resp.get_data())["emailId"])
        result_json = json.loads(result.get_data())
        print result.get_data()
        assert result.status_code == 200
        assert result_json["status"] == "success"
        assert result_json["result"]["_service"] == "secondary"


if __name__ == "__main__":
    unittest.main()
