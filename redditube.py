#!/usr/local/bin/python
#BY Arturo Alviar
#Redditube (10/24/2014)
'''Gets videos from the r/videos's hot,
grabs the youtube data and outputs as a csv'''

import praw, json, urllib, requests, time, sys
from time import strftime
r = praw.Reddit(user_agent="Research project that takes youtube videos from r/videos and tries to analyze the impact reddit has on youtube video views - by /u/your_reddit_username")

API_KEY = "YOURAPIKEYGOESHERE" #Youtube API key


def convertYouTubeTime(videoLen):
	'''Takes seconds as a parameter and
	converts it to a hour minute second format
	'''
	hours = videoLen / 3600
	minutes = videoLen/60
	seconds = videoLen%60
	return "%s:%s:%s" % (hours, minutes, seconds)

def convertRedditPostedTime(seconds):
	'''takes in seconds as a parameter and formats it
	in a similar timestamp manner that reddit does on its posts'''

	now = int(time.time())
	postedTime = now - int(seconds)
	posted = postedTime / 31536000
	if posted >= 1:
		return "Posted " + str(posted) + " year(s) ago"
	posted = postedTime / 2592000
	if posted >= 1:
		return "Posted " + str(posted) + " month(s) ago"
	posted = postedTime / 86400
	if posted >= 1:
		return "Posted " + str(posted) + " day(s) ago"
	posted = postedTime / 3600
	if posted >= 1:
		return "Posted " + str(posted) + " hours(s) ago"
	posted = postedTime / 60
	if posted >= 1:
		return "Posted " + str(posted) + " minute(s) ago"
	return "Posted " + str(posted) + " seconds(s) ago"

def removeChars(string):
	'''remove quotes or commas in reddit or youtube video titles in order
	to preserve csv structure'''

	if '"' in string:
		string = string.replace('"', "'")
	if "," in string:
		string = string.replace(",", "")
	return string


def generateTitle(videoCat):
	'''Create title for text file. Takes a string as a parameter and concatenates
	that with the current time by calling the strftime function'''
	return videoCat + strftime("_%Y-%m-%d_%H-%M.csv")

def getDate():
	'''Get current time. Used to organize output file'''
	return strftime("%m/%d/%Y %H-%M")


def getYouTubeID(youtubeURL):
	'''Takes in a URL as a parameter and checks if the url is a youtube link.
	If it is, grab the id by spliting the url string.'''

	if "m.youtube" in youtubeURL: #check to see if it is a mobile link
		startPos = youtubeURL.index("v=") # find the begining of the video id
		videoID = youtubeURL[startPos+2:startPos+13] #slice id value
		return videoID #return that id value

	elif "youtube" in youtubeURL: #if it is not mobile check if it is a regular youtube link
		if "v=" in youtubeURL:
			startPos = youtubeURL.index("v=")#hanlde regular clean youtube links
			videoID = youtubeURL[startPos+2:startPos+13] #Video IDs are always 11 characters and are typically after a ?v=
			return videoID
		elif "v%3D" in youtubeURL:
			startPos = youtubeURL.index("v%3D") #This is to handle messy links
			videoID = youtubeURL[startPos+4:startPos+15]
			return videoID
		else:
			print "Is youtube link but ID not found"
			return False # is a youtube link but not a video, maybe a link to a channel

	elif "youtu.be" in youtubeURL: #if it is not mobile or regular, it might be a shorten link
		startPos = youtubeURL.index("be/") #This is to handle shortern links
		videoID = youtubeURL[startPos+3:startPos+14]
		return videoID

	else: #not a youtube link
		print "Not Youtube video" #for debugging purposes
		return False #skip if the link is not a youtube link

