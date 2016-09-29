from celery import task, Celery
from celery.bin import worker

celeryApp = Celery(__name__)
celeryApp.config_from_object('celeryconfig')

@celeryApp.task(name="micromailer.sendEmail")
def send_email(to, subjet, body, cc=None, bcc=None, content_type="plain/text"):
    print "Sending email to %s" % (to)


# Make it easier to run for debugging
if __name__ == '__main__':
    worker = worker.worker(app=celeryApp)

    options = {
        'broker': 'redis://localhost',
        'loglevel': 'DEBUG',
        'traceback': True
    }

    worker.run(**options)
