#!/usr/bin/env python3
#
# Just to test the API until the backend is ready

from pix.api_modobank import Pix
from sys import argv
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Modobank Pix API Wrapper")
    # TODO: inicio/fim args
    parser.add_argument("-a", "--amount", help="specifies the value to be paid")
    parser.add_argument("-c", "--create-charge", help="create a new charge of AMOUNT", action='store_true')
    parser.add_argument("-l", "--list-charges", help="list last charges", action='store_true')
    parser.add_argument("-x", "--txid", help="consult charge by txid")
    parser.add_argument("-t", "--test-args", help="list provided arguments", action='store_true')
    args = parser.parse_args()
    
    if len(argv) == 1:
        parser.print_help()
        exit(1)
    if args.test_args:
        print(args)
        exit(0)
    if args.create_charge:
        if not args.amount:
            parser.print_help()
            exit(1)
    return args

def main():
    args = parse_args()
    pix = Pix()

    if args.list_charges:
        response = pix.list_cobs(inicio="2025-07-16T00:00:00Z", fim="2025-07-17T00:00:00Z")
        print(response)
        return
    elif args.txid:
        response = pix.detail_cob(args.txid)
        print(response)
        return
    else:
        response = pix.create_cob(args.amount)
        print(response)
        return
    

if  __name__ == "__main__":
    main()
