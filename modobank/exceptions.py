# encoding: utf-8

class ModobankError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class AuthenticationError(ModobankError):
    def __init__(self, status):
        message = "{ 'Status': " + str(status) + ", 'Message': 'Could not authenticate.' } "
        super(AuthenticationError, self).__init__(message)

class AmountError(ModobankError):
    def __init__(self, status):
        message = "{ 'Status': " + str(status) + ", 'Message': 'Amount is not valid.' } "
        super(AmountError, self).__init__(message)

class TxidError(ModobankError):
    def __init__(self, status):
        message = "{ 'Status': " + str(status) + ", 'Message': 'txid is not valid.' } "
        super(TxidError, self).__init__(message)

class ChargeError(ModobankError):
    def __init__(self, status):
        message = "{ 'Status': " + str(status) + ", 'Message': 'Failed to create charge.' } "
        super(ChargeError, self).__init__(message)

class DateError(ModobankError):
    def __init__(self, status):
        message = "{ 'Status': " + str(status) + ", 'Message': 'Date format is not valid.' } "
        super(DateError, self).__init__(message)

class WebhookError(ModobankError):
    def __init__(self, status):
        message = "{ 'Status': " + str(status) + ", 'Message': 'Failed to create webhook.' } "
        super(WebhookError, self).__init__(message)
