from __future__ import division
from flask import Flask
import json
import datetime as dt
from datetime import datetime
import time
from time import mktime



#this is used as a unique key for hour indices

def relevantDateTuple(dateObject):
	return (dateObject.year, dateObject.month, dateObject.day, dateObject.hour, dateObject.weekday())

def hoursSince2000(dateObject):
	delta = dateObject - dt.datetime(2000,1,1,0,0,0)
	return ((delta.days) * 24) + delta.seconds // 3600

def dateFromHoursSince2000(myInt):
	year2000 = dt.datetime(2000,1,1,0,0,0)
	newYear = year2000 + dt.timedelta(hours = myInt)
	#print newYear.timetuple()
	return newYear


"""
app = Flask(__name__)

@app.route('/todo/api/v1.0/tasks', methods = ['GET'])
def get_tasks():
    return jsonify( { 'dates': times } )

if __name__ == '__main__':
    app.run(debug = True)

"""

#process times

with open("uber_demand_prediction_challenge.json") as f:
	json_object = json.load(f)

times = []

for element in json_object:
	times.append(datetime.fromtimestamp(mktime(time.strptime(element,"%Y-%m-%dT%H:%M:%S+00:00"))))

dateStart = dt.datetime(2012,3,1, 0, 0, 0)
dateEnd = dt.datetime(2012,5,1, 0, 0, 0)
currentDate = dateStart
baseInt = hoursSince2000(dateStart)
# initalize buckets

two_category_buckets = {}
hourly_bucket = [None] * (hoursSince2000(dateEnd) - baseInt) # good for analytics
while currentDate < dateEnd:
	two_category_buckets[(currentDate.hour, currentDate.weekday())] = []
	hourly_bucket[hoursSince2000(currentDate) - baseInt] = []
	currentDate = currentDate + dt.timedelta(hours = 1)

# add dates to buckets


for time in times:
	two_category_buckets[(time.hour, time.weekday())].append(time)
	hourly_bucket[hoursSince2000(time) - baseInt].append(time)

#print len(hourly_bucket[0])
#print len(hourly_bucket[1])
print "Type, Date 1 Last 24 Hours, Date 1 Last Hour, Date 2 Last 24 Hours, Date 2 Last Hour, Date 1 Index, Date 2 Index, Date 1 Year, Date 1 Month, Date 1 Day, Date 1 Hour, Date 1 Weekday, Date 2 Year, Date 2 Month, Date 2 Day, Date 2 Hour, Date 2 Weekday"

#iterate through times
for index in range(24,len(hourly_bucket)):
	sameWeekdayAndHour = [index2 for index2 in range(24,index) if index % 168 == index2 % 168]
	secondObjectNextHourCounter = 0
	secondObjectLast24HoursCounter = 0
	for index2 in sameWeekdayAndHour:
		firstObjectNextHour = len(hourly_bucket[index])
		secondObjectNextHour = len(hourly_bucket[index2])
		secondObjectNextHourCounter += secondObjectNextHour
		firstObjectLast24Hours = sum([len(hourly_bucket[index3]) for index3 in range(index - 24, index)])
		secondObjectLast24Hours = sum([len(hourly_bucket[index3]) for index3 in range(index2 - 24, index2)])
		secondObjectLast24HoursCounter += secondObjectLast24Hours
		dateTupleOne = relevantDateTuple(dateFromHoursSince2000(index + baseInt))
		dateTupleTwo = relevantDateTuple(dateFromHoursSince2000(index2 + baseInt))
		print "object-to-object,",
		print str(firstObjectLast24Hours) + ",",
		print str(firstObjectNextHour)+ ",",
		print str(secondObjectLast24Hours) + ",",
		print str(secondObjectNextHour)+ ",",
		print str(dateFromHoursSince2000(index + baseInt)) + ",",
		print str(dateFromHoursSince2000(index2 + baseInt)) + ",",
		for element in dateTupleOne:
			print str(element) + ",",
		for element in dateTupleTwo:
			print str(element) + ",",
		print ""
		if index2 == max(sameWeekdayAndHour):
			print "average " + str(len(sameWeekdayAndHour)) + ",",
			print str(firstObjectLast24Hours) + ",",
			print str(firstObjectNextHour)+ ",",
			print str(secondObjectLast24HoursCounter / len(sameWeekdayAndHour)) + ",",
			print str(secondObjectNextHourCounter / len(sameWeekdayAndHour))+ ",",
			print str(dateFromHoursSince2000(index + baseInt)) + ",",
			print "NA,",
			for element in dateTupleOne:
				print str(element) + ",",
			print ""
# define sequential time buckets

