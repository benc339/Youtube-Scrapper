#############################
#README
#
#there are two functions:
#1. scrapping channels (and their videos from the last 3 months from current date) based on search phrases you specify
#2. exporting a list of the gathered videos based on more criteria you define (e.g. median views, video post freq)
#
# to connect to the program
# 1. if you're on windows to connect download and install putty: https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html
# if you have another os, let me know, I'll help you connect
# 2. run putty and enter: ec2-18-218-46-91.us-east-2.compute.amazonaws.com into the host name box
# 3. click on the + sign next to SSH on the bottom left
# 4. click on Auth
# 5. click Browse and load in dw_key.ppk 
# 6. click open
# 7. type ubuntu and the press enter

#to run the srapper:
#1. load search_phrases.txt with keyphrases you want the program to search against to find new channels:
#2. to delete the current list type: rm search_phrases.txt
#3. to edit the blank list type: vim search_phrases.txt
#4. copy your list (deliminated by new lines) and right click anywhere to paste
#5. to save the list type the following then press enter: :wq
#6. type python scrape.py and press enter to run the scrapper
#7. as it finds new channels it'll tell you for channels it finds then channel name, country, median views,
# number of videos in the last 3 months and number of videos in the last 3 months with one of your search phrases in the title or description
#if you want you can include a list of channels you don't want the program to waste time scrapping, add it to
# skip_channel_list.txt
#
# - if you run out of keys with gather quota, I can load in more, just ask me
# - if google bans you for abuse, just ask me, we'll just need to delete all the keys and add in a new list created by unlinked google accounts

#to run the exporter:
#1. load into check_phrases.txt key phrases separated by new lines for it to check how many videos have one of those key phrases
#2. load into skip_channel_list.txt channels you don't want it to export
#3. to edit the remaining criteria type: vim export.py
#4. at the top are the search queries e.g. (Channel.country == 'US') | (Channel.country == 'Not Found') & (Channel.videos_last_3_months > 10)
# & (Channel.median_views > 1000) & (Channel.general_makeup_phrase_videos > 5)
#5. to run the program type and press enter: python export.py
#6. the results will be saved in extract.txt
#
# to download extract.txt to your computer:
# 1. download pscp.exe and place in your putty installation folder e.g. (C:\Program Files\PuTTY)
# https://the.earth.li/~sgtatham/putty/latest/w64/pscp.exe 
# 2. run cmd  (press windows, type cmd, press enter)
# 3. type and press enter: cd C:\Program Files\PuTTY    (or your installation folder)
# 4. type and press enter: pscp.exe -i dw_key.ppk ubuntu@ec2-18-218-46-91.us-east-2.compute.amazonaws.com:/home/ubuntu/extract.txt C:\users\bence\documents\output.txt
# (change the 2nd folder to a folder on your computer)
#
################################

US_only = True
###########################

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
#####
######
import datetime
from tinydb import TinyDB, Query
DEVELOPER_KEY = open('current_key.txt').read().split()[0] #open('key2.txt').read().split()[0] #'AIzaSyCNwpK3VXG5aubU52di5RznPP1EJBiF0FI'

print DEVELOPER_KEY
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


skip_channel_list = open('skip_channel_list.txt').read().split('\n')
'''
import sys
def my_except_hook(exctype, value, traceback):
    print exctype
    print value
    print traceback

    current_key = open("current_key.txt").read().split()[0]
    print current_key
    keylist = open('api_keylist.txt').read().split('\n')
    next = False
    found = False
    for key in keylist:
      
        if len(key)<3:
            continue
        if next:
            open('current_key.txt','w').write(key)
            print 'found'
            global DEVELOPER_KEY
            DEVELOPER_KEY = key
            print DEVELOPER_KEY
            found = True
            break
        if key == current_key:
            next = True

    if not found:
        open('current_key.txt','w').write(keylist[0])
    sys.excepthook = my_except_hook
    start()
''' 

