import pandas as pd

data = pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vTH_cLTC9WWqvZaU_6MNuT1ReQvTp6nszF3rhzzpWzC78xm940Ykjo1_jcjByVbk47r2tR-FWpEUfRN/pub?gid=0&single=true&output=csv')
palavra = 'maomé'
if(data.COMANDO.isin([palavra]).any()):
    link = data.MP3[data.loc[data.isin([palavra]).any(axis=1)].index.tolist()[0]]
    print(link)