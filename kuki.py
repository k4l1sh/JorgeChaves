import requests
from googletrans import Translator
import re

def filtro_resposta(resposta):
    resposta = re.sub("kuki", "Jorge Chaves", resposta, flags=re.IGNORECASE)
    resposta = re.sub(re.compile("<.*?>"), "\n", resposta)
    resposta = Translator().translate(resposta, dest='pt').text
    return resposta

def kuki_request(texto):
    dados = {
        "input": Translator().translate(texto, dest='en').text,
        "botkey": "icH-VVd4uNBhjUid30-xM9QhnvAaVS3wVKA3L8w2mmspQ-hoUB3ZK153sEG3MX-Z8bKchASVLAo~",
        "channel": 7,
        "sessionid": 471594971,
        "client_name": "uuiprod-un18e6d73c-user-3247"
    }
    url = "https://icap.iconiq.ai/atalk"
    response = requests.post(url, dados).json()
    return list(map(filtro_resposta, response["responses"]))