def get_channel_videos_before(channel_id,beforeDate):
        
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
	videoId_list={}
	videos = []
	if len(channel_id) < 20:
		response = youtube.channels().list(
						part = 'contentDetails',
		                forUsername = channel_id,
		                ).execute()
	else:
		response = youtube.channels().list(
						part = 'contentDetails',
		                id = channel_id,
		                ).execute()

	playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']


	
	response = youtube.playlistItems().list(
					part = 'snippet',
                    playlistId = playlist_id,
                    ).execute()
	#print response
	no_makeup_in_a_row=0
	low_views_in_a_row=0
	general_makeup_phrases = open('general_makeup_phrases.txt').read().split('\n')
	for video in response['items']:


		
		title = video['snippet']['title']
		videoId = video['snippet']['resourceId']['videoId']
		publishDate = video['snippet']['publishedAt']
		description = video['snippet']['description']
		phrase_found=False
                for keyphrase in general_makeup_phrases:
                    if keyphrase == '':
                        continue
                    
                    if keyphrase.lower() in title.lower() \
                       or keyphrase.lower() in description.lower():
                        print '"'+keyphrase+'" found!'
                        phrase_found=True
                        no_makeup_in_a_row=0
                        break
                    
                   
                if not phrase_found:
                    no_makeup_in_a_row+=1
                #print no_makeup_in_a_row

                if no_makeup_in_a_row > 10:
                    print "This isn't a makeup channel, stop gathering..."
                    no_makeup_in_a_row=0
                    return videos
                    break
                

                
		print 'Gathering stats from '+title[:30]+'..'+\
                                      ' published on '+publishDate.split('T')[0]+'...'
                video_stats = get_video_stats(videoId)
                try:
                    views = int(video_stats[0])
                except:
                    views = 0
                print 'views: '+str(views)
                if views<400:
                    low_views_in_a_row+=1
                else:
                    low_views_in_a_row=0
                if low_views_in_a_row>5:
                    print "This channel has low view counts, stop gathering..."
                    
                    return videos
                    break
                comments = video_stats[1]
                likes = video_stats[2]
                dislikes = video_stats[3]
                channel_id = video_stats[4]
                channel_name = video_stats[5]
                country = get_country(channel_id)

		if not isBefore(beforeDate,publishDate):			
			return videos
		videoEntry = {'video_id':videoId,'publish_date':publishDate,'title':title\
                                              ,'description':description,'views':views,'comments':comments\
                                              ,'likes':likes,'dislikes':dislikes,'channel_id':channel_id\
                                              ,'channel_name':channel_name, 'country':country}

		videos.append(videoEntry)

	
	while response:
		if 'nextPageToken' in response: 
			response = youtube.playlistItems().list(
					part = 'snippet',
                    playlistId = playlist_id,
					pageToken = response['nextPageToken'] 
                    ).execute()
			for video in response['items']:
				title = video['snippet']['title']
				videoId = video['snippet']['resourceId']['videoId']
				publishDate = video['snippet']['publishedAt']
				description = video['snippet']['description']
				phrase_found=False
                                for keyphrase in general_makeup_phrases:
                                    if keyphrase == '':
                                        continue
                                    
                                    if keyphrase.lower() in title.lower() \
                                       or keyphrase.lower() in description.lower():
                                        print '"'+keyphrase+'" found!'
                                        phrase_found=True
                                        no_makeup_in_a_row=0
                                        break
                                    
                                   
                                if not phrase_found:
                                    no_makeup_in_a_row+=1
                                #print no_makeup_in_a_row

                                if no_makeup_in_a_row > 12:
                                    print "This isn't a makeup channel, stop gathering channel"
                                    no_makeup_in_a_row=0
                                    return videos
                                    break
				print 'Gathering video stats from '+title[:30]+\
                                      ' published on '+publishDate.split('T')[0]+'...'
				video_stats = get_video_stats(videoId)
				try:
                                    views = int(video_stats[0])
                                except:
                                    views = 0
				print 'views: '+str(views)
				if views<400:
                                    low_views_in_a_row+=1
                                    print 'only '+str(views) + ' views '+str(low_views_in_a_row)
                                else:
                                    low_views_in_a_row=0
                                if low_views_in_a_row>5:
                                    print "This channel has low view counts, stop gathering..."
                                    no_makeup_in_a_row=0
                                    return videos
                                    break
                                comments = video_stats[1]
                                likes = video_stats[2]
                                dislikes = video_stats[3]
                                channel_id = video_stats[4]
                                channel_name = video_stats[5]
                                country = get_country(channel_id)
				
				if not isBefore(beforeDate,publishDate):			
					return videos
				videoEntry = {'video_id':videoId,'publish_date':publishDate,'title':title\
                                              ,'description':description,'views':views,'comments':comments\
                                              ,'likes':likes,'dislikes':dislikes,'channel_id':channel_id\
                                              ,'channel_name':channel_name, 'country':country}
				videos.append(videoEntry)

		else:
			break
	return videos

