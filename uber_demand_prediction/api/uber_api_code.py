from __future__ import division
from flask import Flask, jsonify, abort, request, make_response, url_for
import json
import datetime as dt
from datetime import datetime
import time
from time import mktime
import numpy as np
import math
app = Flask(__name__, static_url_path = "")

originalStart = None
dateStart = None
dateEnd = None
times = []
to_be_binned = []
two_category_buckets = {}
hourly_bucket = None
predictions = {}
checkinsPerWeek = {}
@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify( { 'error': 'Bad request' } ), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify( { 'error': 'Not found' } ), 404)

@app.route('/api/post', methods=['POST'])
def post_checkins():
	global times
	global dateStart
	global dateEnd
	global to_be_binned
	global originalStart
	oldStart = dateStart
	oldEnd = dateEnd

	json_object = json.loads(request.data)
	currentLength = len(times)
	additionalLength = currentLength + len(json_object)
	for element in json_object:
		thisDate = datetime.fromtimestamp(mktime(time.strptime(element,"%Y-%m-%dT%H:%M:%S+00:00")))
		if not originalStart:
			originalStart = thisDate
		if not dateStart or thisDate < dateStart:
			dateStart = thisDate
		if not dateEnd or thisDate > dateEnd:		
			dateEnd = thisDate
		times.append(thisDate)
		to_be_binned.append(thisDate)
		updateWeekArray(thisDate)
	if oldStart == None and oldEnd == None:
		initialize_dates(dateStart,dateEnd)
		bin_dates(1)
	else:			
		initialize_dates(dateStart,oldStart)
		initialize_dates(oldEnd,dateEnd)
		bin_dates(1)
	to_be_binned = []
	thisDict = {str(i): times[i] for i in range(currentLength,additionalLength)}
	return jsonify(**thisDict)

@app.route('/api/<int:date_id>', methods=['GET', 'DELETE'])
def handle_date_request():
	global times
	global two_category_buckets
	global hourly_bucket
	currentDate = times[date_id]
	if request.headers.has_key('-Method'):
		method = request.headers['-Method'].upper()
	if request.method == 'GET':
		return jsonify(dict((date_id, times[date_id])))
	elif request.method == 'DELETE':
		# delete from the buckets it's sitting in
		two_category_buckets[(currentDate.hour, currentDate.weekday())] = [x for x in two_category_buckets[(currentDate.hour, currentDate.weekday())] if x != times[date_id]]
		hourly_bucket[hoursSince2006(currentDate)] = [x for x in hourly_bucket[hoursSince2006(currentDate)] if x != times[date_id]]
		times[date_id] = None
		return jsonify(dict((date_id, times[date_id])))

@app.route('/api/all_data', methods=['GET', 'DELETE'])
def handle_all_dates_request():
	global times
	global two_category_buckets
	global hourly_bucket
	global dateStart
	global dateEnd
	global predictions
	if request.headers.has_key('-Method'):
		method = request.headers['-Method'].upper()
	if request.method == 'GET':
		all_dates = dict((times[i], i) for i in enumerate(times))
		return jsonify(**all_dates)
	elif request.method == 'DELETE':
		dateStart = None
		dateEnd = None
		times = []
		two_category_buckets = {}
		hourly_bucket = None
		predictions = {}
		return jsonify(**predictions)

def initialize_dates(placeToStart, placeToEnd):
	if placeToEnd == placeToStart:
		return ""
	global hourly_bucket
	global two_category_buckets
	currentDate = placeToStart

	## creating initial list
	if hourly_bucket == None:
		hourly_bucket = [None] * (hoursSince2006(placeToEnd)) 

	# this array is good for analytics. I'm aware it's going to create a 30,000-some length array, mostly empty. 
	# However, I created this data structure in order to cover the possibility of prepending dates onto an array,
	# and then having to shift the whole array over, *every time this happens*. Ugh. 
	
	# if appending dates on the end of the list
	elif dateFromHoursSince2006(len(hourly_bucket)) < placeToEnd:
		while currentDate <= placeToEnd:
			hourly_bucket.append([])
			currentDate = currentDate + dt.timedelta(hours = 1)	

	# if prepending dates on beginning of list
	elif dateFromHoursSince2006(len(hourly_bucket)) > placeToEnd:
		while currentDate < placeToEnd:
			hourly_bucket[hoursSince2006(currentDate)] = []
			currentDate = currentDate + dt.timedelta(hours = 1)		

	if len(two_category_buckets) == 0:
		for hour in range(0,24):
			for weekday in range(0,7):
				two_category_buckets[(hour, weekday)] = []

