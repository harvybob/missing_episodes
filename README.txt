missing_episodes.py

This script will use the mysql database used by KODI and compare tv series to the TVDB listings
It will then return a list of episodes which are duplicated,
and more importantly, any episodes which are missing.

mysqldb must be installed first...

sudo apt-get install python-mysqldb

Couple of things are needed to be configured first.

Using the example_config_missing.ini, change the following:

ip - this should be the ip address that the mysql database resides in
name - the username that kodi uses to connect to mysql
pass - the password that kodi uses to connect to mysql
schema - this is the current kodi schema (as of version 14 video90)


Optional:
if you want to see specials as well:
change specials: N 
to
specials: Y


If you only want to check for a single series:
set single_show: N
to
single_show: Y

You will also need to add the value into the Others section.
You can easily find this by going to thetvdb.com and search for the series of intrest

Add the series into series_id



The last item of config is skip_list.
If there are series which you no longer want to check (say you only wanted a few episodes out of the full series)
add the series id's into the skip_list.
format must be 'id','id'



The script needs thetvdbapi.py to do the lookup.


To run, just execute as a python code:
python missing_episodes.py

output will go to screen.
If you want to push to a file then do:

python missing_episodes.py > file.log
