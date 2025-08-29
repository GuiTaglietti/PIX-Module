# encoding: utf-8
from __future__ import unicode_literals

import re
import requests
from datetime import datetime, timezone, timedelta

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .exceptions import (
    AuthenticationError,
    AmountError,
    TxidError,
    ChargeError,
    DateError
)


class Modobank:
    def __init__(self, credentials: dict):
        self.api_keys = {
            "API_CLIENT_ID": credentials['client_id'],
            "API_CLIENT_SECRET": credentials['client_secret'],
            "API_CRT_PATH": credentials['certificate_crt'],
            "API_KEY_PATH": credentials['certificate_key'],
            "REC_PIX_KEY": credentials['receiver_pix_key'],
        }
        self.domain = "https://v3.qrcodes.sulcredi.coop.br"

        crt_path = self.api_keys['API_CRT_PATH']
        key_path = self.api_keys['API_KEY_PATH']

        if crt_path and key_path:
            self.certificate = (crt_path, key_path)
        else:
            self.certificate = None

        self.pix_key = self.api_keys['REC_PIX_KEY']
        self._bearer = None
        self._bearer_expires_at = None

    @property
    def bearer(self) -> str:
        """ 
        @property method -> self._bearer
        """
        if not self._bearer or self._is_token_expired():
            self._bearer = self._auth()
            self._bearer_expires_at = datetime.now(timezone.utc) + timedelta(seconds=300)
        return self._bearer


    def create_immediate_charge(self,
                         amount: str,
                         cpf: str,
                         name: str,
                         txid: str = "",
                         expiration: str = "600") -> dict:
        """ 
        Create an immediate charge

        Parameters:
            amount (str): amount to charge
            cpf (str): the CPF of the person requesting the charge
            txid (str, optional): optional txid
            expiration (str, optional): optional expiration
        Returns:
            (dict): the actual response of the Modobank API
        """
        if not self._amount_format_is_valid(amount):
            raise AmountError(404)

        # TODO: check if txid is "" in case the programmer wants to create an immediate with an specific txid

        url = f"{self.domain}/cob"

        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }

        data = {
            "calendario": {
                "expiracao": expiration
            },
            "devedor": {
                "cpf": cpf,
                "nome": name
            },
            "valor": {
                "original": amount
                },
            "chave": self.pix_key
        }

        try:
            # NOTE: read online this 'verify=False' is risky but it doesn't work without it
            response = requests.post(url, headers=headers, json=data, cert=self.certificate, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ChargeError(404)


    def list_immediate_charge(self, inicio: str, fim: str) -> dict:
        """ 
        List immediate charges between 'inicio' and 'fim'

        Parameters:
            inicio (str): date in 'yyyy-mm-dd-hh-mm-ss' lookup starting point
            fim (str): date in 'yyyy-mm-dd-hh-mm-ss' lookup date limit
        Returns:
            (dict): the actual response of the Modobank API
        """
        if not (self._date_format_is_valid(inicio) and self._date_format_is_valid(fim)):
            raise DateError(404)

        url = f"{self.domain}/cob/"

        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }

        payload = {
            "inicio": self._to_rfc3339(inicio),
            "fim": self._to_rfc3339(fim)
        }
        try:
            # NOTE: read online this 'verify=False' is risky but it doesn't work without it
            response = requests.get(url, headers=headers, params=payload, cert=self.certificate, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ChargeError(404)


    # NOTE: not tested after refactor
    def detail_immediate_charge(self, txid: str) -> str: # TODO: better typing
        """ 
        Details about an immediate charge associated with the txid provided

        Returns:
            (dict): the actual response of the Modobank API
        """
        if not self._txid_format_is_valid(txid):
            raise TxidError(404)

        url = f"{self.domain}/cob/{txid}"

        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }
        try:
            # NOTE: read online this 'verify=False' is risky but it doesn't work without it
            response = requests.get(url, headers=headers, cert=self.certificate, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ChargeError(404)


    def create_webhook(self, txid:str):
        # TODO: `create_webhook()` doc
        """
        Create a webhook for the payment associated with the txid provided.

        Parameters:
            txid (str): Transaction ID to monitor
        Returns:
        """
        if not self._txid_format_is_valid(txid):
            raise TxidError(404)

        url = f"{self.domain}/webhook/{txid}"

        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }

        try:
            # NOTE: read online this 'verify=False' is risky but it doesn't work without it
            response = requests.put(url, headers=headers, cert=self.certificate, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ChargeError(404)



    def _auth(self) -> str:
        """ 
        Modobank API OAuth authentication request

        Returns:
            (str): Bearer access token
        """
        url = f"{self.domain}/oauth/token"

        data = {
            'client_id': self.api_keys['API_CLIENT_ID'],
            'client_secret': self.api_keys['API_CLIENT_SECRET'],
            'grant_type': 'client_credentials'
        }

        headers = {'Content-Type': 'application/json'}
        
        try:
            # NOTE: read online this 'verify=False' is risky but it doesn't work without it
            response = requests.post(url, json=data, headers=headers, cert=self.certificate, verify=False)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.exceptions.RequestException as e:
            raise AuthenticationError(404)

    def _is_token_expired(self) -> bool:
        """ 
        Check if the Modobank Acess Token expired

        Returns:
            (bool): True if token expired, False otherwise
        """
        if not self._bearer_expires_at:
            return True
        return datetime.now() >= self._bearer_expires_at

    def _amount_format_is_valid(self, amount: str) -> bool:
        """ 
        Check if an amount is in '^[0-9]{1,10}\\.[0-9]{2}$' format

        Parameters:
            amount (str): amount string
        Returns:
            (bool): True if amount format is valid, False otherwise
        """
        pattern = r"^[0-9]{1,10}\.[0-9]{2}$"
        return bool(re.fullmatch(pattern, amount))

    def _txid_format_is_valid(self, txid: str) -> bool:
        """ 
        Check if txid format is in '^[a-za-z0-9]{26,35}$' format

        Parameters:
            txid (str): txid string
        Returns:
            (bool): True if txid format is valid, False otherwise
        """
        pattern = r"^[a-za-z0-9]{26,35}$"
        return bool(re.match(pattern, txid))

    def _date_format_is_valid(self, date_string: str) -> bool:
        """ 
        Check if date string is in format 'yyyy-mm-dd-hh-mm-ss'

        Parameters:
            date_string (str): string
        Returns:
            (bool): True if date format is valid, False otherwise
        """
        pattern = r'^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$'
        try:
            datetime.strptime(date_string, '%Y-%m-%d-%H-%M-%S')
            return bool(re.match(pattern, date_string))
        except ValueError:
            return False

    def _to_rfc3339(self, date_string: str) -> str:
        """ 
        Transform 'yyyy-mm-dd-hh-mm-ss' to RFC 3339

        Parameters:
            date_string (str): string in 'yyyy-mm-dd-hh-mm-ss'
        Returns:
            (str): the date string in RFC 3339
        """
        dt = datetime.strptime(date_string, '%Y-%m-%d-%H-%M-%S')
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc.isoformat()

