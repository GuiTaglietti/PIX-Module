#!/usr/bin/env python3

import requests
import base64
import os
import json
import re
from datetime import datetime, timezone

class Pix():
    def __init__(self, sandbox : bool = True):
        self.sandbox = sandbox
        self.api_keys = self._get_api_keys()
        self.certificate = self.api_keys['API_CERTIFICATE_PATH']
        self.domain = "https://pix-h.api.efipay.com.br" if sandbox else "https://pix.api.efipay.com.br"
        self.bearer = self._auth()


    def _get_api_keys(self) -> dict:
        """
        Get the API keys from the OS environment variables

        Returns:
            API keys (dict): The API keys 
        """
        env = "EFI_SANDBOX" if self.sandbox else "EFI_PROD"

        api_keys = {
            'API_CLIENT_ID': os.getenv(f"{env}_CLIENT_ID"),
            'API_CLIENT_SECRET': os.getenv(f"{env}_CLIENT_SECRET"),
            'API_CERTIFICATE_PATH': os.getenv(f"{env}_CERTIFICATE_PATH")
        }

        ok = True
        for k,v in api_keys.items():
            if not v:
                print(f"{k} environment variable is not set")
                ok = False
        if not ok:
            exit(1)

        return api_keys


    def _value_is_not_valid(self, value: str) -> bool:
        """
        Check if the value provided is not formatted accordingly with the regexp
        ^[0-9]{1,10}.[0-9]{2}$

        Args:
            value (str): String representing the value
        Returns:
            True -> If is not formatted accordingly
            False -> If is formatted accordingly
        """
        value_pattern = r"^[0-9]{1,10}\.[0-9]{2}$"
        if not re.fullmatch(value_pattern, value):
            # TODO: seems weird to print it like that
            print("Value should be '^[0-9]{1,10}\\.[0-9]{2}$'")
            return True
        else:
            return False


    def _save_to_file(self, filename: str, response: str):
        """
        Save a response to a log file at 'log/requests/'

        Args:
            filename (str): Name of the file to be saved
            response (str): Response in formatted json
        """ 
        date = str(datetime.now()).replace(" ","-").replace(":","-")[:19]
        with open(f"log/requests/efi/{filename}-{date}.json", "w") as f:
            f.write(response)

    
    def _date_format_is_valid(self, date_string):
        """
        Check if date string is in yyyy-mm-dd-hh-mm-ss format
        
        Args:
            date_string (str): Date string to validate
        Returns:
            bool: True if valid format, False otherwise
        """
        pattern = r'^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}$'
        if not re.match(pattern, date_string):
            return False
        
        try:
            datetime.strptime(date_string, '%Y-%m-%d-%H-%M-%S')
            return True
        except ValueError:
            return False


    def _to_rfc3339_utc(self, date_string):
        """
        Transform yyyy-mm-dd-hh-mm-ss format to RFC 3339
        
        Args:
            date_string (str): Date in format "yyyy-mm-dd-hh-mm-ss"
        Returns:
            str: RFC 3339 formatted date string in UTC
        """
        dt = datetime.strptime(date_string, '%Y-%m-%d-%H-%M-%S')
        dt_utc = dt.replace(tzinfo=timezone.utc)
        
        return dt_utc.isoformat()


    def _txid_format_is_valid(self, txid: str):
        """
        Check if the value provided is not formatted accordingly with the regexp
        ^[a-zA-Z0-9]{26,35}$
        Args:
            txid (str): transaction ID to test
        Returns:
            True if matches, False otherwise
        """
        pattern = r"^[a-zA-Z0-9]{26,35}$"
        return bool(re.match(pattern, s))


    def _auth(self):
        credentials = { 
           "client_id": self.api_keys['API_CLIENT_ID'],
           "client_secret": self.api_keys['API_CLIENT_SECRET']
        }
        
        auth = base64.b64encode(
            (f"{credentials['client_id']}:{credentials['client_secret']}"
            ).encode()).decode()

        url = f"{self.domain}/oauth/token"

        payload="{\r\n    \"grant_type\": \"client_credentials\"\r\n}"

        headers = {
          'Authorization': f"Basic {auth}",
          'Content-Type': 'application/json'
        }

        response = requests.request("POST",
                                    url,
                                    headers=headers,
                                    data=payload,
                                    cert=self.certificate)

        self._save_to_file(filename="auth", response=response.text)
        return response.json()['access_token']


    def create_cob(self, value: str, txid: str = ""):
        # TODO: return value must be abstracted
        # TODO: txid regex
        """
        Create an immediate cob.

        Args:
            value (str): The value of the charge in BRL
        Returns:
            Formatted json string of the HTTP response
        """
        if self._value_is_not_valid(value):
            exit(1)

        url = f"{self.domain}/v2/cob"

        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "calendario": {
                "expiracao": 600
            },
            "devedor": {
                "cpf": "12345678909",
                "nome": "Francisco da Silva"
            },
            "valor": {
                "original": value
            },
            "chave": "03109929074",
            "solicitacaoPagador": "Serviço realizado."
        }

        response =  requests.post(url, headers=headers, json=payload, cert=self.certificate)
        fmt_response = json.dumps(response.json(), indent=4, ensure_ascii=False)
        self._save_to_file(filename="create_cob", response=fmt_response)

        return str(fmt_response)


    def list_cobs(self, inicio: str, fim :str) -> str:
        # TODO: return value must be abstracted
        """
        List the charges between 'inicio' and 'fim'

        Args:
            inicio (str): RFC 3339 formatted timestamp of when to start looking for charges
            fim (str): RFC 3339 formatted timestamp of when to stop looking for charges
        Return value:
            Formatted json string of the HTTP response
        """
        if not (self._date_format_is_valid(inicio) and self._date_format_is_valid(fim)):
            print("Date format should be yyyy-mm-dd-hh-mm-ss")
            exit(1)

        url = f"{self.domain}/v2/cob/"

        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }

        payload = {
                "inicio": self._to_rfc3339_utc(inicio),
                "fim": self._to_rfc3339_utc(fim)
        }
        response =  requests.get(url, headers=headers, params=payload, cert=self.certificate)
        fmt_response = json.dumps(response.json(), indent=4, ensure_ascii=False, sort_keys=False)
        self._save_to_file(filename="list_cobs", response=fmt_response)

        return str(fmt_response)


    def detail_cob(self, txid: str) -> str:
        # TODO: return value must be abstracted
        """
        Detail a specific charge with the specified {txid}

        Args:
            txid (str): Transaction ID
        Return value:
            Formatted json string of the HTTP response
        """
        if not self._txid_format_is_valid(txid):
            # TODO: seems weird to print it like that
            print("txid format should be ^[a-zA-Z0-9]{26,35}$")
            exit(1)

        url = f"{self.domain}/v2/cob/{txid}"
        response = requests.get(url, cert=self.certficate)
        fmt_response = json.dumps(response.json(), indent=4, ensure_ascii=False, sort_keys=False)
        self._save_to_file(filename=f"{txid}", response=fmt_response)

        return str(fmt_response)

