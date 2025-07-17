#!/usr/bin/env python3

from efipay import EfiPay
import os
import json
import re
from datetime import datetime

# TODO: this piece of code repeats a lot, make it a function
#               
#       efi = EfiPay(credentials)
#       response =  efi.pix_detail_charge(params=params)
#       fmt_response = json.dumps(response, indent=4, ensure_ascii=False, sort_keys=False)
#       self._save_to_file(filename=f"{txid}", response=fmt_response)
#
class Pix:
    def __init__(self):
        self.api_keys = self._get_api_keys()


    def _get_api_keys(self) -> dict:
        # TODO: write documentation
        api_keys = {
                'API_CLIENT_ID': os.getenv("EFI_CLIENT_ID"),
                'API_CLIENT_SECRET': os.getenv("EFI_CLIENT_SECRET"),
                'API_CERTIFICATE_PATH': os.getenv("EFI_CERTIFICATE_PATH")
                }

        ok = True
        for k,v in api_keys.items():
            if not v:
                print(f"{k} environment variable is not set")
                ok = False
        if not ok:
            exit(1)

        return api_keys

    
    def _amount_is_not_valid(self, amount: str) -> bool:
        # TODO: write documentation
        amount_pattern = r"^[0-9]{1,10}\.[0-9]{2}$"
        if not re.fullmatch(amount_pattern, amount):
            # TODO: seems weird to print it like that
            print("Amount should be '^[0-9]{1,10}\\.[0-9]{2}$'")
            return True
        else:
            return False

    def _save_to_file(self, filename: str, response: str) -> bool:
        # TODO: write documentation
        # TODO: this is very ugly
        date = str(datetime.now()).replace(" ","-").replace(":","-")[:19]
        with open(f"responses/{filename}-{date}.json", "w") as f:
            f.write(response)


    def make_cob(self, amount: str) -> str:
        # TODO: write documentation
        # TODO: i believe this should be a cobv not a cob
        if self._amount_is_not_valid(amount):
            exit(1)

        credentials = {
            'client_id': self.api_keys['API_CLIENT_ID'],
            'client_secret': self.api_keys['API_CLIENT_SECRET'],
            'sandbox': True,
            'certificate': self.api_keys['API_CERTIFICATE_PATH']
        }
        body = {
            'calendario': {
                'expiracao': 3600
            },
            'devedor': {
                'cpf': '18563601059',
                'nome': 'Francisco da Silva'
            },
            'valor': {
                'original': str(amount)
            },
            'chave': '1cdf9ba-c695-4e3c-b010-abb521a3f1be',
            'solicitacaoPagador': 'Cobrança dos serviços prestados.'
        }

        efi = EfiPay(credentials)
        response =  efi.pix_create_immediate_charge(body=body)
        fmt_response = json.dumps(response, indent=4, ensure_ascii=False, sort_keys=False)
        self._save_to_file(filename="make-cob", response=fmt_response)

        return str(fmt_response)


    def list_charges(self, inicio: str, fim :str) -> str:
        # TODO: write documentation
        # TODO: date fmt regex
        credentials = {
            'client_id': self.api_keys['API_CLIENT_ID'],
            'client_secret': self.api_keys['API_CLIENT_SECRET'],
            'sandbox': True,
            'certificate': self.api_keys['API_CERTIFICATE_PATH']
        }
        params = { 
                  'inicio': inicio,
                  'fim': fim
                  }

        efi = EfiPay(credentials)
        response =  efi.pix_list_charges(params=params)
        fmt_response = json.dumps(response, indent=4, ensure_ascii=False, sort_keys=False)
        self._save_to_file(filename="list-charges", response=fmt_response)

        return str(fmt_response)


    def detail_single_charge(self, txid: str) -> str:
        # TODO: write documentation
        # TODO: txid regex ?
        credentials = {
            'client_id': self.api_keys['API_CLIENT_ID'],
            'client_secret': self.api_keys['API_CLIENT_SECRET'],
            'sandbox': True,
            'certificate': self.api_keys['API_CERTIFICATE_PATH']
        }
        params = { 
                  'txid': txid 
                  }

        efi = EfiPay(credentials)
        response =  efi.pix_detail_charge(params=params)
        fmt_response = json.dumps(response, indent=4, ensure_ascii=False, sort_keys=False)
        self._save_to_file(filename=f"{txid}", response=fmt_response)

        return str(fmt_response)

