#v1.7 - using config file
#v1.6 - message if name not returned skip, to investigate further
#v1.5 - put logging back in
#v1.4 - includes a check for current date, and only looks at episodes that are prior to today
#v1.3 - highlight duplicates
#v1.2 - exclude specials from output if not wanted
#v1.1 - included ability to check single show 
#v1.0 - look up of tvdb and kodi for series, and removes teh kodi ones from the tvdb


from thetvdbapi import *
import MySQLdb as mdb
import time as time
import datetime
import ConfigParser
import logging

Config = ConfigParser.ConfigParser()
Config.read("./config_missing.ini")
Config.sections()

def ConfigSectionMap(section):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1

serverip = ConfigSectionMap("SectionOne")['ip']
username = ConfigSectionMap("SectionOne")['name']
userpass = ConfigSectionMap("SectionOne")['pass']
schema = ConfigSectionMap("SectionOne")['schema']


tvdb_list = []
kodi_list = []
series_list = []
current_show_name = ""
specials = ConfigSectionMap("SectionTwo")['specials']
single_show = ConfigSectionMap("SectionTwo")['single_show']
todays_date=datetime.datetime.now().date()

logging.basicConfig(filename='./kodi_missing_errors.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger(__name__)





def select_sql(command):
    """Will execute a select command onto the pi schema on 192.168.1.100 and return the value"""
    
    try:
## host, userid, password, database instance
      con = mdb.connect(serverip, username, userpass, schema);
      cursor = con.cursor()
        
      sql = command
      cursor.execute(sql)
      return cursor.fetchall()
           
      con.close()

    except mdb.Error, e:
      logger.error(e)
      


def get_tvdb_details_for_series_id(series_id):
    
    global tvdb_list
    global current_show_name
    global todays_date
    
    logging.debug("looking for "+series_id)

    api_key = "AD9B5756BE643CEA"
    thetvdb = TheTVDB(api_key)
    print "Connecting to TVDB..."
    show = thetvdb.get_show_and_episodes(series_id)
    if thetvdb.get_show(series_id) is None:
        print "Name error, go to tvdb and put the series id in the url to find series."
        logging.info("No name for "+series_id+" was returned")
    else:
        show_name= thetvdb.get_show(series_id)
        current_show_name = show_name.name
    #print current_show_name
    
    for episode in show[1]:
        
        
        if episode.first_aired is None :
           # print "no date"
            tvdb_list.append((episode.season_number.zfill(2),episode.episode_number.zfill(2)))
        elif episode.first_aired < todays_date :
            #print episode.first_aired
        #print "S" + episode.season_number.zfill(2) + "E" + episode.episode_number.zfill(2) + " AD " + str(episode.first_aired)
            tvdb_list.append((episode.season_number.zfill(2),episode.episode_number.zfill(2)))
        #else :
             #print "future episode of "+ episode.season_number.zfill(2) + episode.episode_number.zfill(2)


def get_episodes_for_series_id(series_id):
    global kodi_list
# give list of all series and episodes based on tvdb show number
    
    kodi_episodes = select_sql("SELECT episode.c12 ,episode.c13 FROM episode,tvshow where tvshow.idShow=episode.idShow and tvshow.c12 = '"+series_id+"' order by episode.c12, episode.c13")
    for i in range(0,len(kodi_episodes)):
      #  print kodi_episodes[i][0].zfill(2),kodi_episodes[i][1].zfill(2)
        kodi_list.append((kodi_episodes[i][0].zfill(2),kodi_episodes[i][1].zfill(2)))


def clear_what_is_there():
    global tvdb_list
    global kodi_list
    
    #this loops through the tvdb_list and pulls out the series and episode for each item
    for i in range(0,len(kodi_list)):
        current=kodi_list.pop()
        series=current[0]
        episode=current[1]
        curr_len=len(tvdb_list)
        #print curr_len
        try:
            location = tvdb_list.index((series,episode))
        except ValueError:
            print "duplicate entry of Series: " + series +" Episode: "+ episode 
           # print "location is " + str(location)
            location = int(-1)
        
        if location >= 0 :
            tvdb_list.pop(location)
            curr_len=len(tvdb_list)
            #print curr_len
        
      


def get_series_ids():
    global series_list
    series_list = select_sql("SELECT tvshow.c12 FROM tvshow")

def missing(series_id):
    global current_show_name
    global specials
    
    for i in range(0,len(tvdb_list)):
        series_episode = tvdb_list.pop()
        season = series_episode[0]
        episode = series_episode[1]
        if specials <> "N":
            print "Season: "+ season + " Episode: "+ episode
        else: 
            if season > "00":
                print "Season: "+ season + " Episode: "+ episode
                
                


def main():
    global tvdb_list
    global kodi_list
    global series_list
    global single_show

    
    if single_show <> "Y":
  
        get_series_ids()
        skip_list = ConfigSectionMap("Others")['skip_list']  
        for i in range(0,len(series_list)):
            series_id=series_list[i][0]
            if series_id not in skip_list:
                get_episodes_for_series_id(series_id)
                get_tvdb_details_for_series_id(series_id)
                print "shows missing for: " +current_show_name + " show number: " + series_id
            #this loops through the tvdb_list and pulls out the series and episode for each item
                clear_what_is_there()
                missing(series_id)
                print 
                print
    else:
        series_id = ConfigSectionMap("Others")['series_id']
        get_episodes_for_series_id(series_id)
        get_tvdb_details_for_series_id(series_id)
        print "shows missing for: " +current_show_name + " show number: " + series_id
        #this loops through the tvdb_list and pulls out the series and episode for each item
        clear_what_is_there()
        missing(series_id)
        print 
        print



if __name__ == "__main__":
    main()
