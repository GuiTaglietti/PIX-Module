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

response = modobank.create_webhook(txid="345b9f42df4d13a2585822a3247a65")


print(response)
