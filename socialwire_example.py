# in response to http://www.socialwire.com/exercise1.html; took me about 2 hours to code
# python 2.7

def test(aString):
  stillNumber = True
	expectedExpressions = 0
	allExp = []
	currentExp = []
	for char in aString:
		#print "iterate" + char
		if is_number(char) and stillNumber:
			expectedExpressions = expectedExpressions*10 + float(char)
		else:
			if stillNumber == True: # only should enter the else if loop once
				stillNumber = False
				if expectedExpressions == 0:
					expectedExpressions = 1
			if notInSet(char):
				return "INVALID, " + char + " NOT VALID CHARACTER"
			currentExp = push(char, currentExp)
			#print currentExp
			if completeTree(currentExp):
				allExp.append(currentExp)
				currentExp = []
	if len(allExp) == 0:
		return "INVALID, NO FULL EXPRESSIONS GIVEN"
	if not completeTree(allExp[len(allExp)-1]):
		return "INVALID, LAST EXPRESSION " + str(allExp[len(allExp)-1]) + "NOT COMPLETE"  
	if len(allExp) != expectedExpressions:
		#print allExp
		return "EXPECTED "+ str(expectedExpressions) + " EXPRESSIONS. GOT " + str(len(allExp))
	print "PARSE TREE: " + str(len(allExp)) + " EXPRESSION(S):",
	print allExp
	return "VALID"


def push(element,currentTree): # put element into our Tree, using recursion to push it down where necessary
	if not currentTree: # if empty
		#print "hello"
		currentTree.append([element])
		return currentTree
	if currentTree[0] == ["Z"]:
		if len(currentTree) == 1:		
			currentTree.append([element])
			return currentTree
		if len(currentTree) == 2:
			return [currentTree[0], push(element,currentTree[1])]
	if currentTree[0] in (["M"],["K"],["P"],["Q"]):
		if len(currentTree) == 1:
			currentTree.append([element])
			return currentTree
		if len(currentTree) == 2 and not completeTree(currentTree[1]):
			return [currentTree[0], push(element,currentTree[1])]
		if len(currentTree) == 2 and completeTree(currentTree[1]):
			currentTree.append([element])
			return currentTree
		if len(currentTree) == 3:
			return [currentTree[0], currentTree[1], push(element,currentTree[2])]
	if currentTree[0] in ("M","K","P","Q", "Z"):
		return [[currentTree[0]],[element]]

def completeTree(currentTree): # determines if tree is complete using recursion
	if not currentTree: # if empty
		return False
	if currentTree[0] in (["M"],["K"],["P"],["Q"]) and len(currentTree) == 3 and completeTree(currentTree[1]) and completeTree(currentTree[2]):
		return True
	elif currentTree[0] == ["Z"] and len(currentTree) == 2 and completeTree(currentTree[1]):
		return True
	elif currentTree[0] in (["a"],["b"],["c"],["d"],["e"],["f"],["g"],["h"],["i"],["j"],"a","b","c","d","e","f","g","h","i","j") and len(currentTree) == 1:
		return True
	#print "savory"
	#print currentTree
	return False
def notInSet(char): # determine if valid input
	if char in ("a","b","c","d","e","f","g","h","i","j","M","K","P","Q","Z"):
		return False
	return True

def is_number(s): #okay, this should be self-explanatory
    try:
        float(s)
        return True
    except ValueError:
        return False

inputString = raw_input()
while inputString != "BREAK":
	print test(inputString)
	inputString = raw_input()

