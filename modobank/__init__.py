# encoding: utf-8
"""
Modobank Python SDK
Python library for integrating with Modobank API for PIX payments
"""
from .modobank import Modobank

from .exceptions import (
    ModobankError,
    AuthenticationError,
    AmountError,
    TxidError,
    ChargeError,
    DateError,
    WebhookError
)

__version__ = "1.0.0"
__author__ = "Guilherme Ganassini, Guilherme Taglietti"
__email__ = "gdganassini@inf.ufpel.edu.br"

__all__ = [
    "Modobank",
    "ModobankError",
    "AuthenticationError",
    "AmountError",
    "TxidError",
    "ChargeError",
    "DateError"
]