def get_country(channel_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
    response = youtube.channels().list(
                    part = 'snippet',
                    id = channel_id,
                ).execute()
    try:
            country = response['items'][0]['snippet']['country']
    except:
            country='Not Found'
    return country

def get_video_stats(video_id):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
	
	try:
		response = youtube.videos().list(
                    part = 'statistics',
                    id = video_id,
                    ).execute()
		#print response
		stats =  response['items'][0]['statistics']
	
		views = stats['viewCount']
		comments_count = stats['commentCount']
		try:
			likes = stats['likeCount']
			dislikes = stats['dislikeCount']
		except:
			likes = 0
			dislikes = 0
	except Exception as e:
            #raw_input(e)
            print e
            views = 0
            comments_count=0
            likes = 0
            dislikes = 0

        try:
		response = youtube.videos().list(
                    part = 'snippet',
                    id = video_id,
                    ).execute()
		#print response
		snippet =  response['items'][0]['snippet']
                channel_id = snippet['channelId']
                channel_name = snippet['channelTitle']
		
		
	except Exception as e:
            channel_id = ''
            channel_name = ''
            print e
            #raw_input(e)
            

	return [views,comments_count,likes,dislikes,channel_id,channel_name]

def isBefore(date1,date2):
	date1=date1.split('T')[0].split('-')
	date2=date2.split('T')[0].split('-')
      
	if int(date1[0]) < int(date2[0]):
                
		return True
    
	elif int(date1[1]) < int(date2[1]) and int(date1[0]) == int(date2[0]):
		return True
    
	elif int(date1[2]) < int(date2[2]) and int(date1[1]) == int(date2[1]):     
		return True
	else:
		return False

def youtube_search(q, max_results=10,order="relevance", token=None, location=None, location_radius=None):

  youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    developerKey=DEVELOPER_KEY)

  search_response = youtube.search().list(
    q=q,
    type="video",
    pageToken=token,
    order = order,
    part="id,snippet",
    maxResults=max_results,
    location=location,
    locationRadius=location_radius

  ).execute()

  videos = []

  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      videos.append(search_result)
  try:
      nexttok = search_response["nextPageToken"]
      return(nexttok, videos)
  except Exception as e:
      nexttok = "last_page"
      return(nexttok, videos)


def geo_query(video_id):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    video_response = youtube.videos().list(
        id=video_id,
        part='snippet, recordingDetails, statistics'

    ).execute()

    return video_response

def get_channel_id(username):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

	if len(username) < 20:
		response = youtube.channels().list(
						part = 'contentDetails',
		                forUsername = username,
		                ).execute()
		channel_id = response['items'][0]['id']
		return channel_id
	else:
		return username


