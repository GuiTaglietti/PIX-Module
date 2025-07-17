# PIX-Module
PIX dedicated decoupled module. The goal is create a module that can be used on any project to integrate PIX transactions and control.

## Links
[List of PSPs](https://github.com/bacen/pix-api/issues/76) <br>
[PSPs in non-compliance with the Pix API Regulation](https://github.com/bacen/pix-api/issues/560) <br>
[BR Code manual](https://www.bcb.gov.br/content/estabilidadefinanceira/spb_docs/ManualBRCode.pdf)

## EFÍ Bank API Pix
[Documentation](https://dev.efipay.com.br/docs/api-pix/credenciais/)
[Code examples](https://github.com/efipay/sdk-python-apis-efi/blob/main/examples/)

## Modobank API Pix
[Documentation](https://www.docs.pix.modobank.com/) <br>
[Para desenvolvedores](https://modobank.com/para-desenvolvedores/)

### Convert .p12 -> .pem
```sh
$ openssl pkcs12 -in certificado.p12 -out certificado.pem -nodes -password pass:""
```
