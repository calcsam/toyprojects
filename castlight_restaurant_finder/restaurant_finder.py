import csv
from ete2 import Tree
import sys
import math
import collections as cl

# MenuTree class, extending Tree
# Creates a tree of all possible ways to buy a given set of items from a given restaurant.
# In other words, say you want a large burger, a small burger, fries, and a shake
class menuTree(Tree):

	#sometimes for options that aren't possible money_spent is never set programmatically,
	#so I assigned a default value of None here and check for it below
	# to prevent errors from being thrown when referencing it
	nodeNumber = 0
	money_spent = None
	remaining_items_to_purchase = None
	
	def populateTree(self, current_menu_to_fulfill):

		#if we still have more things to buy:
		if self.remaining_items_to_purchase:

			#look at the first item...
			item = self.remaining_items_to_purchase[0]

			#...and check which menu items contain it. For each menu item that contains it,
			# create a separate tree fork. Eg, if you want a burger, and can buy a burger, or
			# a burger-fries-drink combo, or a burger-fries-drink supersize combo, three tree forks
			# will be created.
			for deal in current_menu_to_fulfill.keys():
				if item in deal:

					#unique ID generator
					#the 50 is semi-arbitary, assumes there aren't more than 50 options at any point;
					# exists to ensure unique ID #s. 
					try:
						parentNo = 50*(self.up.nodeNumber + 1)
					except:
						parentNo = 0

					#if the menu item contains the item we are looking for,
					# create a name for a child, create the child, and then find the child.
					newName = item + str(parentNo + self.nodeNumber)
					self.add_child(name=newName)
					childNode = self.search_nodes(name=newName)[0]

					#add the money spent to the running total
					childNode.add_feature("money_spent", self.money_spent + float(current_menu_to_fulfill[deal]))
					current_items = self.remaining_items_to_purchase
					
					#create new list without items that were bought, by subtracting bags. Note we *cannot* just use
					#list comprehension here due to possible duplicates (what if we want two burgers?)
					current_counter = cl.Counter(current_items)
					deal_counter = cl.Counter(deal)
					current_counter.subtract(deal_counter)
					new_current_items = list(current_counter.elements())
					print "new_current_items",
					print new_current_items
					print "childNode.money_spent",
					print childNode.money_spent
					#set the new list as the child node's list of things to buy			
					childNode.add_feature("remaining_items_to_purchase", new_current_items)
					self.nodeNumber += 1

					#....and run this program recursively on the child node.
					childNode.populateTree(current_menu_to_fulfill)

#This class, given a set of restaurants and a list of items desired, handles those,
#finds the best restaurant, and outputs it to user.
class RestaurantFinder:
	restaurants = {}
	restaurant_prices = {}
	minimum_price_overall = 99999
	best_restaurant = None
	items = []

	#For each restaurant, create a tree using a recursive algorithm, then find the 
	#cheapest meal among all leaves of the tree.	
	def findBestRestaurant(self):
		if not self.items:
			raise Exception("Need to pass a non-empty set of items to purchase")
		if not self.restaurants:
			raise Exception("Need to pass a non-empty set of restaurants")
		for restaurant in self.restaurants.keys():
			current_menu = self.restaurants[restaurant]
			t = menuTree()
			t.add_feature("money_spent", 0)
			t.add_feature("remaining_items_to_purchase", self.items)
			t.populateTree(current_menu)

			#sometimes for options that aren't possible money_spent is never set programmatically,
			#so I assigned a default value of None above and check for it here
			# to prevent errors from being thrown
			setOfPossibleOptions = [x.money_spent for x in t.get_leaves() if x.money_spent and x.remaining_items_to_purchase == []] 
			#To ensure that the min() does not return an error we attach this condition
			if setOfPossibleOptions and setOfPossibleOptions != [0]:
				minimum_menu_price_for_restaurant = min(setOfPossibleOptions)
				self.restaurant_prices[restaurant] = minimum_menu_price_for_restaurant
				if minimum_menu_price_for_restaurant < self.minimum_price_overall:
					self.minimum_price_overall = minimum_menu_price_for_restaurant
					self.best_restaurant = restaurant

	def setRestaurantList(self,givenRestaurants):
		self.restaurants = givenRestaurants
	def setItems(self,givenItems):
		self.items = items
	def printBestRestaurant(self):
		if not self.best_restaurant:
			print None
		else:
			print str(self.best_restaurant) + ",",
			print self.minimum_price_overall

	def __init__(self, givenRestaurants=None, givenItems=None):
		if givenRestaurants:
			self.restaurants = givenRestaurants
		if givenItems:
			self.items = givenItems

def takeUserInputs():

	#the items the user inputted. If you want to buy two items just type in "burger burger fries" or whatever.
	#I assume this is not being used for event catering! If so I would redesign the input algorithm
	items = sys.argv[2:]

	# restaurant will be a dictionary, key = name and value = the menur.
	#each menu will be a dictionary with key as the tuple of the items, 
	# and value being the price of that item or combo.
	inputRestaurants = {}

	with open(sys.argv[1]) as f:
		reader = csv.reader(f)
		counter = 0
		for row in reader:

			#Check for row length:
			#if row in data isn't long enough, prints warning and skips row to avoid ArrayOutOfBounds exception
			if len(row) < 2:
				print "Warning! Row %d does not contain all relevant information. Skipping row" % counter
				continue
			
			# Read in the restaurant name and items price
			restaurant_name = row[0]
			item_price = row[1]
			
			#Check whether item_price is a number and can be added to other #s.
			# If not, skips row to avoid exceptions when trying to add it to other #s later.
			try:
				float(item_price)
			except:
				print "Warning! Row %d contains an invalid price. Skipping row" % counter
				continue
			
			# Create list of items on the menu, relevant to the user's search
			# (Relevance means: if the menu item contains at least one relevant item to what is desired, 
			# and there is no examined menu item which provides the set of relevant items at less cost)

			# the "if item[1:] in items" can be deleted if desired.
			# However, reading in only deals containing items that are desired. saves space in memory. 
			# For a different use case, we could delete this to separate the read/filter functions,
			# but right now desired items always passed with menu			
			item_list = [item[1:] for item in row[2:] if item[1:] in items] #[1:] to delete inital space				

			# Initialize the menu for the restaruant if necessary
			if not restaurant_name in inputRestaurants.keys():
				inputRestaurants[restaurant_name] = {}

			# If a menu item is relevant to the user's query, add it to the menu of the restaurant it belongs to 
			if item_list and (tuple(item_list) not in inputRestaurants[restaurant_name].keys() or inputRestaurants[restaurant_name][tuple(item_list)] > item_price):
				inputRestaurants[restaurant_name][tuple(item_list)] = item_price
	return inputRestaurants, items

# get the restaurant menus to pass to the restaurant finder
relevantRestaurantMenus, userItems = takeUserInputs()

# create the restaurant finder, pass the restaurant menus
myFinder = RestaurantFinder(relevantRestaurantMenus, userItems)

#find the best restaurant...
myFinder.findBestRestaurant()

#...and output it
myFinder.printBestRestaurant()