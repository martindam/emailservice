import json
import requests
import logging
import mailservice


class BearerAuth(requests.auth.AuthBase):

    def __init__(self, token):
        self._token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer %s' % self._token
        return r


class SendGridMailService(mailservice.BackoffOnFailureMailServiceBase):

    def __init__(self, api_key, service_score=50):
        super(SendGridMailService, self).__init__(service_score)
        self._auth = BearerAuth(api_key)
        self._url = "https://api.sendgrid.com/v3/mail/send"

    def _do_send(self, msg):

        body = {
            "personalizations": [{"to": [{"email": x[0]}]} if x[1] is None else {"to": [{"email": x[0], "name": x[1]}]} for x in msg.to],
            "subject": msg.subject,
            "from": {"email": msg.sender} if msg.sender_name is None else {"email": msg.sender, "name": msg.sender_name},
            "content": [
                {
                    "type": msg.content_type,
                    "value": msg.content
                }
            ]
        }
        logging.debug("Sending email via sendgrid: %s" % json.dumps(body))

        # Perform HTTP request
        try:
            response = requests.post(self._url, json=body, auth=self._auth)

            if response.status_code >= 200 and response.status_code <= 299:
                output = self._build_success_response(msg)
                output['_response'] = response.text
                output['_service'] = 'sendgrid'
                return output
            elif response.status_code == 419:
                raise mailservice.TooManyRequests(response.text)
            elif response.status_code == 401:
                raise mailservice.UnauthorizedRequest(response.text)
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

    def _build_success_response(self, msg):
        output = {}
        for email in msg.to:
            output[email[0]] = True
        return output
