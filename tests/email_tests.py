import context
import unittest

from micromailer import email

class EmailTestSuite(unittest.TestCase):

    def test_invalid_email(self):
        with self.assertRaises(email.InvalidEmailArgument):
            email.Email("invalidEmail", "valid@email.com", "Subject", "Content")

    def test_invalid_from_email(self):
        with self.assertRaises(email.InvalidEmailArgument):
            email.Email("valid@email.com", "invalid", "Subject", "Content")

    def test_invalid_email2(self):
        with self.assertRaises(email.InvalidEmailArgument):
            email.Email(None, None, "Subject", "Content")

    def test_valid_email(self):
        e = email.Email("valid@email.com", "anothervalid@email.com", "Subject", "Content")
        self.assertIn("valid@email.com", [x[0] for x in e.to], "Receiver not set correctly")
        self.assertEqual(e.sender, "anothervalid@email.com", "Sender not set correctly")

    def test_invalid_content_type(self):
        with self.assertRaises(email.InvalidEmailArgument):
            email.Email(None, None, "Subject", "Content", "application/json")

    def test_add_recipient(self):
        e = email.Email("valid@email.com", "anothervalid@email.com", "Subject", "Content")
        e.add_recipient("anotheremail@valid.com", "With name")
        self.assertIn("anotheremail@valid.com", [x[0] for x in e.to], "Second receiver not added correctly")

if __name__ == '__main__':
    unittest.main()
