#!/usr/bin/env python3

import requests
import os
import json
import re
from datetime import datetime

class Pix:
    def __init__(self):
        self.api_keys = self._get_api_keys()
        self.domain = "https://secureapi.onz.finance"


    def _get_api_keys(self) -> dict:
        """
        Get the API keys from the OS environment variables

        Return value:
            API keys (dict): The API keys 
        """
        api_keys = {
                'API_CLIENT_ID': os.getenv("MODOBANK_CLIENT_ID"),
                'API_CLIENT_SECRET': os.getenv("MODOBANK_CLIENT_SECRET"),
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

    def _save_to_file(self, filename: str, response: str):
        """
        Save a response to a log file at 'log/requests/'

        Args:
            filename (str): Name of the file to be saved
            response (str): Response in formatted json
        """ 
        # TODO: this is ugly
        date = str(datetime.now()).replace(" ","-").replace(":","-")[:19]
        with open(f"log/requests/{filename}-{date}.json", "w") as f:
            f.write(response)


    def create_cob(self, value: str):
        # TODO: return value must be abstracted
        """
        Create an immediate charge.

        Args:
            value (str): The value of the charge in BRL
        Return value:
            Formatted json string of the HTTP response
        """
        if self._value_is_not_valid(value):
            exit(1)

        url = f"{self.domain}/api/v2/cob"
        headers = { 
            "Content-Type": "application/x-www-form-urlencoded" 
            "Authorization: Bearer no_aguardo" 
                   }
        payload = {
            "calendario": {
                "expiracao": 600
            },
            "valor": 
            {
                "original": value,
                "modalidadeAlteracao": 0
            },
            "chave": "03109929074",
            "solicitacaoPagador": "Serviço realizado."
        }

        response =  requests.post(url, headers=headers, params=payload)
        fmt_response = json.dumps(response, indent=4, ensure_ascii=False)
        self._save_to_file(filename="create_cob", response=fmt_response)

        return str(fmt_response)


    def list_cobs(self, inicio: str, fim :str) -> str:
        # TODO: date RFC 3339 regex
        # see: (https://www.rfc-editor.org/rfc/rfc3339.html#section-5.8)
        # TODO: return value must be abstracted
        """
        List the charges between 'inicio' and 'fim'

        Args:
            inicio (str): RFC 3339 formatted timestamp of when to start looking for charges
            fim (str): RFC 3339 formatted timestamp of when to stop looking for charges
        Return value:
            Formatted json string of the HTTP response
        """
        url = f"{self.domain}/api/v2/cob/"
        payload = {
                "inicio": "2025-07-19T00:00:00Z",
                "fim": "2025-07-19T23:59:00Z"
        }
        response =  requests.get(url, payload)
        fmt_response = json.dumps(response, indent=4, ensure_ascii=False, sort_keys=False)
        self._save_to_file(filename="list_cobs", response=fmt_response)

        return str(fmt_response)


    def detail_cob(self, txid: str) -> str:
        # TODO: txid regex?
        # TODO: return value must be abstracted
        """
        Detail a specific charge with the specified {txid}

        Args:
            txid (str): Transaction ID
        Return value:
            Formatted json string of the HTTP response
        """
        url = f"{self.domain}/api/v2/cob/{txid}"
        response = requests.get(url)
        fmt_response = json.dumps(response, indent=4, ensure_ascii=False, sort_keys=False)
        self._save_to_file(filename=f"{txid}", response=fmt_response)

        return str(fmt_response)

