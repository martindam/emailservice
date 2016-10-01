import json
import requests
import logging
import mailservice


class MandrillMailService(mailservice.BackoffOnFailureMailServiceBase):

    def __init__(self, api_key, service_score=50):
        super(MandrillMailService, self).__init__(service_score)
        self._api_key = api_key
        self._url = "https://mandrillapp.com/api/1.0/messages/send.json"

    def _do_send(self, msg):
        body = {
            "key": self._api_key,
            "async": False,
            "message": {
                "html" if msg.content_type == "text/html" else "text": msg.content,
                "subject": msg.subject,
                "from_email": msg.sender,
                "to": [{"email": x[0], "type": "to"} if x[1] is None else {"email": x[0], "name": x[1], "type": "to"} for x in msg.to]
            }
        }
        logging.debug("Sending email via sendgrid: %s" % json.dumps(body))

        # Perform HTTP request
        try:
            response = requests.post(self._url, json=body)

            if response.status_code >= 200 and response.status_code <= 299:
                return self._process_response(response.json())
            elif response.status_code >= 400 and response.status_code <= 499:
                raise mailservice.BadRequest(response.text)
            elif response.status_code >= 500 and response.status_code <= 599:
                raise mailservice.ServerException(response.text)
            else:
                raise mailservice.MailServiceException("Unexpected status code: %d" % response.status_code)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            raise mailservice.NetworkException(e.message)
        except requests.exceptions.RequestException as e:
            raise mailservice.ServerException(e.message)

    def _process_response(self, json_resp):
        output = {'_response': json_resp, '_service': 'mandrill'}
        for entry in json_resp:
            output[entry['email']] = entry['status'] in ['sent', 'queued', 'scheduled']
        return output
