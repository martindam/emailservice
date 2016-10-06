# Micro email service

This project implements a simple HTTP email service that delivers the emails via multiple email-as-a-service backends based on a scoring algorithm described below. This project is done in response to the Uber code challenge and is for the backend track. Sendgrid and Mandrill is currently being used.

The service provides a simple interface to send a single email at a time. A more advanced interface could be added that allows for managing lists of receivers, bulk transmission, delivery/opening status and so on. However, these features was deemed out of scope for this project.

This project was made by [Martin Dam](https://www.linkedin.com/in/martinslothdam)

## Usage
A very simple web interface is provided to make it easy to test the service, however the main use case of this service is using the REST HTTP endpoints directly from another application.

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| /email   | POST   | Enqueue email for delivery. Accepts both JSON body and form data. Required fields: to, subject, content. Optional fields: to_name |
| /email/`<id>` | GET | Get the status of the email posted via /email. Returns JSON object describing the status including potential failure if delivery was not possible within 3 attempts. |

Emails are sent asynchronously. When an email is enqueued via the `/email` endpoint, a task is posted to one of the workers and eventually delivered. An emailId is returned which can be used to get the status of the email.

[Link to deployed service](http://emailservice.martindam.dk)

## Architecture
The system is built in Python and split into a web frontend and a backend of workers responsible for sending the emails. [Celery](http://www.celeryproject.org/) is used as a distributed task queue to send task and results between the frontend and backend. This architecture allows to scale the system as the number of workers can be scaled independent of the frontend and vice versa. RabbitMQ is used as the task queue as it provides good delivery guarantees as it keeps state about the clients and supports selective acknowledgement and re-delivery. Redis is used for the result backend as result are looked up by key. Configuration for the task queue and result backend can be found in [celereconfig.py](celeryconfig.py).

The webservice is based on [Flask](http://flask.pocoo.org/docs/0.11/api/).

Prior to this project, I had very little experience with Python except some smaller scripts and no experience with Celery. I was aware about RabbitMQ and Redis, but only used it very little previously. I have extensive experience with Kubernetes and Docker.

## Service selection strategy
The services are selected based on a continous score that is calculated for the service independently on each worker.
When a service failure is detected (server, authentication or too many request exceptions), the score for the service is exponential degraged (with a factor of 0.9). This will result in the score going down until another service is selected as the primary service. Over time the score will linearly (5 min) go back to its base score if it is not used or there are no more errors. When the service is no longer experiencing degraded performance, the service score will slowly restore to its base score and again become the primary service. See the algorithm in [mailservice.py](micromailer/mailservice.py). See [figure](docs/backoff_alg_single.png) on how the algorithm work for a single service.

[Simulations](tests/backoff_all_simulate.py) of this algorighm and the selection of the service with the highest score reveals significant error rate reduction under various service degradation patterns compared to a simple random service selection. See figure below. Note: Failures in this context is the failure to deliver an email to a single service, however the dispatcher falls back to the secondary service in this case and still delivers the email.

![Service score selection algorithm simulation](docs/backoff_alg_withalternative.png)

## Running locally
To run locally, install the dependencies using
```
pip install -r requirements.txt
```

The webservice can then be run with `python webservice.py` and the worker with `celery worker -A tasks`. For local testing, the configuration defaults to a redis instance without password which can be started with `redis-server`.

## Building
To deploy the project, the docker images have to be built. This can be done with:
```
docker build -t gcr.io/emailservice-144105/emailservice:<version> .
cd nginx
docker build -t gcr.op/emailservice-144105/nginx:<version> .
```
and then pushed to the gcloud docker registry.

## Testing
Various unit tests and an integration tests are implemented in [tests](tests/). Run with:
```
cd tests
python run_all.py
```

## Deployment
This repository includes the deployment specification for running on Kubernetes on Google Cloud Platform. Besides deploying the web service and workers, this specification also deploys a 2 node RabbitMQ cluster with persistent disk and a 1 node redis in-memory only cluster. The clusters are deployed with minimum configuration for demonstration purposes and may require tuning for production workload (e.g. TLS and virtual hosts).

**RabbitMQ**
When setting up RabbitMQ initially some steps needs to be taken to create the cluster. When both the nodes are up, do a `rabbitmqctl join_cluster <other node>` on one node to create the cluster. The default user `guest` should be removed and replaced with an administrator and emailservice user.

**Nginx**
The webservice has nginx running in front of the Python flask application. This has various advantages like security (nginx is argurably a better implementation of HTTP than Flask), SSL management if needed, offloading of static files, authentication and so on.

**Configs**
In order to deploy on Kubernetes, a configmap will need to be manually deployed with various configurations. See example below
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: emailservice-config
  namespace: default
data:
  sendgrid-api-key: 
  mandrill-api-key: 
  celery-broker-url: amqp://guest:guest@rmq1-1:5672/
  celery-result-backend: redis://redis-master/
```

## Production readiness
This project is made to be ready for production and large scale load:
 - Monitoring: System level monitoring is handled by Heapster in Kubernetes and Google StackDriver. Service monitoring is done with [Flower](http://flower.readthedocs.io/en/latest/). Flower is only internally available.
 - Logging: All docker containers logs to stdout/stderr and is captured by Fluentd and available in Google Cloud Platform logging infrastrucutre

## Improvements
The following improvements should/could be made:
 - Do not use Pickle as serialization for the task queue. Pickle is going to be deprecated in Celery 3.2 due to security concerns so switch to use JSON or similar on the task queue
 - Improve the initial cluster bootstrapping of RabbitMQ so it does not require manual steps
 - Add healthcheck to services to let Kubernetes re-deploy if they fail
 - Make a proper build system that runs tests before building the docker images
 - Add service specific tracking so the email services health score and other metrics are available for analysis and alerting.
 - Add authentication and auditing