# note! 
# this, like the rest of this program, assumes a contiguous set of dates and times for
# the date. If two non-contiguous sets of dates are uploaded, the program will simply assume 
# there were zero checkins in the intervening time and calculate accordingly!


def get_time_periods_in_training_set(thisHour, thisWeekday, thisDateEnd = None, thisDateStart = None):
	#get number days, reduced to the nearest divisor of 7
	if not thisDateEnd:
		thisDateEnd = dateEnd
	if not thisDateStart:
		thisDateStart = dateStart
	if thisDateEnd < thisDateStart:    # to deal with dates inputted previous to the original start date
		return (-1 * get_time_periods_in_training_set(thisHour, thisWeekday, thisDateStart, thisDateEnd))
	diffDays = ((thisDateEnd - thisDateStart).days // 7) * 7
	testDateGap = thisDateStart + dt.timedelta(days = diffDays)
	testDateInGap = dt.datetime(year = testDateGap.year, month = testDateGap.month, day = testDateGap.day, hour = testDateGap.hour)
	increment = 0
	
	# set increment to 1 if there is a match in the partial week
	while testDateInGap < thisDateEnd:
		testDateInGap = testDateInGap + dt.timedelta(hours = 1)
		if testDateInGap.hour == thisHour and testDateInGap.weekday() == thisWeekday:
			increment = 1

	return (diffDays // 7 ) + increment

@app.route('/api/all_data_binned/', methods=['GET'])
def return_binned_dates():
	return jsonify(**two_category_buckets)

def bin_dates(type_id):
	#assumes all bins have been created already
	global hourly_bucket
	global two_category_buckets
	global to_be_binned
	# add dates to buckets
	if to_be_binned:
		prevIndex = hoursSince2006(to_be_binned[0])
	for time in to_be_binned:
		two_category_buckets[(time.hour, time.weekday())].append(time)
		
		# ie, if the desired element not in the hourly bucket array index

		if hoursSince2006(time) >= len(hourly_bucket):
			
			counter = prevIndex + 1              		# this is code to deal with empty time periods
			while counter < hoursSince2006(time):        # 
				hourly_bucket[counter].append([])		#
				counter += 1
			hourly_bucket.append([time])

		# desired element in the hourly bucket array index but currently
		# an empty array
		elif not hourly_bucket[hoursSince2006(time)]:

			counter = prevIndex + 1                 # this is code to deal with empty time periods
			while counter < hoursSince2006(time):   #
				hourly_bucket[counter] = []          #
				counter += 1
			hourly_bucket[hoursSince2006(time)] = [time]
		
		# desired element in the hourly bucket array index and 
		# there are some items there
		else:
			hourly_bucket[hoursSince2006(time)].append(time)
		prevIndex = hoursSince2006(time)
	if type_id == 1:
		return two_category_buckets
	elif type_id == 2:
		myDict = {str(i): hourly_bucket[i] for i in enumerate(hourly_bucket)}
		return myDict

@app.route('/api/data_analytics', methods=['GET'])
def perform_analytics():
	createPredictionsArray()
	return jsonify(predictions)

def createPredictionsArray():
	global predictions
	"""for element in two_category_buckets.keys():      ---- diagnostic tool 
		if element:
			print element, 
			print len(two_category_buckets[element])
		else:
			print element
	"""
	global predictions
	datePredictStart = dt.datetime(2012,5,1, 0, 0, 0)
	datePredictEnd = dt.datetime(2012,5,16, 0, 0, 0)

	# should handle exceptions on small data sets where we don't have enough data to compute weekly slope
	try:
		slope = returnModifier()      
		modifier_average = averager(slope)
	except:
		slope = 1

	global dateStart
	currentDate = datePredictStart
	while currentDate < datePredictEnd:
		# set basic prediction equal to # of observations with same (hour, weekday)
		# divided by number of periods with same (hour, weekday)

		basicPrediction = len(two_category_buckets[(currentDate.hour, currentDate.weekday())]) / get_time_periods_in_training_set(currentDate.hour, currentDate.weekday())
		hoursIndex = hoursSince2006(currentDate)
		time_period_number = get_time_periods_in_training_set(currentDate.hour, currentDate.weekday(),currentDate)		
		#if we can retrieve the relevant data, try to calculate a prediction modifier, 
		# equal to logins in the last 24 hours divided by logins in an average 24 hours with the same (hour, weekday)

		if hoursIndex - 1 < len(hourly_bucket) and hourly_bucket[hoursIndex - 1]:
			thisObjectLast24Hours = sum([len(hourly_bucket[index3]) for index3 in range(hoursIndex - 24, hoursIndex) if hourly_bucket[index3]])
			
			# all indices in the hourly_bucket with the same (hour, weekday)
			# because it's ordered sequentially, easy to calculate sums and so in
			sameWeekdayAndHour = [index2 for index2 in range(hoursSince2006(dateStart) + 24,hoursSince2006(dateEnd)) if hoursIndex % 168 == index2 % 168]
			holderObjectLast24HoursCounter = 0
			holderObjectNextHourCounter = 0
			# iterate through this list, grabbing all 'last 24 hours' and 'next hour'
			for index2 in sameWeekdayAndHour:
				holderObjectLast24Hours = sum([len(hourly_bucket[index3]) for index3 in range(index2 - 24, index2) if hourly_bucket[index3]])
				holderObjectLast24HoursCounter += holderObjectLast24Hours
				holderObjectNextHour = 0
				if hourly_bucket[index2]:
					holderObjectNextHour = len(hourly_bucket[index2])
				holderObjectNextHourCounter += holderObjectNextHour		

			#computes an average
			averageObjectLast24Hours = (holderObjectLast24HoursCounter / len(sameWeekdayAndHour))
			averageObjectNextHour = (holderObjectNextHourCounter / len(sameWeekdayAndHour))
		else:
			thisObjectLast24Hours = 0
			averageObjectLast24Hours = 0
		#calculate the prediction modifier if possible, otherwise set it to 1

		try:
			ratioToMultiply = thisObjectLast24Hours / averageObjectLast24Hours
		except:
			ratioToMultiply = (slope ** time_period_number) / modifier_average
			print ratioToMultiply

		# convert to string and attach to predictions array

		stringDate = currentDate.strftime("%Y-%m-%dT%H:%M:%S")
		predictions[stringDate] = str(basicPrediction*ratioToMultiply)
		# incremenet value to next

		currentDate = currentDate + dt.timedelta(hours = 1)	

def averager(slope):
	avg_boost_in_training_data = sum([slope**i for i in sorted(checkinsPerWeek.keys())[0:-2]]) / (len(checkinsPerWeek.keys())- 1)
	return avg_boost_in_training_data

# needs at least a week of data!
# the 0:-2 eliminates the last week of data because it will be incomplete and not accurately reflect 
# but exception should be handled in above routine

def returnModifier():
	weekmod = [math.log(checkinsPerWeek[i]/checkinsPerWeek[0]) for i in sorted(checkinsPerWeek.keys())[0:-2]]
	weekindex = [i for i in sorted(checkinsPerWeek.keys())[0:-2]]
	x = np.array(weekindex)
	x = x[:,np.newaxis]
	y = np.array(weekmod)
	a, _, _, _ = np.linalg.lstsq(x, y)
	exp_slope = math.exp(a)
	return exp_slope
def updateWeekArray(thisDay):
	global checkinsPerWeek
	num = (thisDay - originalStart).days // 7
	if num in checkinsPerWeek.keys():
		checkinsPerWeek[num] += 1
	else:
		checkinsPerWeek[num] =1	
		
def relevantDateTuple(dateObject):
	return (dateObject.year, dateObject.month, dateObject.day, dateObject.hour, dateObject.weekday())

# this is used as a unique key for hour indices. 
# If you want times back to 2000, just find-replace the whole document with 2000 for 2006.
# Or if times start in 2009, find-replace 2009 for 2006.

def hoursSince2006(dateObject):
	delta = dateObject - dt.datetime(2006,1,1,0,0,0)
	return ((delta.days) * 24) + delta.seconds // 3600

def dateFromHoursSince2006(myInt):
	year2006 = dt.datetime(2006,1,1,0,0,0)
	newYear = year2006 + dt.timedelta(hours = myInt)
	return newYear

if __name__ == '__main__':
    app.run(debug = True)