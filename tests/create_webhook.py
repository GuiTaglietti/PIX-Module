import os
from modobank import Modobank

credentials = {
    'client_id': os.getenv("MODOBANK_CLIENT_ID"),
    'client_secret': os.getenv("MODOBANK_CLIENT_SECRET"),
    'certificate_crt': os.getenv("MODOBANK_CRT_PATH"),
    'certificate_key': os.getenv("MODOBANK_KEY_PATH"),
    'receiver_pix_key': os.getenv("RECEIVER_PIX_KEY")
}

modobank = Modobank(credentials)

response = modobank.create_webhook(txid="b6189c0ef24eeaa30831e566b1bdd3")

print(response)
