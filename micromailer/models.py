import re

# Simple regex to check the email is valid (is not correct in 100% of the cases)
email_pattern = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


class InvalidEmailArgument(Exception):

    def __init__(self, message):
        super(InvalidEmailArgument, self).__init__(message)


class Email():

    def __init__(self, to, sender, subject, content, content_type="text/plain", to_name=None, sender_name=None):
        self.to = [(to, to_name)]
        self.sender = sender
        self.sender_name = sender_name
        self.subject = subject
        self.content = content
        self.content_type = content_type

        self._allowed_content_types = ["text/plain", "text/html"]

        # Make sure the arguments are valid, if not raise an exception
        self.is_valid()

    def is_valid(self):
        # Validate to email
        if len(self.to) == 0:
            raise InvalidEmailArgument('No recipient supplied')

        for email in self.to:
            if email[0] is None or not email_pattern.match(email[0]):
                raise InvalidEmailArgument("Recipient %s is invalid" % email[0])

        # Validate sender email
        if self.sender is None or not email_pattern.match(self.sender):
            raise InvalidEmailArgument('Sender email is invalid')

        # Validate subject
        if self.subject is None or type(self.subject) is not str:
            raise InvalidEmailArgument("Subject has to be a string")

        # Validate content
        if self.content is None or type(self.content) is not str:
            raise InvalidEmailArgument("Content has to be a string")

        if self.content_type is None or type(self.content_type) is not str or self.content_type not in self._allowed_content_types:
            raise InvalidEmailArgument("Content-type has to be plain/text or text/html")

        return True

    def add_recipient(self, email, name=None):
        self.to.append((email, name))
