import os
from telethon import TelegramClient
from telegram_app import accounts, client_spam, client_parse_cities, create_dataframe_stopputin, get_divided_work, client_create_group
import sys
import pandas as pd

#INITIALIZING PARAMETERS
# FORMAT: python create_client_window.py <phone> <task> [<split_n> <work_part>]
client_phone = sys.argv[1]
task = sys.argv[2] # "spam" / "parse" / "group"
if task == "parse":
    split_n = int(sys.argv[3])
    work_part = int(sys.argv[4])
    PROTESTS_FILE = sys.argv[5]
elif task == "spam" or task == "group":
    PROTESTS_FILE = sys.argv[3]
    split_n = None
    work_part = None
cwd = os.getcwd()

#EXECUTING
if __name__ == "__main__":
    cities_df = pd.read_csv('Data/worldcities.csv')
    stopputin_df = create_dataframe_stopputin(PROTESTS_FILE)
    print(stopputin_df)

    client = TelegramClient(client_phone, accounts[client_phone]['api_id'], accounts[client_phone]["api_hash"])
    try:
        if task == "parse":
            split_df = get_divided_work(stopputin_df, split_n)[work_part]
            client_parse_cities(client, client_phone, split_df, cities_df)
        elif task == "spam":
            client_spam(client, client_phone, stopputin_df)
        elif task == "group":
            client_create_group(client, client_phone, stopputin_df)
    except Exception as e: print("\nWARNING: ", e, "\n")