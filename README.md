# PIX-Module

PIX dedicated decoupled module. The goal is create a module that can be used on any project to integrate PIX transactions and control.

## Docs

[Modobank API Documentation](https://developers.onz.software/reference/qrcodes/) <br>

## Estrutura do diretório raiz

```
samples/
├── requests/                   # Modobank QR Codes API request examples
│   └── create_immediate.json       
├── responses/                  # Modobank QR Codes API response examples
│   └── create_immediate.json
├── modobank.py                 # Modobank Pix module main file
├── exceptions.py               # Modobank Pix module exceptions
├── test.py                     # Implementation example
├── postman_collection.json     # Modobank Pix API postman collection provided by ONZ Software
├── LICENSE                     # License
└── README.md                   # Instructions and basic information
```

## Example usage

```python
from modobank import Modobank

credentials = {
    'client_id': 'client_id',
    'client_secret': 'client_secret',
    'certificate_crt': '/path/to/cert.crt/',
    'certificate_key': '/path/to/cert.key/',
    'receiver_pix_key': 'receiver_pix_key'
}

psp = Modobank(credentials)

response = modobank.create_immediate_charge(amount="1.00", cpf="44401970004", name="Foobar da Silva")

print(response)
```

