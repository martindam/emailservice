# Script to simulate the mail service score algorithm and dispatching selection when a service is expericing errors.
# This script simulates requests over a 30 min period with 10 msg/s with various failure scenarios.
# Two graphs are outputted:
#  1) Service failure rate with the score algorithm compared with a simple "select a service at random" strategy
#  2) The behavior of the service score when there is only a single service

import context
import random
import matplotlib.pyplot as plt

from micromailer.mailservice import BackoffOnFailureMailServiceBase, ServerException
from micromailer.email import Email


class MockFailingMailService(BackoffOnFailureMailServiceBase):

    def __init__(self, send_callback):
        super(MockFailingMailService, self).__init__(50)
        self._index = 0
        self._send_callback = send_callback

    def _do_send(self, email):
        index = self._index
        self._index = index + 1

        self._send_callback(index, self._get_time())

    def _get_time(self):
        return self._time

    def set_time(self, time):
        self._time = time


# Simulate random 5% failure rate
def uniform_random_5percentage_error(index, time):
    if random.uniform(0, 100) <= 5:
        raise ServerException()


# A continous outage of service for 10 min after 200 sec
def continous_failure_10min(index, time):
    if time > 200 and time < 800:
        raise ServerException()


# A 50% service degradation for 10 min after 200 sec
def sporadic_failure_10min(index, time):
    if time > 200 and time < 800:
        if random.uniform(0, 100) <= 50:
            raise ServerException()


# The service is working perfectly
def no_failure(index, time):
    pass


def get_email():
        return Email("valid@email.com", "anothervalid@email.com", "Subject", "Content")


def run_test(callback_a, alternative_base_score=40, disable_alg=False):
    x = [x / 10.0 for x in range(0, 18000, 1)]
    scores_A = []
    scores_B = []

    exceptions = 0
    attempts = 0
    service_A = MockFailingMailService(callback_a)
    service_B = MockFailingMailService(no_failure)
    service_B._base_score = alternative_base_score

    # Simulate that the services are picked at random instead of using the score algorithm
    if disable_alg:
        service_A.get_service_score = lambda: random.uniform(0, 50)
        service_B.get_service_score = lambda: random.uniform(0, 50)

    options = [service_A, service_B]
    for t in [v / 10.0 for v in range(0, 18000, 1)]:
        service_A.set_time(t)
        service_B.set_time(t)

        options = sorted(options, key=lambda x: x.get_service_score(), reverse=True)
        for option in options:
            try:
                attempts = attempts + 1
                option.send(get_email())
                break
            except ServerException:
                exceptions = exceptions + 1
        scores_A.append(service_A.get_service_score())
        scores_B.append(service_B.get_service_score())

    # Calculate moving average for better graph
    yA = []
    for score in scores_A:
        if len(yA) > 0:
            yA.append(yA[-1] * 0.90 + score * 0.1)
        else:
            yA.append(score)

    yB = []
    for score in scores_B:
        if len(yB) > 0:
            yB.append(yB[-1] * 0.90 + score * 0.1)
        else:
            yB.append(score)

    return (x, yA, yB, exceptions, attempts)


def plot_data(fig_no, title, result):
    x = result[0]
    yA = result[1]
    yB = result[2]
    exceptions = result[3]
    attempts = result[4]

    plt.subplot(fig_no)
    plt.plot(x, yA, 'b', x, yB, '--r')
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
    plt.ylabel('Service score')
    plt.xlabel('Time [s]')
    plt.title(title % (exceptions / float(attempts) * 100))
    plt.ylim([0, 55])


if __name__ == '__main__':

    # Simulate without algorithm to determine failure rate
    result = run_test(continous_failure_10min, disable_alg=True)
    no_alg_continous_error_rate = result[3] / float(result[4]) * 100

    result = run_test(sporadic_failure_10min, disable_alg=True)
    no_alg_sporadic_error_rate = result[3] / float(result[4]) * 100

    result = run_test(uniform_random_5percentage_error, disable_alg=True)
    no_alg_random_error_rate = result[3] / float(result[4]) * 100

    # Plot the simulations of the service scores
    fig = plt.figure(1)
    plot_data(311, '10 min complete service failure - %%.2f%%%% failure rate (vs %.2f w/o alg)' % no_alg_continous_error_rate,
              run_test(continous_failure_10min))
    plot_data(312, '10 min sporadic service failure - %%.2f%%%% failure rate (vs %.2f w/o alg)' % no_alg_sporadic_error_rate,
              run_test(sporadic_failure_10min))
    plot_data(313, 'Random 5%%%% service failure - %%.2f%%%% failure rate (vs %.2f w/o alg)' % no_alg_random_error_rate,
              run_test(uniform_random_5percentage_error))
    plt.legend(['Prefered service', 'Alternative service'], 'lower right')
    fig.tight_layout()

    # Plot service score with a single service
    fig = plt.figure(2)
    plot_data(311, '10 msg/s with 10 min complete service failure - %.2f%% failure rate', run_test(continous_failure_10min, alternative_base_score=0))
    plot_data(312, '10 msg/s with 10 min sporadic service failure - %.2f%% failure rate', run_test(sporadic_failure_10min, alternative_base_score=0))
    plot_data(313, '10 msg/s with random 5%% service failure - %.2f%% failure rate', run_test(uniform_random_5percentage_error, alternative_base_score=0))
    fig.tight_layout()
    plt.show()
