import os

# Setup broker for task communication
# In production this should be AMQP (and not redis) to avoid loosing tasks due to worker failure.
# For local testing, redis is the default
BROKER_URL = os.environ.get("BROKER_URL", "redis://localhost")

# Result backend: redis
# Use redis as results are looked up by key, are temporary and if lost it is non-critical
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost")

# Default queue to send tasks. Should be unique if the RabbitMQ service is shared with other applications
CELERY_DEFAULT_QUEUE = "mailservice"

# Store results for 3 hours with a maximum of 10M results. On redis this should stay within 8GB of memory
CELERY_MAX_CACHED_RESULTS = 10000000
CELERY_TASK_RESULT_EXPIRES = 10800

# Only acknowledge tasks AFTER they have been executed. Setting this to False could loose a task
# Note: This may result in duplicate emails being delivered as micromailer is not idempotent
CELERY_ACKS_LATE = True
