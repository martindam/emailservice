# Micro email service

This project implements a simple HTTP email service that delivers the emails via multiple email-as-a-service backends based on a scoring algorithm described below. 

A very simple web interface is provided to make it easy to test the service, however the main usecase of this service is using the HTTP endpoint directly from another application.

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| /email   | POST   | Enqueue email for delivery. Accepts both JSON body and form data. Required fields: to, subject, content. Optional fields: to_name |
| /email/`<id>` | GET | Get the status of the email posted via /email |

[Link to deployed service](http://emailservice.martindam.dk)


## Architecture


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
 - Improve the initial cluster bootstrapping of RabbitMQ so it does not require manual steps
 
 ## Deployment
 This repository includes the deployment specification for running on Kubernetes on Google Cloud Platform. Besides deploying the web service and workers, this specification also deploys a 2 node RabbitMQ cluster with persistent disk and a 1 node redis in-memory only cluster. The clusters are deployed with minimum configuration for demonstration purposes and may require tuning for production workload (e.g. TLS and virtual hosts).

 **RabbitMQ**
 When setting up RabbitMQ initially some steps needs to be taken to create the cluster. When both the nodes are up, do a `rabbitmqctl join_cluster <other node>` on one node to create the cluster. The default user `guest` should be removed and replaced with an administrator and emailservice user.

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

**Nginx**
The webservice has nginx running in front of the Python flask application. This has various advantages like security (nginx is argurably a better implementation of HTTP than Flask), SSL management if needed, offloading of static files, authentication and so on.
