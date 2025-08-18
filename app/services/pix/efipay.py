# app/services/pix/efipay.py
from __future__ import annotations
import os
import re
import json
import requests
from datetime import datetime, timezone, timedelta
from app.config import Settings
from typing import Optional
from pydantic_br import CPF
import base64

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PixError(Exception):
    pass


class Efipay:
    def __init__(self, settings: Settings):
        self.api_keys = {
            "API_CLIENT_ID": settings.psp_client_id,
            "API_CLIENT_SECRET": settings.psp_client_secret,
            "API_PEM_PATH": settings.psp_pem_path,
            "REC_PIX_KEY": settings.psp_pix_key,
        }
        self.domain = "https://pix-h.api.efipay.com.br"

        pem = self.api_keys['API_PEM_PATH']
        if pem:
            self.certificate = pem
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

    def _is_token_expired(self) -> bool:
        if not self._bearer_expires_at:
            return True
        return datetime.now() >= self._bearer_expires_at

    def create_cob(self, value: str, cpf: CPF, name: str,txid: str = "") -> dict:
        if self._value_is_not_valid(value):
            raise PixError("Invalid value format. Expected: '^[0-9]{1,10}\\.[0-9]{2}$'")

        url = f"{self.domain}/v2/cob"
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
            response = requests.post(url, headers=headers, json=data, cert=self.certificate)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise PixError(f"Failed to create PIX payment: {str(e)}")

    def list_cobs(self, inicio: str, fim: str) -> dict: # TODO: this wat not tested in the new version yet
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
            response = requests.get(url, headers=headers, params=payload, cert=self.certificate, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise PixError(f"Failed to list PIX payments: {str(e)}")

    def detail_cob(self, txid: str) -> dict: # TODO: this wat not tested in the new version yet
        if not self._txid_format_is_valid(txid):
            raise PixError("Invalid txid format")

        url = f"{self.domain}/cob/{txid}"
        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers, cert=self.certificate, verify=False, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise PixError(f"Failed to get PIX payment details: {str(e)}")

    def _auth(self) -> str:
        credentials = { 
           "client_id": self.api_keys['API_CLIENT_ID'],
           "client_secret": self.api_keys['API_CLIENT_SECRET']
        }
        auth = base64.b64encode(
            (f"{credentials['client_id']}:{credentials['client_secret']}"
            ).encode()).decode()

        url = f"{self.domain}/oauth/token"
        data="{\r\n    \"grant_type\": \"client_credentials\"\r\n}"

        headers = {
          'Authorization': f"Basic {auth}",
          'Content-Type': 'application/json'
        }
        
        try:
            response = requests.request("POST", url, headers=headers, data=data,  cert=self.certificate)
            response.raise_for_status()
            return response.json()['access_token']
        except requests.exceptions.RequestException as e:
            raise PixError(f"Authentication failed: {str(e)}")

    def _value_is_not_valid(self, value: str) -> bool:
        pattern = r"^[0-9]{1,10}\.[0-9]{2}$"
        return not bool(re.fullmatch(pattern, value))

    def _txid_format_is_valid(self, txid: str) -> bool:
        pattern = r"^[a-zA-Z0-9]{26,35}$"
        return bool(re.match(pattern, txid))

    def _date_format_is_valid(self, date_string: str) -> bool:
        pattern = r'^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$'
        try:
            datetime.strptime(date_string, '%Y-%m-%d-%H-%M-%S')
            return bool(re.match(pattern, date_string))
        except ValueError:
            return False

    def _to_rfc3339(self, date_string: str) -> str:
        dt = datetime.strptime(date_string, '%Y-%m-%d-%H-%M-%S')
        dt_utc = dt.replace(tzinfo=timezone.utc)
        return dt_utc.isoformat()

    def _save_to_file(self, filename: str, response: dict):
        os.makedirs("logs", exist_ok=True)
        date = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        with open(f"logs/{date}-{filename}.json", "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=4)
