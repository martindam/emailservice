import context
import unittest
import mock
import json

import requests

from micromailer.models import Email
from micromailer.mandrill import MandrillMailService
from micromailer import mailservice


class MockResponse(requests.Response):

    def __init__(self, body):
        super(MockResponse, self).__init__()
        self._body = body

    @property
    def text(self):
        return self._body


class MandrillMailServerTestSuite(unittest.TestCase):

    def get_email(self, name=None):
        return Email("valid@email.com", "anothervalid@email.com", "Subject", "Content", to_name=name)

    @mock.patch('requests.post')
    def test_send_single_email(self, mock):
        response = MockResponse(json.dumps([{"status": "sent", "email": "valid@email.com"}]))
        response.status_code = 200
        mock.return_value = response

        service = MandrillMailService("api")
        email = self.get_email()
        result = service.send(email)

        assert mock.called
        request_body = mock.call_args_list[0][1]['json']
        assert request_body["key"] == "api"
        assert request_body["message"]["to"][0]["email"] == "valid@email.com"
        assert request_body["message"]["text"] == email.content
        assert request_body["message"]["subject"] == email.subject

        assert 'valid@email.com' in result
        assert result['valid@email.com']

    @mock.patch('requests.post')
    def test_send_single_email_withname(self, mock):
        response = MockResponse(json.dumps([{"status": "sent", "email": "valid@email.com"}]))
        response.status_code = 200
        mock.return_value = response

        service = MandrillMailService("api")
        service.send(self.get_email("John"))

        assert mock.called
        request_body = mock.call_args_list[0][1]['json']
        assert request_body["key"] == "api"
        assert request_body["message"]["to"][0]["name"] == "John"

    @mock.patch('requests.post')
    def test_server_failure(self, mock):
        response = requests.Response()
        response.status_code = 500
        mock.return_value = response

        service = MandrillMailService("api")
        with self.assertRaises(mailservice.ServerException):
            service.send(self.get_email())

    @mock.patch('requests.post')
    def test_network_failure(self, mock):
        mock.side_effect = requests.exceptions.ConnectionError()

        service = MandrillMailService("api")
        with self.assertRaises(mailservice.NetworkException):
            service.send(self.get_email())


if __name__ == '__main__':
    unittest.main()
