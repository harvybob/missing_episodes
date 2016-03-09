# missing_episodes
Look at kodi mysql database and find all episodes, check against TVDB

Couple of settings needed:

1) provide mysql details to line 29 - host/ip of where mysql is, user, pass, current kodi video schema

2) Set if you wish to see specials - N for No, Y for yes (line 17)

3) Set single show to Y/N - If Yes it will only check one show based on id provided on line 166. - This is really to test


You will need mysqldb installed on the pi
sudo apt-get update
sudo apt-get install python-mysqldb

Once setup, make sure that the kodi library is up to date, and clean to remove any extra entries for removed media.

Once setup run with:

python missing_episodes.py 

for output to screen.
