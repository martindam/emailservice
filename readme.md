# Micro email service



## Installation

```
pip install -r requirements.txt
```

## Running locally



## Service selection strategy
The services are selected based on a continous score that is calculated the for service.
When a service failure is detected (server, authentication or too many request exceptions), the score for the service is exponential degraged (with a factor of 0.9). This will result in the score going down until another service is selected as the primary service. Over time the score will linearly (5 min) go back to its base score if it is not used or there are no more errors. When the service is no longer experiencing degraded performance, the service score will slowly restore to its base score and again become the primary service. See the algorithm in [mailservice.py](micromailer/mailservice.py). See [figure](docs/backoff_alg_single.png) on how the algorithm work for a single service.

[Simulations](tests/backoff_all_simulate.py) of this algorighm and the selection of the service with the highest score reveals significant error rate reduction under various service degradation patterns. See figure below. Note: Failures in this context is the failure to deliver an email to a single service, however the dispatcher falls back to the secondary service in this case and still delivers the email.

![Service score selection algorithm simulation](docs/backoff_alg_withalternative.png)


## Improvements
The following improvements should/could be made:
 - Do not use Pickle as serialization for the task queue. Pickle is going to be deprecated in Celery 3.2 due to security concerns so switch to use JSON or similar on the task queue
 