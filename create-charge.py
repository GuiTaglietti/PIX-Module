#!/usr/bin/env python3

from efipay import EfiPay
import argparse
import sys
import os
import json
import re


def parse_args():
    parser = argparse.ArgumentParser(
                description="Create a dynamic PIX charge"
            )
    parser.add_argument("-a", "--amount", help="specifies the value to be paid")
    parser.add_argument("-p", "--print-response", help="print the response to stdout", action='store_true') #TODO
    parser.add_argument("-v", "--verbose", help="be verbose", action='store_true') # TODO
    parser.add_argument("-t", "--test-args", help="list provided arguments", action='store_true')
    args = parser.parse_args()
    
    if not args.amount and not args.test_args:
        parser.print_help()
        sys.exit(1)

    if args.test_args:
        print(args)
        sys.exit(0)
    
    return args


def get_api_keys():
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


def main():
    args = parse_args()

    # TODO: make this a function
    amount_pattern = r"^[0-9]{1,10}\.[0-9]{2}$"
    if not re.fullmatch(amount_pattern, args.amount):
        print("amount should be \"^[0-9]{1,10}\\.[0-9]{2}$\"")
        exit(1)
    else:
        amount = str(args.amount)
  
    api_keys = get_api_keys()

    credentials = {
        'client_id': api_keys['API_CLIENT_ID'],
        'client_secret': api_keys['API_CLIENT_SECRET'],
        'sandbox': True,
        'certificate': api_keys['API_CERTIFICATE_PATH']
    }

    efi = EfiPay(credentials)

    body = {
        'calendario': {
            'expiracao': 3600
        },
        'devedor': {
            'cpf': '18563601059',
            'nome': 'Foobar da Silva'
        },
        'valor': {
            'original': str(amount)
        },
        'chave': '03109929074',
        'solicitacaoPagador': 'Cobrança dos serviços prestados.'
    }

    response =  efi.pix_create_immediate_charge(body=body)
    fmt_response = json.dumps(response, indent=4, ensure_ascii=False, sort_keys=False)
    print(fmt_response)


if  __name__ == "__main__":
    main()