def getYouTubeVideoInfo(videoJSON):
	try: #try and see if video has all of the following keys from the JSON file we grabbed
		return [videoJSON.json()['data']['title'], videoJSON.json()['data']['viewCount'], videoJSON.json()['data']['likeCount'], videoJSON.json()['data']['commentCount'], videoJSON.json()['data']['duration'] ]
	except KeyError: #if there is one or two keys missings (likeCount and/or commentCount since videos can have 0 of both) lets try the following
		if 'likeCount' not in videoJSON.json()['data'] and 'commentCount' not in videoJSON.json()['data'] and 'duration' not in videoJSON.json()['data'] and 'viewCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], "NO VIEWS", "0", "0 or disabled", "LIVE"]

		elif 'likeCount' not in videoJSON.json()['data'] and 'commentCount' not in videoJSON.json()['data'] and 'duration' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], videoJSON.json()['data']['viewCount'], "0", "0 or disabled", "LIVE"]

		elif 'likeCount' not in videoJSON.json()['data'] and 'commentCount' not in videoJSON.json()['data'] and 'viewCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], "NO VIEWS", "0", "0 or disabled", videoJSON.json()['data']['duration']]

		elif 'duration' not in videoJSON.json()['data'] and 'commentCount' not in videoJSON.json()['data'] and 'viewCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], "NO VIEWS", videoJSON.json()['data']['likeCount'], "0 or disabled", "LIVE"]

		elif 'viewCount' not in videoJSON.json()['data'] and 'duration' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], "NO VIEWS", videoJSON.json()['data']['likeCount'], videoJSON.json()['data']['commentCount'], "LIVE"]

		elif 'viewCount' not in videoJSON.json()['data'] and 'commentCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], videoJSON.json()['data']['viewCount'], "0", "0 or disabled", videoJSON.json()['data']['duration']]

		elif 'likeCount' not in videoJSON.json()['data'] and 'commentCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], videoJSON.json()['data']['viewCount'], "0", "0 or disabled", videoJSON.json()['data']['duration']]

		elif 'likeCount' not in videoJSON.json()['data'] and 'viewCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], "NO VIEWS", "0", videoJSON.json()['data']['commentCount'], videoJSON.json()['data']['duration']]

		elif 'commentCount' not in videoJSON.json()['data']: #if commentCount is not in the JSON file, then return our info with the comment index set to 0 or disabled since disabled comments means 0 comments
			return [videoJSON.json()['data']['title'], videoJSON.json()['data']['viewCount'], videoJSON.json()['data']['likeCount'], "0 or disabled", videoJSON.json()['data']['duration']]

		elif 'duration' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], videoJSON.json()['data']['viewCount'], videoJSON.json()['data']['likeCount'], videoJSON.json()['data']['commentCount'], "LIVE"]

		elif 'likeCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], videoJSON.json()['data']['viewCount'], "0",  videoJSON.json()['data']['commentCount'], videoJSON.json()['data']['duration']]

		elif 'viewCount' not in videoJSON.json()['data']:
			return [videoJSON.json()['data']['title'], "NO VIEWS", videoJSON.json()['data']['likeCount'] ,  videoJSON.json()['data']['commentCount'], videoJSON.json()['data']['duration']]


def getVideoJSON(youtubeVideoID):
	'''Get youtube video JSON file and make sure video is working/ has not been deleted '''
	video = requests.get("https://www.googleapis.com/youtube/v3/videos?part=statistics&id=" + youtubeVideoID + "&key=" + API_KEY) #use this to get status code
	#video = requests.get("http://gdata.youtube.com/feeds/api/videos/"+youtubeVideoID) #request video if you do not have an API key
	jsonFile = requests.get("http://gdata.youtube.com/feeds/api/videos/"+youtubeVideoID+"?v=2&alt=jsonc") #request the json file of the video which contains the information we want
	print video.status_code #used during debugging
	if(video.status_code == requests.codes.ok): #check if the video exists and has not been deleted
		return jsonFile
	else:
		return False



