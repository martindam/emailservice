from flask import Flask, request, Response
from celery.result import AsyncResult
from celery.exceptions import TimeoutError
import json

from tasks import send_email
from micromailer.models import Email

from emailservice_config import MAILSERVICE_SENDER_EMAIL, MAILSERVICE_SENDER_NAME

app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('index.html')


'''
Add en email to be sent by the system. This endpoints emits the task definition
so a Celery worker can deliver the email. A HTTP/200 indicates the task was
successfully queued in Celery, NOT the delivery of the email.
Returns the taskId (or emailId) that can be used to query for the status of the task
on the /email/<emailId> endpoint
'''
@app.route('/email', methods=['POST'])
def add_email():
    email = None
    if request.is_json:
        json_body = request.get_json()
        email = Email(json_body['to'], MAILSERVICE_SENDER_EMAIL,
                      json_body['subject'], json_body['content'],
                      sender_name=MAILSERVICE_SENDER_NAME)
    else:
        email = Email(request.form['to'], MAILSERVICE_SENDER_EMAIL,
                      request.form['subject'], request.form['content'],
                      sender_name=MAILSERVICE_SENDER_NAME)

    task_id = send_email.apply_async([email]).id
    return Response(json.dumps({'taskId': task_id}), mimetype='application/json')


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
