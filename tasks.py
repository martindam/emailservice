from celery import Celery
from celery.bin import worker

from micromailer.dispatcher import MailDispatcher
from micromailer.sendgrid import SendGridMailService
from micromailer.mandrill import MandrillMailService
from micromailer.mailservice import MailServiceException

from emailservice_config import MANDRILL_API_KEY, SENDGRID_API_KEY

celeryApp = Celery(__name__)
celeryApp.config_from_object('celeryconfig')

# Create mail dispatcher instance
dispatcher = MailDispatcher()
if SENDGRID_API_KEY is not None:
    dispatcher.add_service(SendGridMailService(SENDGRID_API_KEY))
if MANDRILL_API_KEY is not None:
    dispatcher.add_service(MandrillMailService(MANDRILL_API_KEY))


@celeryApp.task(name="micromailer.sendEmail", bind=True)
def send_email(self, email):
    try:
        return dispatcher.send(email)
    except MailServiceException as exc:
        # Retry on mail service exceptions.
        raise self.retry(exc=exc, countdown=10)


# Make it easier to run for debugging
if __name__ == '__main__':
    worker = worker.worker(app=celeryApp)

    options = {
        'loglevel': 'DEBUG',
        'traceback': True
    }

    worker.run(**options)
