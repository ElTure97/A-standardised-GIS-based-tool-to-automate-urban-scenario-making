import pandas as pd
import glob
import os

# Definisci il percorso dei file CSV
percorso = 'ding0-output/759/*.csv'

# Ottieni la lista di tutti i file CSV nel percorso specificato
file_csv = glob.glob(percorso)

# Crea una lista vuota per memorizzare i DataFrame
dataframe_dict = {}

# Itera sui file CSV
for file in file_csv:
    # Leggi il file CSV e crea un DataFrame
    df = pd.read_csv(file)
    # Aggiungi il DataFrame alla lista
    nome_file = os.path.splitext(os.path.basename(file))[0]

    dataframe_dict[nome_file] = df



