#!/usr/bin/env python3

import requests
import os
import json
import re
from datetime import datetime, timezone
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Pix:
    def __init__(self):
        self.api_keys = self._get_api_keys()
        self.certificate = (self.api_keys['API_CRT_PATH'], self.api_keys['API_KEY_PATH'])
        self.domain = "https://v3.qrcodes.sulcredi.coop.br"
        self.bearer = self._auth()


    def _get_api_keys(self) -> dict:
        """
        Get the API keys from the OS environment variables

        Returns:
            API keys (dict): Client ID, Client Secret and Certificate
        """
        api_keys = {
                'API_CLIENT_ID': os.getenv("MODOBANK_CLIENT_ID"),
                'API_CLIENT_SECRET': os.getenv("MODOBANK_CLIENT_SECRET"),
                'API_CRT_PATH': os.getenv("MODOBANK_CRT_PATH"),
                'API_KEY_PATH': os.getenv("MODOBANK_KEY_PATH")
                }

        ok = True
        for k,v in api_keys.items():
            if not v:
                print(f"{k} environment variable is not set")
                ok = False
        if not ok:
            # TODO: better erorr handling
            exit(1)

        return api_keys


    def _auth(self):
        # TODO: this is made to auth with EFI Pay API, needs to check if it works with Modobank API
        url = f"{self.domain}/oauth/token"

        data = {
            'client_id': self.api_keys['API_CLIENT_ID'],
            'client_secret': self.api_keys['API_CLIENT_SECRET'],
            'grant_type': 'client_credentials'
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(
            url,
            data=data,
            headers=headers,
            cert=self.certificate,
            verify=False
        )

        #self._save_to_file(filename="auth", response=response.text)
        # TODO: better return values instead of just returning the Bearer
        return response.text


    def _value_is_not_valid(self, value: str) -> bool:
        """
        Check if the value provided is not formatted accordingly with the regexp
        ^[0-9]{1,10}.[0-9]{2}$

        Args:
            value (str): String representing the value
        Return value:
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
    

    def _txid_format_is_valid(self, txid: str):
        # TODO: check if in Modobank API is the same pattern
        """
        Check if the value provided is not formatted accordingly with the regexp
        ^[a-zA-Z0-9]{26,35}$
        Args:
            txid (str): transaction ID to test
        Returns:
            True if matches, False otherwise
        """
        pattern = r"^[a-zA-Z0-9]{26,35}$"
        return bool(re.match(pattern, txid))


    def _to_rfc3339(self, date_string):
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


    def _save_to_file(self, filename: str, response: str):
        """
        Save a response to a log file at 'log/requests/'

        Args:
            filename (str): Name of the file to be saved
            response (str): JSON response
        """ 
        # TODO: this is ugly
        date = str(datetime.now()).replace(" ","-").replace(":","-")[:19]
        with open(f"log/requests/{filename}-{date}.json", "w") as f:
            f.write(response)


    def create_cob(self, value: str, pix_key: str, txid: str = ""):
        # TODO: txid handling
        """
        Create an immediate cob.

        Args:
            value (str): The value of the charge in BRL
            pix_key (str): Receiver PIX key
            txid: (str, optional): Transaction ID, default is PSP defined
        Returns:
            String request response 
        """
        if self._value_is_not_valid(value):
            # TODO: better error handling
            exit(1)
        
        # maybe this should not have "/api/"
        url = f"{self.domain}/api/v2/cob"

        # maybe Content-Type should be "application/json"
        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/x-www-form-urlencoded" 
       }

        payload = {
            "calendario": {
                "expiracao": 600
            },
            #"devedor": {
                #"cpf": "12345678909",
                #"nome": "Francisco da Silva"
            #},
            "valor": 
            {
                "original": value
                #"modalidadeAlteracao": 0
            },
            "chave": pix_key,
            "solicitacaoPagador": "Serviço realizado."
        }

        # maybe cert is not needed idk
        response =  requests.post(url, headers=headers, json=payload, cert=self.certificate)
        fmt_response = json.dumps(response, indent=4, ensure_ascii=False)
        # TODO: write better logs
        #self._save_to_file(filename="create_cob", response=fmt_response)

        # TODO: better return values
        return str(fmt_response)


    def list_cobs(self, inicio: str, fim :str) -> str:
        """
        List cobs between 'inicio' and 'fim'

        Args:
            inicio (str): yyyy-mm-dd-hh-mm-ss format timestamp of when to start looking for cobs
            fim (str): yyyy-mm-dd-hh-mm-ss format timestamp of when to stop looking for cobs
        Return value:
            Formatted JSON string of the request response
        """
        # maybe "/api" is not needed
        url = f"{self.domain}/api/v2/cob/"

        # maybe Content-Type is "application/x-www-form-urlencoded"
        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }

        payload = {
                "inicio": self._to_rfc3339(inicio),
                "fim": self._to_rfc3339(fim)
        }

        # maybe certificate is not needed idk
        response =  requests.get(url, headers=headers, params=payload, cert=self.certificate)
        fmt_response = json.dumps(response.json(), indent=4, ensure_ascii=False, sort_keys=False)
        # TODO: write better logs
        #self._save_to_file(filename="list_cobs", response=fmt_response)

        # TODO: return better values
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
            # TODO: better error handling
            exit(1)

        # maybe "/api/" is not needed
        url = f"{self.domain}/api/v2/cob/{txid}"

        headers = { 
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json"
        }

        # maybe certificate is not needed
        response = requests.get(url, headers=headers, cert=self.certificate)
        fmt_response = json.dumps(response.json(), indent=4, ensure_ascii=False, sort_keys=False)
        # TODO: write better logs
        #self._save_to_file(filename=f"detail-cob-{txid}", response=fmt_response)

        return str(fmt_response)

