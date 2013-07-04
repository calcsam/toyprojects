# http://www.thumbtack.com/challenges

import sys
myDict = {}

def readOneLine(line): # parses the line
  (one, two, three) = mySplitter(line)
	if line == "END":
		return [line.line]
	elif line.startswith("SET"):
		return ("SET", (two, three))
	elif line.startswith("GET"):	
		return ("GET", two)
	elif line.startswith("UNSET"):	
		return ("UNSET", two)
	elif line.startswith("BEGIN"):
		return ("BEGIN", None) # the none to make the myInput[0] read the first entry and not the first character
	elif line.startswith("ROLLBACK"):
		print "okay, trying?"
		return ("ROLLBACK", None)
	elif line.startswith("COMMIT"):
		return ("COMMIT", None)
	elif line.startswith("NUMEQUALTO"):
		return ("NUMEQUALTO", two)
	return "Hello?"
def mySplitter(lineRead):
	array = lineRead.split()
	if len(array) == 0:
		return (None, None, None)
	elif len(array) == 1:
		return (array[0],None,None)
	elif len(array) == 2:
		return (array[0],array[1],None)
	else:
		return (array[0],array[1],array[2])

def master():
	myInput = ["test"]*2
	database = {}
	inTransBlock = False
	inTransBlockArray = {}
	shouldContinue = True
	while shouldContinue:
		line = sys.stdin.readline()
		if line[0:3] == "END": #Cuts off the carriage return
			shouldContinue = False
		myInput = readOneLine(line)
		if myInput[0] == "SET":
			if inTransBlock and not inTransBlockArray.has_key(myInput[1][0]): # once this key appears once, we want to keep it, so that we roll back to the beginning.
				try:
					prev = database[myInput[1][0]]
				except KeyError:
					prev = None
				inTransBlockArray[myInput[1][0]] = prev
			database[myInput[1][0]] = myInput[1][1]
		if myInput[0] == "GET":	
			try:
				print database[myInput[1][0]]
			except: 
				print "that key is not in the database"
		if myInput[0] == "UNSET":
			if inTransBlock:
				try:
					prev = inTransBlock[myInput[1]]
				except Error:
					prev = None
				inTransBlockArray[myInput[1][0]] = prev
			del database[myInput[1]]
		if myInput[0] == "BEGIN":
			inTransBlock = True
		if myInput[0] == "ROLLBACK":
			if inTransBlock == False:
				print "INVALID ROLLBACK"
			else:
				for key in inTransBlockArray: 
					if inTransBlockArray[key] != None: 	# overwrite the key to database /
						database[key] = inTransBlockArray[key]
					else:
						if database.has_key(key): # delete key from databse
							del database[key]
			inTransBlock = False
		if myInput[0] == "COMMIT":
			inTransBlockArray = {}
			return ("COMMIT")
		if myInput[0] == "NUMEQUALTO":
			i = 0
			for key in database:
				if database[key] == myInput[1]:
					i+=1
			print i

master()
