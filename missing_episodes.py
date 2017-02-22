# v1.13 - added series id on duplicates.
# v1.12 - fixed to work only with kodi 17 +  (db version 107)
# v1.11 - skip series special - episodes with show number 00
# v1.10 - only print show details if show has missing episodes
# v1.9 - added air date to output.
# v1.8 - error with unicodes, cast all string for output to unicode
# v1.7 - using config file
# v1.6 - message if name not returned skip, to investigate further
# v1.5 - put logging back in
# v1.4 - includes a check for current date
#        and only looks at episodes that are prior to today
# v1.3 - highlight duplicates
# v1.2 - exclude specials from output if not wanted
# v1.1 - included ability to check single show
# v1.0 - look up of tvdb and kodi for series,
#        and removes teh kodi ones from the tvdb


from thetvdbapi import *
import MySQLdb as mdb
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
missing_list = []
missing_ep_dict = {}
episode_date_dict = {}

current_show_name = ""
specials = ConfigSectionMap("SectionTwo")['specials']
single_show = ConfigSectionMap("SectionTwo")['single_show']
todays_date = datetime.datetime.now().date()

logging.basicConfig(filename='./kodi_missing_errors.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)


def select_sql(command):
    """Will execute a select command onto the pi schema and return the value"""

    try:
        # host, userid, password, database instance
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
    # print "Connecting to TVDB..."
    show = thetvdb.get_show_and_episodes(series_id)
    if thetvdb.get_show(series_id) is None:
        print "Name error, go to tvdb and put the series id in the url to find series."
        logging.info("No name for "+series_id+" was returned")
    else:
        show_name = thetvdb.get_show(series_id)
        current_show_name = show_name.name
    # print current_show_name
    for episode in show[1]:

        if episode.first_aired is None:
            # print "no date"
            tvdb_list.append((episode.season_number.zfill(2), episode.episode_number.zfill(2)))
            missing_ep_dict[(episode.season_number.zfill(2), episode.episode_number.zfill(2))] = episode.name
            episode_date_dict[(episode.season_number.zfill(2), episode.episode_number.zfill(2))] = episode.first_aired
        elif episode.first_aired < todays_date:
            # print episode.first_aired
            tvdb_list.append((episode.season_number.zfill(2), episode.episode_number.zfill(2)))
            missing_ep_dict[(episode.season_number.zfill(2), episode.episode_number.zfill(2))] = episode.name
            episode_date_dict[(episode.season_number.zfill(2), episode.episode_number.zfill(2))] = episode.first_aired


def get_episodes_for_series_id(series_id):
    global kodi_list
    # give list of all series and episodes based on tvdb show number
    #kodi_episodes = select_sql("SELECT episode.c12 ,episode.c13 FROM episode,tvshow where tvshow.idShow=episode.idShow and tvshow.c12 = '"+series_id+"' order by episode.c12, episode.c13")
    kodi_episodes = select_sql("select episode.c12 ,episode.c13 from episode,tvshow,uniqueid where tvshow.idshow=episode.idshow and tvshow.c12=uniqueid.uniqueid_id and uniqueid.media_type='tvshow' and uniqueid.value='"+series_id+"' order by episode.c12, episode.c13")
    
    for i in range(0, len(kodi_episodes)):
        kodi_list.append((kodi_episodes[i][0].zfill(2), kodi_episodes[i][1].zfill(2)))


def clear_what_is_there(series_id):
    global tvdb_list
    global kodi_list

    # this loops through the tvdb_list and pulls out
    # the series and episode for each item
    for i in range(0, len(kodi_list)):
        current = kodi_list.pop()
        series = current[0]
        episode = current[1]
        # print curr_len
        try:
            location = tvdb_list.index((series, episode))
        except ValueError:
            print "duplicate entry of Seriesid: " + series_id + \
                " Series: " + series + \
                " Episode: " + episode
            location = int(-1)

        if location >= 0:
            tvdb_list.pop(location)


def clear_specials():
    global tvdb_list
    global missing_list

    for i in range(0, len(tvdb_list)):
        current = tvdb_list.pop()
        series = current[0]
        episode = current[1]
        name = missing_ep_dict[(series, episode)]
        airdate = str(episode_date_dict[(series, episode)])
        if series != "00":
            if episode != "00":
                missing_list.append((series, episode, airdate, name))


def keep_specials():
    global tvdb_list
    global specials
    global missing_list

    for i in range(0, len(tvdb_list)):
        current = tvdb_list.pop()
        series = current[0]
        episode = current[1]
        name = missing_ep_dict[(series, episode)]
        airdate = str(episode_date_dict[(series, episode)])
        missing_list.append((series, episode, airdate, name))


def get_series_ids():
    global series_list
    series_list = select_sql("select uniqueid_value from tvshow_view")


def show_missing(series_id):
    global current_show_name
    global missing_list

    if len(missing_list) > 0:
        print "shows missing for: " + current_show_name + \
            " show number: " + series_id
        for i in range(0, len(missing_list)):

            series_episode = missing_list.pop()
            season = series_episode[0]
            episode = series_episode[1]
            airdate = series_episode[2]
            name = series_episode[3]
            print "Season: " + season.encode('utf-8') + " Episode: " + \
                episode.encode('utf-8') + " Aired Date: " + airdate.ljust(10) + \
                ", Name: " + name.encode('utf-8')
        print
        print
    del missing_list[:]


def main():

    global series_list
    global single_show
    if single_show != "Y":
        # Run if checking all shows
        get_series_ids()
        skip_list = ConfigSectionMap("Others")['skip_list']
        for i in range(0, len(series_list)):
            series_id = series_list[i][0]
            if series_id not in skip_list:
                get_episodes_for_series_id(series_id)
                get_tvdb_details_for_series_id(series_id)
            # this loops through the tvdb_list and pulls out
            # the series and episode for each item
                clear_what_is_there(series_id)
                if specials != "Y":
                    clear_specials()
                else:
                    keep_specials()
                show_missing(series_id)

    else:
        # Run if checking a single show
        series_id = ConfigSectionMap("Others")['series_id']
        get_episodes_for_series_id(series_id)
        get_tvdb_details_for_series_id(series_id)
        # this loops through the tvdb_list and pulls out
        # the series and episode for each item
        clear_what_is_there(series_id)
        if specials != "Y":
            clear_specials()
        else:
            keep_specials()
        print missing_list
        show_missing(series_id)
        print
        print


if __name__ == "__main__":
    main()