def get_channel_videos_before_old(channel_id,beforeDate):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
	videoId_list={}
	if len(channel_id) < 20:
		response = youtube.channels().list(
						part = 'contentDetails',
		                forUsername = channel_id,
		                ).execute()
	else:
		response = youtube.channels().list(
						part = 'contentDetails',
		                id = channel_id,
		                ).execute()

	playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
	print playlist_id

	
	response = youtube.playlistItems().list(
					part = 'snippet',
                    playlistId = playlist_id,
                    ).execute()
	#print response
	for video in response['items']:
		print video
		open('responsevideo.txt','w').write(str(video))
		
		title = video['snippet']['title']
		videoId = video['snippet']['resourceId']['videoId']
		publishDate = video['snippet']['publishedAt']
		
		views = ''
		print title, videoId, publishDate, views
		if not isBefore(beforeDate,publishDate):			
			return videoId_list
		videoEntry = {'video_id':videoId,'publish_date':publishDate,'title':title}
		videoId_list[videoId] = videoEntry
		open('response.txt','w').write(str(video))
	
	while response:
		if 'nextPageToken' in response: 
			response = youtube.playlistItems().list(
					part = 'snippet',
                    playlistId = playlist_id,
					pageToken = response['nextPageToken'] 
                    ).execute()
			for video in response['items']:
				title = video['snippet']['title']
				videoId = video['snippet']['resourceId']['videoId']
				publishDate = video['snippet']['publishedAt']
				description = video['snippet']['description']
				
				views = ''
				
				if not isBefore(beforeDate,publishDate):			
					return videoId_list
				videoEntry = {'video_id':videoId,'publish_date':publishDate,'title':title\
                                              ,'description':description}
				videoId_list[videoId] = videoEntry
				open('response.txt','w').write(str(video))
		else:
			break
	return videoId_list

def store_channel_name(channel_id):
        ###get channel name and country
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
        response = youtube.channels().list(
                        part = 'snippet',
                        id = channel_id,
                    ).execute()
        channel_name=response['items'][0]['snippet']['title']
        print channel_name
        #print response['items'][0]['snippet']
        try:
                country = response['items'][0]['snippet']['country']
        except:
                country=''
        print country
	print response
	open('channelnametest.txt','w').write(str(response))
        #raw_input()
	####store in db
	db = TinyDB('video_db.json')
	Channel = Query()
	
	
	db.insert({'channel_id': channel_id,'country': country,'channel_name': channel_name})
	#db.update({'channel_name':channel_name,'country':country},Channel.channel_id == channel_id)
        channelDict = db.search(Channel.channel_id == channel_id)[0]

        #raw_input(str(channelDict))
def store_video_stats(video_id, channel_id):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
	
	try:
		response = youtube.videos().list(
                    part = 'statistics',
                    id = video_id,
                    ).execute()
		stats =  response['items'][0]['statistics']
		
		
		open('stats.txt','w').write(str(response['items'][0]))
	
		views = stats['viewCount']
		comments_count = stats['commentCount']
		try:
			likes = stats['likeCount']
			dislikes = stats['dislikeCount']
		except:
			likes = 0
			dislikes = 0
	except:
		views = 0
		comments_count=0
		likes = 0
		dislikes = 0	

	db = TinyDB('video_db.json')
	Channel = Query()
	videoDict = db.search(Channel.channel_id == channel_id)[0]['videos']
	print videoDict[video_id]
	videoDict[video_id]['views']=views
	videoDict[video_id]['comments_count']=comments_count
	videoDict[video_id]['likes']=likes
	videoDict[video_id]['dislikes']=dislikes
	
	db.update({'videos':videoDict},Channel.channel_id == channel_id)
	
def get_comments(video_id):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)
	#get views	
	comment_list=[]
	try:
		response = youtube.commentThreads().list(
		                part = 'snippet',
		                videoId = video_id,
		                maxResults = 100, # Only take top 100 comments...
		                order = 'relevance', #... ranked on relevance
		                textFormat = 'plainText',
		                ).execute()
		for item in response['items']:
					comment_list.append(item['snippet']\
					['topLevelComment']['snippet']\
					['textDisplay'])
	except Exception as e:
                
                if 'has disabled' in str(e):
                        return comment_list
                elif 'you have exceeded' in str(e) or 'Could not automatically' in str(e) \
                     or 'The quota will' in str(e):
                        isNext=False
                        global DEVELOPER_KEY
                        for key in DEVELOPER_KEYS.split('\n'):
                                if isNext:
                                        DEVELOPER_KEY=key
                                        break
                               
                                if DEVELOPER_KEY == key:
                                        isNext=True
                        print DEVELOPER_KEY
                        return get_comments(video_id)
                else:
                        print str(e)
                        #raw_input(str(e))
                        

	while response:
		if 'nextPageToken' in response: 
			try:			
				response = youtube.commentThreads().list(
		                part = 'snippet',
		                videoId = video_id,
		                maxResults = 100, # Only take top 100 comments...
		                order = 'relevance', #... ranked on relevance
		                textFormat = 'plainText',
						pageToken = response['nextPageToken'] 
		                ).execute() 
				for item in response['items']:
					comment_list.append(item['snippet']\
					['topLevelComment']['snippet']\
					['textDisplay'])
			except:
				continue
		else: 
			break

	return comment_list

