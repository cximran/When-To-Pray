from twython import Twython,TwythonStreamer
import csv, json,os,re,requests, time
from praytimes import prayTimes
from datetime import date

zipdict=json.load(open('ziplist.json','r')) # loads a pre-build JSON that contains  informatio, age, of reference and                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
APP_KEY='pG1C0NoMH1FzezkznLBPCDhrs'
APP_SECRET='lY3hx3ygcjgjphhKN76J2GClgdazNPLQakuDEScECZvKdNy6x8'
OAUTH_TOKEN = '2651886151-XLoV4GSvyfs6qRPHLOvfQUmnv79LirOMTgsmhU6'
OAUTH_TOKEN_SECRET = 'hYO82dmHEvkwzbUWp9cpNPmZD4j43fRVWyUKf1rMGqJal'
location_api='https://maps.googleapis.com/maps/api/geocode/json'
timezone_api='https://maps.googleapis.com/maps/api/timezone/json'
google_api_key='AIzaSyCAQ0Ya-_yYDG427n54O1_BUugHtagXuOk'
twitter=Twython(APP_KEY, APP_SECRET,OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

def getlocationslist(location):
	urlparameters={'key':google_api_key,'address':location}
	locationsreq=requests.get(location_api,params=urlparameters)
	locationslist=locationsreq.json()
	return(locationslist)
def gettimezone(location):
	today=date.today()
	timestamp=time.mktime(date.today().timetuple())
#	urlparameters={'location':'%s,%s'%(location[0],location[1]),'timestamp':timestamp}
	urlparameters={'key':google_api_key,'location':'%s,%s'%(location[0],location[1]),'timestamp':timestamp}

	timezoneandoffsetreq=requests.get(timezone_api,params=urlparameters)
	timezoneandoffset=timezoneandoffsetreq.json()
	tzoffset=timezoneandoffset['rawOffset']/3600
	dstoffset=timezoneandoffset['dstOffset']/3600
	return(tzoffset,dstoffset)
def ziptolatlong(zip): #looks up a zip code that's a key in a dictionary loaded in memry
	coords = (zipdict[zip][2],zipdict[zip][3])
	timezoneandoffset=(zipdict[zip][4],zipdict[zip][5])
	location=((zipdict[zip][0],zipdict[zip][1]))
	return(coords,timezoneandoffset,location)
def iswithinDST(mydate):
	# This function is used to check if the current day is within the U.S. days for daylight savings, as found on Wikipedia: http://en.wikipedia.org/wiki/Daylight_saving_time_in_the_United_States
	dstdict= {2014:[date(2014,3,9),date(2014,11,2)],
			  2015:[date(2014,3,8),date(2014,11,1)],
			  2016:[date(2014,3,13),date(2014,11,6)],
			  2017:[date(2014,3,12),date(2014,11,5)],
			  2018:[date(2014,3,11),date(2014,11,4)]}
	return(dstdict[date.today().year][1]>=mydate>= dstdict[date.today().year][0])


def getprayertimes(location,tzoffset,dstoffset):
	#the core function - it gets prayer times 

	times = prayTimes.getTimes(date.today(),location,timezone=tzoffset,dst=dstoffset);
	return(times)

def statusbuilder(locationslist):
	lat,longi=(locationslist['results'][0]['geometry']['location']['lat'],locationslist['results'][0]['geometry']['location']['lng'])
	tzoffset,dstoffset=gettimezone((lat,longi))
	times=getprayertimes((lat,longi),tzoffset,dstoffset)
	status='Times for %s: ' %(locationslist['results'][0]['formatted_address'])
	status+=('Fajr: %s Dhuhr: %s Asr: %s Maghrib: %s Isha: %s' % (times['fajr'],times['dhuhr'],times['asr'],times['maghrib'],times['isha']))
	return(status)

class MyStreamer(TwythonStreamer):	
	def on_success(self, data):
		pass
		if 'text' in data:
			#if 'times for' in data['text']
			query = re.search(r'(?<=^@whentopray).*', data['text'])
			locationslist=getlocationslist(query.group(0))
			if len(locationslist) > 1: 
				twitter.update_status(status="@%s Multiple locations found, could you please be more specific?" % data['user']['screen_name'],in_reply_to_status_id=data['id'])
			else:
				status=statusbuilder(locationslist)
				completestatus=('@%s:%s'% (data['user']['screen_name'],status))
				twitter.update_status(status=completestatus)
				
	def on_error(self, status_code, data):
		print (status_code)

if __name__ == "__main__":
#	twitter.verify_credentials()
#	twitter.update_status(status='testing 123')
	stream = MyStreamer(APP_KEY, APP_SECRET,OAUTH_TOKEN, OAUTH_TOKEN_SECRET)	
	stream.statuses.filter(track='@whentopray')
