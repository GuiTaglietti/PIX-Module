#!/usr/bin/env python3
#
# Just to test the API until the backend is ready

from pix.api import Pix
from sys import argv
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="Modobank Pix API Wrapper")
    parser.add_argument("-a", "--amount", help="specifies the value to be paid")
    parser.add_argument("-c", "--create-cob", help="create a new immediate cob of AMOUNT", action='store_true')
    parser.add_argument("-l", "--list-cobs", help="list last cobs", action='store_true')
    parser.add_argument("-i", "--inicio", help="date in yyyy-mm-dd-hh-mm-ss")
    parser.add_argument("-f", "--fim", help="date in yyyy-mm-dd-hh-mm-ss")
    parser.add_argument("-x", "--txid", help="consult cob by txid")
    parser.add_argument("-t", "--test-args", help="list provided arguments", action='store_true')
    args = parser.parse_args()
    
    if len(argv) == 1:
        parser.print_help()
        exit(1)
    if args.test_args:
        print(args)
        exit(0)
    if args.create_cob:
        if not args.amount:
            parser.print_help()
            exit(1)
    if args.list_cobs and (not (args.inicio and args.fim)):
        parser.print_help()
        exit(1)

    return args

def main():
    args = parse_args()
    pix = Pix()

    if args.list_cobs:
        response = pix.list_cobs(inicio=args.inicio, fim=args.fim)
        print(response)
        return
    elif args.txid:
        response = pix.detail_cob(args.txid)
        print(response)
        return
    else:
        response = pix.create_cob(args.amount, pix_key="03109929074")
        print(response)
        return
    

if  __name__ == "__main__":
    main()
