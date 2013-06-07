from chargePorts import resetChargePorts, resetChargePortListeners
import vehicle

# ---- storage lots ------

doneChargingLot = [ ]
failedLot = [ ]
declinedLot = [ ]

# adding a lot of cars that don't need to be charged
# might help when we're trying to pick distribution values
cantChargeLot = []

numberOfVehiclesInSimulation = 0
numVehiclesMade = 0

csvOn = False # use this to toggle csv output

# ----- global time vars ------
currentTime = 0 
interval = 0

# -------- price per kilowatt*hour -------
electricityPrice = .5   # in dollars
penaltyCoefficient = 2.0 # a multiplier for electricity - used to add a penalty weight ... keep > 1

# used in main.py to set the common interval variable
def setInterval( newInterval ):
    global interval
    interval = newInterval

def setNumberOfVehiclesInSimulation( n ):
    global numberOfVehiclesInSimulation
    numberOfVehiclesInSimulation = n

# function to reset time, failed/done lots etc. Called at start of every algorithm simlulation
def updateGlobals( arrayOfVehicleArrivals ):
    global currentTime
    currentTime = 0
    global doneChargingLot
    doneChargingLot = []
    global failedLot
    failedLot = []
    global declinedLot
    declinedLot = []
    global cantChargeLot
    cantChargeLot = []
    resetChargePorts()  # function in chargePorts.py to empty all chargePorts
    global numVehiclesMade
    numVehiclesMade = 0
    
    # reset charge, timeToCharge for each vehicle
    for minute, numVehiclesPerMin in enumerate( arrayOfVehicleArrivals ):
        for vehicle in numVehiclesPerMin:
            vehicle.resetVehicleCharge()

# looks at done and failed lots, and returns the profits based on the vehicles
def calcProfit():
    profit = 0

    # add up profit from each vehicle in done lot
    for vehicle in doneChargingLot:
        profit += vehicle.timeToCharge * electricityPrice * vehicle.chargeRate / 60.0

    # now to deal with vehicles in the failed lot
    if len( failedLot ) > 0:
        for vehicle in failedLot:
            profit += ( vehicle.timeToCharge * electricityPrice * vehicle.chargeRate / 60.0) - ( ( vehicle.chargeNeeded - vehicle.currentCharge ) * electricityPrice * penaltyCoefficient )

    return profit


# returns string representation of all vehicles in a list by id in form [0,1,2,3,4...] 
# with one id highlighted which is useful for viewing llfIndex or earliestDLIndex, etc
# pass in -1 for highlight for no highlight
def vehicleIdsInList( list, highlight ):
    output = "["
    for index, item in enumerate( list ):
        if index == highlight:
            output += "***"
        if item is not None:
            output += str( item.id )
        else:
            output += "None"
        if index != len( list ) - 1:
            output += ", "
    output += "]"
    return output

# returns string representation of all vehicles in 2d array, most notably simulationInterval in main.py
def vehicleIdsIn2DList( list ):
    print"------2d List-----"
    for row in list:
        if row is not None:
            count = 0
            output = "["
            for item  in row:
                if item is not None:
                    output += str(item.id)
                    count += 1
                    if count != numberOfVehiclesInSimulation:
                        output += ", "
            output += "]"
        print output
    print"------------------"
