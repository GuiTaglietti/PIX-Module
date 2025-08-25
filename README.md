# PIX-Module

PIX dedicated decoupled module. The goal is create a module that can be used on any project to integrate PIX transactions and control.


## Docs

[Modobank API Documentation](https://developers.onz.software/reference/qrcodes/) <br>
[FasAPI()](https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI) <br>
[JinjaTemplates](https://jinja.palletsprojects.com/en/stable/) <br>
[Jinja x FastAPI](https://fastapi.tiangolo.com/advanced/templates/#install-dependencies) <br>
[psycopg](https://www.psycopg.org/docs/usage.html) <br>
[OAuth2](https://fastapi.tiangolo.com/tutorial/security/#openapi)

## Tutorial

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# or simply
./launch
```


## Estrutura do diretório raiz

```
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── router.py           # endpoint de criação e status de pagamento, webhook, usuários
│   ├── models/
│   │   └── schemas.py              # definição dos dados envolvidos nas requests
│   ├── services/
│   │   └── pix/
│   │       ├── modobank.py         # chamada Modobank API 
│   │       └── efipay.py           # chamada Efipay API (para testes)
│   ├── store/
│   │   ├── db.py                   # funções de query e conexão à base de dados
│   │   └── repository.py           # modelagem do banco de dados
│   ├── web/
│   │   └── templates/            
│   │       └── index.html          # página web root "/"
│   ├── main.py                     # ponto de entrada da aplicação
│   ├── config.py                   # credenciais atuais 'cp config_modobank.py config.py'
│   └── container.py                # banco de dados, psp, templates
├── tests/
│   │   └── config/
│   │       └── config_modobank.py  # credenciais Modobank e banco de dados
│   │       └── config_efipay.py    # credenciais Efipay e banco de dados
│   ├── api_create_user             # curl script para testar criação de usuários
│   └── api_create_cob              # curl script para testar criação de pagamentos
├── launch                          # script pra inicializar o server
├── todo                            # ripgrep p/ mostrar TODOs e NOTEs pelo código
├── requirements.txt                # dependências
├── LICENSE                         # licença
└── README.md                       # instruções
```
