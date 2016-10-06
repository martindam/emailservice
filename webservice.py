from flask import Flask, request, Response
from celery.result import AsyncResult
from celery.exceptions import TimeoutError
import json
import logging
import markdown

from tasks import send_email
from micromailer.models import Email, InvalidEmailArgument

from emailservice_config import MAILSERVICE_SENDER_EMAIL, MAILSERVICE_SENDER_NAME

app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('index.html')


'''
Add en email to be sent by the system. This endpoints emits the task definition
so a Celery worker can deliver the email. A HTTP/200 indicates the task was
successfully queued in Celery, NOT the delivery of the email.
Returns the emailid that can be used to query for the status of the email
on the /email/<emailId> endpoint
'''
@app.route('/email', methods=['POST'])
def add_email():
    email = None
    if request.is_json:
        fields = request.get_json()
    else:
        fields = request.form

    try:
        email = Email(fields['to'], MAILSERVICE_SENDER_EMAIL,
                      fields['subject'], markdown.markdown(fields['content']),
                      content_type="text/html", sender_name=MAILSERVICE_SENDER_NAME,
                      to_name=fields.get('to_name', None))
    except InvalidEmailArgument as e:
        return Response(json.dumps({"status": "failed", "error": e.message}), status=400)

    email_id = send_email.apply_async([email]).id
    logging.debug("Enqueing email to %s with emailId=%s" % (email.to[0][0], email_id))
    return Response(json.dumps({"status": "queued", "emailId": email_id}), mimetype='application/json')


'''
Retrieve the status of an email. Returns an json object describing the status.
Until the task have been executed successfully or the maximum number of retries
have been reached, this will return "not found"
'''
@app.route('/email/<emailId>', methods=['GET'])
def get_email_status(emailId):
    return_object = {'status': 'unknown', 'emailId': emailId}
    try:
        task_result = AsyncResult(id=emailId)
        task_result.get(timeout=2, interval=0.1)

        # If the task raised an exception, the exception is re-raised here
        return_object['status'] = 'success'
        if task_result.info is not None:
            return_object['result'] = task_result.info

    except TimeoutError:
        return_object['status'] = 'notfound'
    except Exception as exception:
        return_object['status'] = 'failed'
        return_object['exception'] = json.loads(exception.message)

    return Response(json.dumps(return_object), mimetype='application/json')


if __name__ == '__main__':
    app.run()
