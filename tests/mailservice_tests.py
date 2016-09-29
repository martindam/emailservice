import context
import unittest
import time

from micromailer.email import Email
from micromailer.mailservice import BackoffOnFailureMailServiceBase, ServerException


class MockMailService(BackoffOnFailureMailServiceBase):

    def __init__(self):
        super(MockMailService, self).__init__(50)

    def _do_send(self, email):
        pass


class MockFailingMailService(BackoffOnFailureMailServiceBase):

    def __init__(self, fail_pattern=[ServerException()]):
        super(MockFailingMailService, self).__init__(50)
        self._index = 0
        self._fail_pattern = fail_pattern

    def _do_send(self, email):
        index = self._index
        self._index = index + 1

        if self._fail_pattern[index] is not None:
            raise self._fail_pattern[index]


class BackoffOnFailureMailServiceBaseTestSuite(unittest.TestCase):

    def get_email(self):
        return Email("valid@email.com", "anothervalid@email.com", "Subject", "Content")

    def test_base_score_on_no_errors(self):
        service = MockMailService()
        service.send(self.get_email())
        self.assertEquals(service.get_service_score(), 50)

    def test_base_score_on_single_failure(self):
        service = MockFailingMailService(fail_pattern=[ServerException()])
        with self.assertRaises(ServerException):
            service.send(self.get_email())

        self.assertLess(service._service_health, 1)
        self.assertAlmostEqual(time.time(), service._last_error, 2)
        self.assertLess(service.get_service_score(), 50)

    def test_base_score_on_multiple_failure(self):
        service = MockFailingMailService(fail_pattern=[ServerException(),
            ServerException(), ServerException(), ServerException(), ServerException(), 
            None, None, None, None, None])
        last_score = service.get_service_score()

        # 5 failing requests, the score will decrease
        for i in range(5):
            with self.assertRaises(ServerException):
                service.send(self.get_email())
            new_score = service.get_service_score()
            self.assertLess(new_score, last_score)
            last_score = new_score

        # 5 successful requests, the score will increase
        for i in range(5):
            service.send(self.get_email())
            new_score = service.get_service_score()
            self.assertGreater(new_score, last_score)
            last_score = new_score

    def test_base_score_restores_after_300sec(self):
        service = MockFailingMailService(fail_pattern=[ServerException()])
        with self.assertRaises(ServerException):
            service.send(self.get_email())
        self.assertLess(service.get_service_score(), 50)

        service._last_error = time.time() - 310
        self.assertEquals(service.get_service_score(), 50)
        self.assertLess(service._service_health, 1)


if __name__ == '__main__':
    unittest.main()
