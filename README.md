# telegram_mailing
Parsing people from People Nearby function and mailing them via Telegram API

REQUIREMENTS:
  - telethon
  - numpy
  - pandas

INSTALLATION:
1. Clone the repository
2. Enable the virtual environment(tg_mail directory). Or create your own one with command python -m venv <venv_name>. Activate it by running start bin/activate. Then install the required libs with: pip install <library_name>
3. Start program:
python telegram_app.py <task> <stopputin_dataset>

  Possible tasks:
  - spam
  - parse
  - group(In development)
  - count

<stopputin_dataset> example is provided here: Data/stopputin260420.html

So the eventual example command would be:
  
  python telegram_app.py parse Data/stopputin260420.html

  
PROJECT STRUCTURE:
  - telegram_app.py contains all the functions. It is the main script.
  - start_gnome_client.sh is a shell script which is run by telegram_app.py to create a separate gnome-terminal window with working client (Gnome-terminal is a command line in linux). It is provided with all parameters by telegram_app.py
  - create_client_window.py is run by start_gnome_client.sh to begin the work ( It should be named as run_client.py and I will rename it later :) ) 
  - create_session.py is a simple script which is run to initialize a session and create a session file
  - all the logs are saved in logs directory. (I should work on them a little bit more. They seem to be not finished)
  - Data directory contains cities_people_parsed(txt files with parsed people ids), stopputin.net downloaded file with all the data, and world_cities.csv (we use cities' coordinates from there)
  
WORK DESCRIPTION:
  1. telegram_app.py determines the task and the dataset
  2. telegram_app.py starts start_gnome_client.sh
  3. These separated terminal windows start create_client_window.py
