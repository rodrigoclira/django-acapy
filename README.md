# Exemplo usando Django + Traction

Baseado no projeto: https://github.com/openwallet-foundation/acapy-controllers/tree/main/TractionIssuanceDemo


## Configuração

1. Crie o arquivo `.env` na pasta `university`. Esse arquivo deve seguir o modelo disponibilizado no arquivo `sample.env`. Você pode manter o valor das propriedades `TRACTION_API_BASE_URL` e o `CREDENTIAL_AUTO_ISSUE`. Contudo será necessário acessar sua conta do [Traction](https://traction-sandbox-tenant-ui.apps.silver.devops.gov.bc.ca/) para obter o valor de `TRACTION_TENANT_ID`, `TRACTION_API_KEY`, e
`TRACTION_CREDENTIAL_DEFINITION_ID`. O passo a passo para obter essas informações está no `README.md` do projeto: https://github.com/openwallet-foundation/acapy-controllers/tree/main/TractionIssuanceDemo#traction (Passos 1-21 da Seção traction). Isso será feito uma única vez.

```bash
### ENV ###
TRACTION_TENANT_ID=""
TRACTION_API_KEY=""
TRACTION_CREDENTIAL_DEFINITION_ID=""
TRACTION_API_BASE_URL="https://traction-sandbox-tenant-proxy.apps.silver.devops.gov.bc.ca"
CREDENTIAL_AUTO_ISSUE="False"
```

2. Execute o localserver. Caso não possua o localserver instalado, execute: `npm install -g localtunnel`. Em seguida, obtenha a URL pública:
> Caso essa configuração já tenha sido feita no Passo 1, siga para a execução do projeto (Passo 4).

```bash 
lt --port 8000
```

3. Copie a url indicada pelo localserver e salve-a na sua conta do Traction. Impotante: Se o localserver fechar, será necessário atualizar o Traction com a nova url para o webhooker continar funcionando. 


4. Após realizadas essas configurações, você pode fazer um dos seguintes comando na pasta raíz do repositório: 

```
docker-compose up --build
```

ou na pasta `university/`, após instalar as bibliotecas indicadas nos `requirements.txt`:

```
python manage.py runserver
````

5. Acesse a página inicial `http://127.0.0.1:8000`. Nela, você pode criar um novo usuário ou usar o usuário abaixo que já está armazenado na base.

```
usuário: rodrigo
password: 1234
```

## Criando uma base nova

Se você quiser criar uma nova base de dados, apague o arquivo da base atual `base.sqlite3`, se ele existir, e em seguida, execute:

```bash
python manage.py makemigrations
python manage.py migrate
```