######
######
#####
######

import sys
#sys.path.append('/home/spnichol/Dropbox/youtube_tutorial/')
#from youtube_videos import youtube_search
#from youtube_videos import get_video_stats
##from youtube_videos import get_country
#from youtube_videos import get_channel_videos_before
#import pandas as pd
import json
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import datetime
from tinydb import TinyDB, Query



def median(lst):
    n = len(lst)
    s = sorted(lst)
    return (sum(s[n//2-1:n//2+1])/2.0, s[n//2])[n % 2] if n else None


    
def get_channel_id(username):
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

	if len(username) < 20:
		response = youtube.channels().list(
						part = 'contentDetails',
		                forUsername = username,
		                ).execute()
		channel_id = response['items'][0]['id']
		return channel_id
	else:
		return username
	    
def isBefore(date1,date2):
	date1=date1.split('T')[0].split('-')
	date2=date2.split('T')[0].split('-')
    
	if int(date1[0]) < int(date2[0]):
		return True
    
	elif int(date1[1]) < int(date2[1]) and int(date1[0]) == int(date2[0]):
		return True
    
	elif int(date1[2]) < int(date2[2]) and int(date1[1]) == int(date2[1]):     
		return True
	else:
		return False
	    
def grab_videos(keyword, token=None):
    res = youtube_search(keyword, token=token)
    try:
        token = res[0]
    except Exception as e:
        print e
        #raw_input()
        return 'error'
    videos = res[1]
    print "found " + str(len(videos)) + ' videos'
    return [token,videos]

#test = youtube_search("spinners")

def start():
    global skip_to_phrase
    first_token=True
    key_phrases = open('search_phrases.txt').read().split('\n')
    print_text = ''
    video_db = TinyDB('scrapped_videos.json')
    channel_db = TinyDB('scrapped_channels.json')
    low_view_video_db = TinyDB('low_view_video_db.json')
    before_date = (datetime.date.today() - datetime.timedelta(3*365/12)).isoformat()
    search_before_date = (datetime.date.today() - datetime.timedelta(18*365/12)).isoformat()
    foreigner_video_db = TinyDB('foreigner_video_db.json')
    checked_video_db = TinyDB('checked_video_db.json') 
    #db.update({'channel_name':channel_name,'country':country},Channel.channel_id == channel_id)

    
    
    for key_phrase in key_phrases:
        if key_phrase == '':
            continue
        if not skip_to_phrase == '':
            if key_phrase != skip_to_phrase:
                continue
            else:
                skip_to_phrase=''
                continue
        skip_to_phrase = key_phrase
        
        print '_______________________________'
        print '_______________________________'
        print '_______________________________'
        print '_______________________________'
        print 'Current search phrase is: '+key_phrase
        print '_______________________________'
        print '_______________________________'
        print '_______________________________'
        print '_______________________________'

        first_token = False
        ####loop through all results
        page_count=0
        count=0
        token = None
        not_found_in_a_row=0
        found_channel = False
        while token != "last_page":
            if not found_channel:
                not_found_in_a_row+=1
                if not_found_in_a_row == 5:
                    print '_______________________________'
                    print 'Current search phrase is: '+key_phrase
                    print '_______________________________'
                if not_found_in_a_row>10:
                    break
            else:
                not_found_in_a_row=0
            page_count+=1
            if page_count > 50:
                break
            #grab 10 videos
            results = grab_videos(key_phrase, token=token)
            if results == 'error':
                continue
            ten_videos = results[1]
            token = results[0]
            ##grab video stats of each video
            for video in ten_videos:
                video_id = video['id']['videoId']

                
                ##skip if video_id already gathered or checked
                Video = Query()
                #if checked:
                try:
                    checked_video_db.search(Video.video_id == video_id)[0]
                    print 'This video was already checked, skip it...'
                    continue
                except:
                    pass
                #if gathered:
                try:
                    video_db.search(Video.video_id == video_id)[0]
                    print 'This video was already gathered, skip it...'
                    
                    continue
                except:
                    pass
                try:
                    low_view_video_db.search(Video.video_id == video_id)[0]
                    checked_video_db.insert({'video_id': video_id})
                    print 'This video was checked, skip it...'
                    continue
                except:
                    pass
                if video_id in open('video_skiplist.txt').read():
                    continue
                
                publish_date = video['snippet']['publishedAt']
                title = video['snippet']['title']
                description = video['snippet']['description']
                
                ##grab the remaining stats only if the
                ##publish date is <3 months ago
                
                if isBefore(search_before_date,publish_date):
             
                    
                    video_stats = get_video_stats(video_id)
                    views = video_stats[0]
                    comments = video_stats[1]
                    likes = video_stats[2]
                    dislikes = video_stats[3]
                    channel_id = video_stats[4]
                    channel_name = video_stats[5]
                    if channel_id in skip_channel_list:
                        checked_video_db.insert({'video_id': video_id})
                        print channel_name + ' is in the skip channel list, skip it...'
                        continue
                    ##skip if the channel name already gathered
                    Channel=Query()
                    try:
                        video_db.search(Video.channel_id == channel_id)[0]
                        checked_video_db.insert({'video_id': video_id})
                        print channel_name + ' was already gathered, skip it...'
                        continue
                    except:
                        pass
                    #print "This channel was already gathered, skip this channel..."
                    
                    ##skip if view count > 500
                    if views>500:
                        country = get_country(channel_id)
                    else:
                        checked_video_db.insert({'video_id': video_id})
                        print "Video doesn't have enough views, skip it..."
                        continue
                else:
                    checked_video_db.insert({'video_id': video_id})
                    print "Video is more then a year old, skip it..."
                    continue

                #skip non US or not not found if us only is specified
                if US_only:
                    if country <> 'US':
                        if country <> 'Not Found':
                            print country+' Foreigner!!!!!!! You shall not Pass!!!!!!!!!!!!!!!!'
                            print ' saved to foreigner video db...'
                            checked_video_db.insert({'video_id': video_id})
                            foreigner_video_db.insert({'video_id': video_id,'publish_date': publish_date,\
                           'title': title, 'views': views,\
                           'comments': comments,'likes': likes, \
                           'dislikes': dislikes, 'channel_id': channel_id,\
                           'channel_name': channel_name, 'country': country})
                            continue
                
                ###append the video to the list of all videos
                print '_______________________________'
                print channel_name,views,publish_date.split('T')[0],country,title
                
                print_text+= video_id+'\t'+\
                             publish_date+'\t'+\
                             title+'\n'
                
                video_db.insert({'video_id': video_id,'publish_date': publish_date,\
                           'title': title, 'views': views,\
                           'comments': comments,'likes': likes, \
                           'dislikes': dislikes, 'channel_id': channel_id,\
                           'channel_name': channel_name, 'country': country})
                print 'Video added to video db...'
                
                print 'New Channel Found!!!!!!!!!!\n'
                
                print channel_name+'\n'
                
                found_channel=True
                
                ###get channel stats and last 90 day video stats
                print 'Gathering videos from '+channel_name+' from the last 3 months...'
                videos = get_channel_videos_before(channel_id,before_date)
                
                
                #get median and keyphrase data
                views_list = []
                comments_list = []
                likes_list = []
                search_phrases = open('search_phrases.txt').read().split('\n')
                general_makeup_phrases = open('general_makeup_phrases.txt').read().split('\n')
                cheap_phrases = open('cheap_phrases.txt').read().split('\n')
                high_end_phrases = open('high_end_phrases.txt').read().split('\n')
                
                search_phrase_videos = 0
                general_makeup_phrase_videos = 0
                cheap_phrase_videos = 0
                high_end_phrase_videos = 0
                total_search_phrases = 0
                total_general_makeup_phrases = 0
                total_cheap_phrases = 0
                total_high_end_phrases = 0
            
                for video in videos:
                    #print str(video)
                    views_list.append(int(video['views']))
                    comments_list.append(int(video['comments']))
                    likes_list.append(int(video['likes']))
                    phrase_found=False 
                    for keyphrase in search_phrases:
                        if keyphrase == '':
                            continue
                        if keyphrase.lower() in video['title'].lower() \
                           or keyphrase.lower() in video['description'].lower():
                            print '"'+keyphrase+'" found!'
                            if not phrase_found:
                                search_phrase_videos+=1
                            total_search_phrases+1
                            phrase_found=True
                    phrase_found=False 
                    for keyphrase in general_makeup_phrases:
                        if keyphrase == '':
                            continue
                        if keyphrase.lower() in video['title'].lower() \
                           or keyphrase.lower() in video['description'].lower():
                            print '"'+keyphrase+'" found!'
                            if not phrase_found:
                                general_makeup_phrase_videos+=1
                            total_general_makeup_phrases+=1
                            phrase_found=True
                      
                   
                    phrase_found=False 
                    for keyphrase in cheap_phrases:
                        if keyphrase == '':
                            continue
                        if keyphrase.lower() in video['title'].lower() \
                           or keyphrase.lower() in video['description'].lower():
                            print '"'+keyphrase+'" found!'
                            if not phrase_found:
                                cheap_phrase_videos+=1
                            total_cheap_phrases+=1
                            phrase_found=True
                    phrase_found=False 
                    for keyphrase in high_end_phrases:
                        if keyphrase == '':
                            continue
                        if keyphrase.lower() in video['title'].lower() \
                           or keyphrase.lower() in video['description']:
                            print '"'+keyphrase+'" found!'
                            if not phrase_found:
                                high_end_phrase_videos+=1
                            total_high_end_phrases+=1
                            phrase_found=True
                    

                median_views = median(views_list)
                median_likes = median(likes_list)
                median_comments = median(comments_list)

                channel_db.insert({'channel_id':channel_id, 'channel_name':channel_name,\
                                  'median_views':median_views, 'median_likes':median_likes,\
                                  'median_comments':median_comments, 'general_makeup_phrase_videos':general_makeup_phrase_videos,\
                                  'cheap_phrase_videos':cheap_phrase_videos, 'high_end_phrase_videos':high_end_phrase_videos,\
                                  'country':country, 'videos':videos,'videos_last_3_months':len(videos),\
                                   'search_phrase_videos':search_phrase_videos,\
                                   'total_search_phrases':total_search_phrases,\
                                   'total_general_makeup_phrases':total_general_makeup_phrases,\
                                   'total_cheap_phrases':total_cheap_phrases,\
                                   'total_high_end_phrases':total_high_end_phrases})
                checked_video_db.insert({'video_id': video_id})
                print 'Channel added to channel DB...\n'
                print '_______________________________'
                print 'Current search phrase is: '+key_phrase
                print '_______________________________'
                #raw_input()
                print '______________________________'
                print channel_name+', '+country+', median views:'+str(median_views)+', videos last 3 months: '+str(len(videos))+\
                      ' , makeup videos: '+str(general_makeup_phrase_videos)
                print '______________________________'
                                  
                

        open('print_text.txt','w').write(print_text.encode('utf8'))

skip_to_phrase = ''
error_count= 0
not_found_in_a_row=0
while 1:
    error_count+=1
    if error_count>25:
        print 'OUT OF SCRAPE QUOTA'
        break
    try:
        start()
    except Exception as e:
        print str(e)
        #raw_input()
        if 'Keyboard' in str(e):
            break
        current_key = open("current_key.txt").read().split()[0]
        print current_key
        keylist = open('api_keylist.txt').read().split('\n')
        next = False
        found = False
        for key in keylist:
          
            if len(key)<3:
                continue
            if next:
                open('current_key.txt','w').write(key)
                #print 'found'
                global DEVELOPER_KEY
                DEVELOPER_KEY = key
                print DEVELOPER_KEY
                found = True
                break
            if key == current_key:
                next = True

        if not found:
            open('current_key.txt','w').write(keylist[0])
