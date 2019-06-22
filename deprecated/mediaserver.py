############################################################
####                All pysql functions                #####
############################################################

import psycopg2, logging
from psycopg2 import sql

## Set the logger and its level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def pysql_connect():
    '''Try to connection to the Video Station database server. '''
    
    try:
        conn = psycopg2.connect("dbname='mediaserver' user='postgres'")
    except psycopg2.Error as e:
        print(e)
        return (None,None)
    cur = conn.cursor()
    return (conn, cur)

def pysql_close(conn, cur):
    ''' Close the connection to the Video Station database server. '''
    cur.close()
    conn.close()

def pysql_add_file(conn, cur, media_infos):
    ''' Add the file if it does not exist already. '''

    try:
        ## Debugging
        logger.debug("INSERT INTO video (path, title, filesize, album, container_type, video_codec, frame_bitrate, frame_rate_num, frame_rate_den, video_bitrate, video_profile, video_level, resolutionX, resolutionY, audio_codec, audio_bitrate, frequency, channel, duration, date, mdate, fs_uuid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" %  (media_infos['path'], media_infos['title'], media_infos['filesize'], media_infos['album'], media_infos['container_type'], media_infos['video_codec'], media_infos['frame_bitrate'], media_infos['frame_rate_num'], media_infos['frame_rate_den'], media_infos['video_bitrate'], media_infos['video_profile'], media_infos['video_level'], media_infos['resolutionX'], media_infos['resolutionY'], media_infos['audio_codec'], media_infos['audio_bitrate'], media_infos['frequency'], media_infos['channel'], media_infos['duration'], media_infos['date'], media_infos['mdate'], media_infos['fs_uuid']))

        ## SQL Execution
        cur.execute(
            sql.SQL("INSERT INTO video (path, title, filesize, album, container_type, video_codec, frame_bitrate, frame_rate_num, frame_rate_den, video_bitrate, video_profile, video_level, resolutionX, resolutionY, audio_codec, audio_bitrate, frequency, channel, duration, date, mdate, fs_uuid) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"),
            (media_infos['path'], media_infos['title'], media_infos['filesize'], media_infos['album'], media_infos['container_type'], media_infos['video_codec'], media_infos['frame_bitrate'], media_infos['frame_rate_num'], media_infos['frame_rate_den'], media_infos['video_bitrate'], media_infos['video_profile'], media_infos['video_level'], media_infos['resolutionX'], media_infos['resolutionY'], media_infos['audio_codec'], media_infos['audio_bitrate'], media_infos['frequency'], media_infos['channel'], media_infos['duration'], media_infos['date'], media_infos['mdate'], media_infos['fs_uuid'])
        )
        conn.commit()

    except psycopg2.IntegrityError:
        logger.error("[-] Could not insert the new file, it already exists")
        return None
    return 0