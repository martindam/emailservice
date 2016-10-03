import logging
import time
from threading import RLock

from models import Email


class MailServiceException(Exception):
    pass


# Request was malformed
class BadRequest(MailServiceException):
    pass


# Not authorized to issue request
class UnauthorizedRequest(MailServiceException):
    pass


# The service had an internal error
class ServerException(MailServiceException):
    pass


# Request limit reached on server
class TooManyRequests(MailServiceException):
    pass


# Network error like DNS, unable to connect etc.
class NetworkException(MailServiceException):
    pass


# Base class for mail service implementations.
class MailServiceBase(object):

    def __init__(self):
        pass

    # Send the email using the service. Raises an exception in case of error
    def send(self, email):
        assert isinstance(email, Email)
        email.is_valid()
        return self._do_send(email)

    # Actually send the email and raise an exception on error
    def _do_send(self, email):
        raise NotImplementedError

    # Return the 'quality' of the service calculated in terms of various
    # factors like cost, response time, average queue time, availability and
    # so on.
    # Return an integer value between 0 and 100 where 100 is the highest score.
    def get_service_score(self):
        return 50

    def get_name(self):
        return "Unknown"


# Simple service base that calculates the service score based on a moving
# average of the service health where the health is defined as 1 if email
# was sent successfully and 0 if not. The time since last error is used as
# a linear weight between base score and service health score
class BackoffOnFailureMailServiceBase(MailServiceBase):

    def __init__(self, base_score=50):
        super(BackoffOnFailureMailServiceBase, self).__init__()
        self._base_score = base_score
        self._lock = RLock()
        self.reset_score()
        self._logger = logging.getLogger("mailservice")

    def reset_score(self):
        with self._lock:
            self._service_health = 1
            self._last_error = 0

    def send(self, email):
        assert isinstance(email, Email)
        email.is_valid()
        try:
            result = self._do_send(email)
            self._update_service_health(True)
            return result
        except (ServerException, UnauthorizedRequest, TooManyRequests):
            self._update_service_health(False)
            self._logger.error(
                "Server exception. Decreasing service score to %s" % self.get_service_score())
            raise

    def _update_service_health(self, success):
        with self._lock:
            if success:
                self._service_health = self._service_health * 0.9 + 0.1
            else:
                self._service_health = self._service_health * 0.9
                self._last_error = self._get_time()

    def get_service_score(self):
        with self._lock:
            time_since_last_error = self._get_time() - self._last_error

            # Linear weight over 5 min.
            # Right after a failure, the service health score is weighted 100%, at
            # 150 sec it is 50%/50% for the base score and health and after 300 sec
            # the base score is used 100%
            # This allows to keep degrading the service health in the presence of
            # failures until it is not longer being used as other services are
            # prefered. When the service recovers, the score will increase as no
            # new errors are observed and the service health will go back up to
            # normal
            time_weight = min(1, time_since_last_error / 300)
            return min(100, max(0, self._base_score * (1 * time_weight + self._service_health * (1 - time_weight))))

    def _get_time(self):
        return time.time()
