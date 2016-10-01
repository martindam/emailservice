import context
import unittest
import mock

import requests

from micromailer.models import Email
from micromailer.sendgrid import SendGridMailService
from micromailer import mailservice


class BackoffOnFailureMailServiceBaseTestSuite(unittest.TestCase):

    def get_email(self, name=None):
        return Email("valid@email.com", "anothervalid@email.com", "Subject", "Content", to_name=name)

    @mock.patch('requests.post')
    def test_send_single_email(self, mock):
        response = requests.Response()
        response.status_code = 200
        mock.return_value = response

        service = SendGridMailService("api")
        email = self.get_email()
        service.send(email)

        assert mock.called
        request_body = mock.call_args_list[0][1]['json']
        assert request_body['personalizations'][0]['to'][0]['email'] == "valid@email.com"
        assert request_body['content'][0]['value'] == email.content
        assert request_body['subject'] == email.subject

    @mock.patch('requests.post')
    def test_send_single_email_withname(self, mock):
        response = requests.Response()
        response.status_code = 200
        mock.return_value = response

        service = SendGridMailService("api")
        service.send(self.get_email("John"))

        assert mock.called
        request_body = mock.call_args_list[0][1]['json']
        assert request_body['personalizations'][0]['to'][0]['name'] == "John"

    @mock.patch('requests.post')
    def test_bearer_token(self, mock):
        response = requests.Response()
        response.status_code = 200
        mock.return_value = response

        service = SendGridMailService("api")
        service.send(self.get_email())

        req = mock.call_args_list[0][1]['auth'](requests.Request())
        assert req.headers['Authorization'] == 'Bearer api'

    @mock.patch('requests.post')
    def test_server_failure(self, mock):
        response = requests.Response()
        response.status_code = 500
        mock.return_value = response

        service = SendGridMailService("api")
        with self.assertRaises(mailservice.ServerException):
            service.send(self.get_email())

    @mock.patch('requests.post')
    def test_network_failure(self, mock):
        mock.side_effect = requests.exceptions.ConnectionError()

        service = SendGridMailService("api")
        with self.assertRaises(mailservice.NetworkException):
            service.send(self.get_email())


if __name__ == '__main__':
    unittest.main()
