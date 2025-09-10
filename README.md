# PIX-Module

PIX dedicated decoupled module. The goal is create a module that can be used on any project to integrate PIX transactions and control.


## Docs

[Modobank API Documentation](https://developers.onz.software/reference/qrcodes/) <br>
[FasAPI()](https://fastapi.tiangolo.com/reference/fastapi/#fastapi.FastAPI) <br>
[psycopg](https://www.psycopg.org/docs/usage.html) <br>

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
│   │   └── modobank.py             # chamada Modobank API
│   ├── store/
│   │   ├── db.py                   # funções de query e conexão à base de dados
│   │   └── repository.py           # modelagem do banco de dados
│   ├── main.py                     # ponto de entrada da aplicação
│   ├── config.py                   # credenciais e database URL
│   └── container.py                # banco de dados, psp
├── tests/
│   ├── create_user                 # curl script para testar criação de usuários
│   ├── create_immediate_charge     # curl script para testar criação de cobranças
│   ├── detail_immediate_charges    # curl script para testar detalhamento de cobranças
│   └── create_webhook              # curl script para criar um webhook
├── launch                          # script pra iniciar o server
├── requirements.txt                # dependências
├── LICENSE                         # licença
└── README.md                       # instruções
```
