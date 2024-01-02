import json

# Exemplo de dicionário
data_dict = {'channel': 20001, 'nickname': 'Alice', 'message': 'Olá, mundo!'}

# Converter o dicionário em uma string JSON
json_data = json.dumps(data_dict)

# Imprimir a string JSON
print(json_data)
