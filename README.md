# telegram_mailing
Parsing people from People Nearby function and mailing them via Telegram API

REQUIREMENTS:
  - telethon
  - numpy
  - pandas

INSTALLATION:
1. Clone the repository
2. pip install -r requirements.txt
3. Add your api key in telegram_app.py
4. Create a telegram session with create_session.py (for example: python create_session.py +123422353 0123432 thisIsk1ndaHasH#$%1023123 )
5. Start program:
python telegram_app.py <task> <stopputin_dataset> [<telegram group_id>]

  Possible tasks:
  - spam
  - parse
  - group
  - count

<stopputin_dataset> example is provided here: Data/stopputin260420.html

So the eventual example commands look like be:
  
  python telegram_app.py parse Data/stopputin260420.html
  python telegram_app.py spam Data/stopputin260420.html
  python telegram_app.py count Data/stopputin260420.html
  python telegram_app.py group Data/stopputin260420.html 12332432
  
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
