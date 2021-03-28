import requests
from google_trans_new import google_translator
import re

def filtro_resposta(resposta):
    resposta = re.sub("kuki", "Jorge Chaves", resposta, flags=re.IGNORECASE)
    resposta = re.sub(re.compile("<.*?>"), "\n", resposta)
    resposta = google_translator().translate(resposta,lang_tgt='pt')
    return resposta

def kuki_request(texto):
    dados = {
        "input": google_translator().translate(texto,lang_tgt='en'),
        "botkey": "icH-VVd4uNBhjUid30-xM9QhnvAaVS3wVKA3L8w2mmspQ-hoUB3ZK153sEG3MX-Z8bKchASVLAo~",
        "channel": 7,
        "sessionid": 471594971,
        "client_name": "uuiprod-un18e6d73c-user-3247"
    }
    url = "https://icap.iconiq.ai/atalk"
    response = requests.post(url, dados).json()
    return list(map(filtro_resposta, response["responses"]))