def getHot():
	'''Sends request to Reddit for the first 100 videos in the hot section of r/videos.
	Gets the title, url, and number of upvotes. Uses the url to get the video ID and send a request to Youtube
	for the JSON file of that video. Reads the JSON file to collect the number of views. All this info
	is then written to a text file.
	'''
	filename = generateTitle("Hot")
	with open(filename, "w") as hot_text:
		hot_text.write("rank, gotOn, redditTitle, uploadedToReddit, uploadedToRedditUTC, ups, url, youtubeTitle, views, likes, comments, duration, isYoutube\n")
		x = 1;
		for hot in r.get_subreddit('videos').get_hot(limit=100): #use pwar to get the 100 posts(that is the max) in the hot section of r/videos
			hot_text.write("%s," % x)
			hot_text.write("%s," % getDate())
			hot_text.write("%s," % removeChars(hot.title.encode("utf-8"))) #encode title in unicode otherwise python doesnt understand it
			hot_text.write("%s," % convertRedditPostedTime(hot.created_utc)) #get upvotes of a certain post
			hot_text.write("%s," % hot.created_utc) #get upvotes of a certain post
			hot_text.write("%s," % hot.ups) #get upvotes of a certain post
			hot_text.write("%s," % hot.url.encode("utf-8"))
			ytURL = getYouTubeID(hot.url)#grab youtube ID
			if(ytURL): #is the url we are looking at a youtube one?
				data = getVideoJSON(ytURL) #get the json data
				if(data):
					info = getYouTubeVideoInfo(data)
					hot_text.write("%s," % removeChars(info[0].encode("utf-8")))
					hot_text.write("%s," % info[1])
					hot_text.write("%s," % info[2])
					hot_text.write("%s," % info[3])
					hot_text.write("%s," % convertYouTubeTime(info[4]))
					hot_text.write("YES\n")
			else:
				hot_text.write("None,")
				hot_text.write("None,")
				hot_text.write("None,")
				hot_text.write("None,")
				hot_text.write("None,")
				hot_text.write("NO\n")
			x+=1

def getNew():
	filename = generateTitle("New")
	with open(filename, "w") as new_text:
		new_text.write("rank, gotOn, redditTitle, uploadedToReddit, uploadedToRedditUTC, ups, url, youtubeTitle, views, likes, comments, duration, isYoutube\n")
		n = 1
		for new in r.get_subreddit('videos').get_new(limit=100):
			new_text.write("%s," % n) #rank
			new_text.write("%s," % getDate()) #date file was created
			new_text.write("%s," % removeChars(new.title.encode("utf-8"))) #reddit title
			new_text.write("%s," % convertRedditPostedTime(new.created_utc)) #how long ago posted
			new_text.write("%s," % new.created_utc) #actual time since posted in seconds
			new_text.write("%s," % new.ups) #upvotes
			new_text.write("%s," % new.url.encode("utf-8")) #youtube url grabbed from reddit
			ytURL = getYouTubeID(new.url)
			if(ytURL):
				data = getVideoJSON(ytURL)
				if(data):
					info = getYouTubeVideoInfo(data)
					new_text.write("%s," % removeChars(info[0].encode("utf-8"))) #youtube title
					new_text.write("%s," % info[1]) #views
					new_text.write("%s," % info[2]) #likes
					new_text.write("%s," % info[3]) # comments
					new_text.write("%s," % convertYouTubeTime(info[4])) #duration
					new_text.write("YES\n")
			else:
				new_text.write("None,")
				new_text.write("None,")
				new_text.write("None,")
				new_text.write("None,")
				new_text.write("None,")
				new_text.write("NO\n")
			n+=1
if __name__ == "__main__":
	try:
		if sys.argv[1] == "new":
			getNew()
		elif sys.argv[1] == "hot":
			getHot()
		else:
			print "Usage: ./redditube keyword"
			print "keyword can be hot or new"
	except IndexError:
		print "Usage ./redditube keyword"
		print "Keywoard can be hot or new"
