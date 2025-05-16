# Django + Traction

## Configuração
Baseado no projeto: https://github.com/openwallet-foundation/acapy-controllers/tree/main/TractionIssuanceDemo


1. É necessário configurar o university/settings.py com informações da sua conta no `Traction`
```python
### ACAPY settings ###
TRACTION_TENANT_ID = ""
TRACTION_API_KEY = ""
TRACTION_CREDENTIAL_DEFINITION_ID = ""
```

2. Rodar o localserver e copiar o link para webhook das configurações do `Traction`. Se o localserver fechar, será necessário atualizar o traction com o novo link para que o webhooker continue funcionando. 

```bash 
lt --port 8000
your url is: https://URL_LOCALSERVER
```

3. Se for a primeira vez que está executando: 

```python
python manage.py makemigrations
python manage.py migrate
```

4. É possível criar um usuário na url 

`http://127.0.0.1:8000/register`

Com esse usuário será possível acessar a aplicação. 