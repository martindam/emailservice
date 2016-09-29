import logging
import time

from email import Email


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

# Base class for mail service implementations.
class MailServerBase(object):

    def __init__(self):
        pass

    # Send the email using the service. Raises an exception in case of error
    def send(self, email):
        assert isinstance(email, Email)
        self._do_send(email)

    # Actually send the email and raise an exception on error
    def _do_send(self, email):
        raise NotImplementedError

    # Return the 'quality' of the service calculated in terms of various
    # factors like cost, response time, average queue time, availability and
    # so on.
    # Return an integer value between 0 and 100 where 100 is the highest score.
    def get_service_score(self):
        return 50


# Simple service base that calculates the service score based on a moving
# average of the service health where the health is defined as 1 if email
# was sent successfully and 0 if not. The time since last error is used as
# a linear weight between base score and service health score
class BackoffOnFailureMailServiceBase(MailServerBase):

    def __init__(self, base_score=50):
        super(BackoffOnFailureMailServiceBase, self).__init__()
        self._base_score = base_score
        self._service_health = 1.0
        self._last_error = 0

    def send(self, email):
        assert isinstance(email, Email)
        try:
            self._do_send(email)
            self._service_health = self._service_health * 0.9 + 0.1
        except (ServerException, TooManyRequests) as e:
            self._service_health = self._service_health * 0.9
            self._last_error = time.time()
            logging.error(
                "Server exception. Decreasing service score to %s" % self.get_service_score())
            raise

    def get_service_score(self):
        time_since_last_error = time.time() - self._last_error

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
