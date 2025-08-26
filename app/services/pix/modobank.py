# app/services/pix/modobank.py
from __future__ import annotations
import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta
from app.config import Settings
from typing import Optional

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PixError(Exception):
    pass


class Modobank:
    def __init__(self, settings: Settings):
        self.api_keys = {
            "API_CLIENT_ID": settings.psp_client_id,
            "API_CLIENT_SECRET": settings.psp_client_secret,
            "API_CRT_PATH": settings.psp_crt_path,
            "API_KEY_PATH": settings.psp_key_path,
            "REC_PIX_KEY": settings.psp_pix_key,
        }
        self.domain = "https://v3.qrcodes.sulcredi.coop.br"

        crt_path = self.api_keys['API_CRT_PATH']
        key_path = self.api_keys['API_KEY_PATH']

        if crt_path and key_path:
            self.certificate = (crt_path, key_path)
        else:
            self.certificate = None

        self.pix_key = self.api_keys['REC_PIX_KEY']
        self._bearer: Optional[str] = None
        self._bearer_expires_at: Optional[datetime] = None

    @property
    def bearer(self) -> str:
        if not self._bearer or self._is_token_expired():
            self._bearer = self._auth()
            self._bearer_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return self._bearer


    def create_immediate(self, value: str, cpf: CPF, name: str, txid: str = "") -> dict:
        """ 
        Create an immediate charge

        Parameters:
            inicio (str): date in 'yyyy-mm-dd-hh-mm-ss' lookup starting point
            fim (str): date in 'yyyy-mm-dd-hh-mm-ss' lookup date limit
        Returns:
            (dict): the actual response of the Modobank API
        """
        if self._amount_is_not_valid(value):
            raise PixError("Invalid value format. Expected: '^[0-9]{1,10}\\.[0-9]{2}$'")

        # TODO: check if txid is "" in case the programmer wants to create an immediate with an specific txid

        url = f"{self.domain}/cob"
        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }
        data = {
            "calendario": {
                "expiracao": 600
            },
            "devedor": {
                "cpf": cpf,
                "nome": name
            },
            "valor": {
                "original": value
                },
            "chave": self.pix_key
        }
        try:
            # NOTE: read online this 'verify=False' is risky but it doesn't work without it
            response = requests.post(url, headers=headers, json=data, cert=self.certificate, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise PixError(f"Failed to create payment: {str(e)}")


    def list_immediate(self, inicio: str, fim: str) -> dict: # NOTE: not tested after refactor
        """ 
        List immediate charges between 'inicio' and 'fim'

        Parameters:
            inicio (str): date in 'yyyy-mm-dd-hh-mm-ss' lookup starting point
            fim (str): date in 'yyyy-mm-dd-hh-mm-ss' lookup date limit
        Returns:
            (dict): the actual response of the Modobank API
        """
        if not (self._date_format_is_valid(inicio) and self._date_format_is_valid(fim)):
            raise PixError("Date format should be yyyy-mm-dd-hh-mm-ss")

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
            raise PixError(f"Failed to list payments: {str(e)}")


    # NOTE: not tested after refactor
    def detail_immediate(self, txid: str) -> dict:
        """ 
        Details about an immediate charge associated with the txid provided

        Returns:
            (dict): the actual response of the Modobank API
        """
        if not self._txid_format_is_valid(txid):
            raise PixError("Invalid txid format")

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
            raise PixError(f"Failed to get payment details: {str(e)}")


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
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            # NOTE: read online this 'verify=False' is risky but it doesn't work without it
            response = requests.post(url, data=data, headers=headers, cert=self.certificate, verify=False)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.exceptions.RequestException as e:
            raise PixError(f"Authentication failed: {str(e)}")

    def _is_token_expired(self) -> bool:
        """ 
        Check if the Modobank Acess Token expired

        Returns:
            (bool): True if token expired, False otherwise
        """
        if not self._bearer_expires_at:
            return True
        return datetime.now() >= self._bearer_expires_at

    def _amount_is_not_valid(self, amount: str) -> bool:
        """ 
        Check if an amount is in a valid format

        Parameters:
            amount (str): amount string
        Returns:
            (bool): True if amount format is not valid, False otherwise
        """
        pattern = r"^[0-9]{1,10}\.[0-9]{2}$"
        return not bool(re.fullmatch(pattern, amount))

    def _txid_format_is_valid(self, txid: str) -> bool:
        """ 
        Check if txid format is valid

        Parameters:
            txid (str): txid string
        Returns:
            (bool): True if txid format is valid, False otherwise
        """
        pattern = r"^[a-zA-Z0-9]{26,35}$"
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

    def _save_to_file(self, filename: str, response: dict):
        """ 
        Vintage way to write logs

        Parameters:
            filename (str): name to be added to the file name
            response (dict): response to save
        """
        os.makedirs("logs", exist_ok=True)
        date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        with open(f"logs/{date}-{filename}.json", "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=4)
