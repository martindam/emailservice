from flask import Flask, request, Response
from celery.result import AsyncResult
from celery.exceptions import TimeoutError

from tasks import send_email
import json

app = Flask(__name__)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/email', methods=['POST'])
def add_email():
    return send_email.apply_async(("martinslothdam@gmail.com", "Test email", "Some content")).id


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
        return_object['exception'] = exception.message

    return Response(json.dumps(return_object), mimetype='application/json')

if __name__ == '__main__':
    app.run()
