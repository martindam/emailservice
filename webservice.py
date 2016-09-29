from flask import Flask, request, Response
from celery.result import AsyncResult
from tasks import send_email

app = Flask(__name__)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/email', methods=['POST'])
def add_email():
    return send_email.apply_async(("martinslothdam@gmail.com", "Test email", "Some content")).id

@app.route('/email/<emailId>', methods=['GET'])
def get_email_status(emailId):
    result = AsyncResult(id=emailId)
    print result.status
    if result.ready:
        # Task have been executed. Find the result
        print 'Task has result' + str(result.info)
        return str(result.result)
    else:
        return Response(status=204)


if __name__ == '__main__':
    app.run()
