import Queue
import common
import csvGen
import chargePorts
import chargeEvent
import copy

schedules = [ [ ] for y in range( chargePorts.numChargePorts ) ]
numOverlapInserts = 0

def simulate( arrayOfVehicleArrivals ):

    # reset global variables such as time, done/failed lots
    common.updateGlobals( arrayOfVehicleArrivals )

    global currentTime
    global numOverlapInserts
    global minutesCharged 
    global allVehicles

    minutesCharged = [0] * common.numberOfVehiclesInSimulation
    allVehicles = []

    # initialize a CSV document for storing all data
    csvGen.generateCSV( "dsac" )

    # iterate through each vehicle in each minute
    for minute, numVehiclesPerMin in enumerate( arrayOfVehicleArrivals ):

        for vehicle in numVehiclesPerMin: 
            port = chargePorts.openChargePort()
            allVehicles.append(vehicle)

            if vehicle.currentCharge > vehicle.chargeNeeded:
                csvGen.exportVehicleToCSV( vehicle, "Charge Not Needed" )
                common.cantChargeLot.append( vehicle )
                print "CHARGE NOT NEEDED: ",vehicle.id
                continue

            # a port is open so start charging the vehicle
            if port is not None:

                # add to chargePort and respective schedule
                chargePorts.chargePorts[ port ] = vehicle
                schedules[ port ].append( vehicle )

                # initialize a listener object for its charging activity
                chargePorts.chargePortListeners[ port ].insert( 0 , chargeEvent.ChargeEvent( vehicle, common.currentTime ) )
    
                continue
            # no ports are available so put the vehicle in the queue
            else:

                # any appendables?
                appendable = findAppendableChargePort( vehicle )

                # add to schedule
                if appendable != -1:
                    # there is at least one car in the schedule
                    if len(schedules[ appendable ]) > 0:
                        tempVehicle = schedules[ appendable ][ len( schedules[ appendable ] ) - 1  ] #last item
                        newStartTime = tempVehicle.startTime + tempVehicle.timeToCharge

                    # schedule is appendable because it is empty 
                    else:
                        carInChargePort = chargePorts.chargePorts[ appendable ]
                        newStartTime = carInChargePort.startTime + carInChargePort.timeToCharge

                    vehicle.updateStartTime( newStartTime )
                    schedules[ appendable ].append( vehicle )

                # an ugly conflict
                else:
                    vehicle.updateStartTime( vehicle.depTime - vehicle.timeToCharge )
                    
                    leastProfitConflictResults = leastProfitConflict( vehicle )
                    leastProfitConflictPort = leastProfitConflictResults[0]
                    leastProfitConflictSchedule = leastProfitConflictResults[1]

                    # vehicle appended with conflict
                    if leastProfitConflictPort > 0:
                        schedules[ leastProfitConflictPort ] = leastProfitConflictSchedule
                        numOverlapInserts += 1
                        if leastProfitConflictSchedule[0] == vehicle:
                            chargePorts.chargePorts[leastProfitConflictPort] = vehicle

                    else:
                        # CSV to decline car
                        csvGen.exportVehicleToCSV( vehicle, "DECLINED" )
                        common.declinedLot.append( vehicle )


        updateVehicles()
        common.currentTime += 1

    # vehicles done arriving, now continue with the simulation
    while not chargePorts.chargePortsEmpty() or not schedulesEmpty():\

        updateVehicles()
        common.currentTime += 1

    # print "DSAC: total number of cars: ", common.numberOfVehiclesInSimulation , \
    #     "  elapsed time: " , common.currentTime , \
    #     "  done charging lot: " , len( common.doneChargingLot ) , \
    #     "  failed charging lot: " , len( common.failedLot ) , \
    #     "  declind lot: ", len( common.declinedLot ) , \
    #     "  cant charge lot: " , len( common.cantChargeLot ) , \
    #     "  schedules:  " , schedulesToString() , \
    #     "  chargePorts " , chargePorts.toString()

    # write a CSV for all the chargePort logs
    csvGen.exportChargePortsToCSV( "dsac" )

    failed = uniqueVehicles(common.failedLot)
    done = uniqueVehicles(common.doneChargingLot) - failed # if a car gets split and is in done and failed, that is considered failed
    declined = uniqueVehicles(common.declinedLot)

    output = [totalProfit(), len(done), len(failed), len(declined), common.numberOfVehiclesInSimulation, common.currentTime]
    return output

leastProfitConflictCount = 0
def leastProfitConflict( vehicle ):
    global leastProfitConflictCount
    # print "leastProfitConflictCount ", leastProfitConflictCount
    leastProfitConflictCount+=1
    profitGained = 0
    leastProfitConflictPort = -1
    bestSchedule = []

    # iterate through each schedule
    for index, schedulePort in enumerate( schedules ):

        # print "Profit Conflict: Trying to put vehicle ", vehicle.id," into ", common.vehicleIdsInList(schedulePort,-1)

        # make a temporary one since we'll be messing with this
        tempSched = copy.deepcopy(schedulePort)

        # print "tempSched ",tempSched

        cutoffTime = vehicle.depTime - vehicle.timeToCharge

        # loop through all the scheduled tasks
        # looking for the car that cutOff time interrupts
        splitVehicleIndex = len( tempSched ) - 1

        while splitVehicleIndex >=0 and tempSched[ splitVehicleIndex ].startTime > vehicle.startTime:
            splitVehicleIndex -= 1

        splitVehicle = tempSched[ splitVehicleIndex ]

        duplicate = splitVehicle.duplicate() # represents the second half of the split vehicle  
        
        splitVehicle.timeToCharge = vehicle.startTime - splitVehicle.startTime

        if len(tempSched) - 1 == splitVehicleIndex:
            duplicate.startTime = vehicle.depTime
        else:
            duplicate.startTime = tempSched[ len(tempSched)-1 ].depTime # duplicate will be appended to the end of the schedule 
        duplicate.timeToCharge -= splitVehicle.timeToCharge
        duplicate.currentCharge += splitVehicle.timeToCharge * ( duplicate.chargeRate / 60.0 )
        duplicate.arrivalTime = str(duplicate.arrivalTime) + "(duplicate)"


        # need to create a list of all vehicles (including the one that is split)
        # that gets appended to the end of the schedule

        pushToEnd = [] # represents the part of the schedule that the new vehicle is kicking out
        pushToEnd.append(duplicate)

        #need to split the second vehicle that the new vehicle overlaps partially 

        secondSplitVehicleIndex = splitVehicleIndex + 1 # the index after the first split vehicle

        while secondSplitVehicleIndex < len(tempSched): 
            if tempSched[secondSplitVehicleIndex].startTime + tempSched[secondSplitVehicleIndex].timeToCharge > vehicle.depTime:
                break
            secondSplitVehicleIndex += 1

        # need to make sure there is a second vehicle that needs to be split
        if secondSplitVehicleIndex < len(tempSched):    
            secondSplitVehicle = tempSched[ secondSplitVehicleIndex ]

            duplicateSecondSplitVehicle = copy.deepcopy( secondSplitVehicle ) # represents second part of split vehicle

            duplicateSecondSplitVehicle.startTime = vehicle.depTime
            duplicateSecondSplitVehicle.timeToCharge -= (vehicle.depTime - duplicateSecondSplitVehicle.startTime)

            # this will eventually be after duplicateSecondSplitVehicle in the schedule
            secondSplitVehicle.timeToCharge -= duplicateSecondSplitVehicle.timeToCharge
            secondSplitVehicle.currentCharge += duplicateSecondSplitVehicle.timeToCharge * (secondSplitVehicle.chargeRate / 60 )

            pushToEnd.append( duplicateSecondSplitVehicle )
            # pushToEnd now containts the 2nd half of the first split vehicle and the 1st half of the second split vehicle

        # now move everything that the new vehicle kicks out to the end of the list
        # first put the overlapped part into pushToEnd after the first split part and before the second split part (if it exists)
        pushToEnd[1:1] = tempSched[splitVehicleIndex + 1: secondSplitVehicleIndex] 

        # then delete the remove the overlapped part, add in the new vehicle and append the overlapped part to then end
        del tempSched[splitVehicleIndex+1 : secondSplitVehicleIndex] # remove the overlapped part of the list

        tempSched.insert(splitVehicleIndex + 1, vehicle)  # insert the new vehicle after split vehicle

        startOfMovedTasks = len(tempSched)

        tempSched += pushToEnd # move the ovelapped part to the end

        # update all start times
        for taskIndex, task in enumerate(tempSched[1:]):
            prevTask = tempSched[ taskIndex - 1 ]
            task.startTime = prevTask.startTime + prevTask.timeToCharge


        # now that tempSched is has been updated with the new vehicle and the overlapped part pushed to the end
        # check to see if the profit is better by checking if the 'pushed to end' tasks are finishable before their deadlines

        profitGainedPerPort = vehicle.profit

        for task in tempSched[startOfMovedTasks:]:
            #check to see if task is finishable, if it is not then subtract (penaltyCoefficient * amountNotCharged) from profitGainedPerPort
            timeDifference = task.depTime - ( task.startTime + task.timeToCharge )
            if timeDifference < 0 :
                profitGainedPerPort += common.penaltyCoefficient * (timeDifference / 60.0) * task.chargeRate * common.electricityPrice

            # otherwise add task.profit() to profitGainedPerPort
            else:
                # print task
                # print "task profit: ", task.getProfit()
                profitGainedPerPort += task.getProfit()

        if profitGainedPerPort > profitGained:
            profitGained = profitGainedPerPort
            leastProfitConflictPort = index
            bestSchedule = tempSched

    return [leastProfitConflictPort, bestSchedule]


def chargeable( vehicle ):
    return ( vehicle.depTime >= vehicle.startTime + vehicle.timeToCharge )

# iterates from one minute to the next for the model
def updateVehicles():
    # print "------------ next update -----------"
    
    # check each chargePort
    for index, vehicle in enumerate( chargePorts.chargePorts ):

        if vehicle is not None:
            removed = False

            # add 1 minute of charge
            vehicle.currentCharge += ( vehicle.chargeRate ) / 60.0
            
            minutesCharged[vehicle.id] += 1

            # when would we kick out a vehicle?

            # definitely when it's hit its charge or when one is scheduled to start next
            if ( vehicle.currentCharge >= vehicle.chargeNeeded ) or ( len( schedules[ index ] ) > 1 and schedules[ index ][ 1 ].startTime == common.currentTime ):

                # print "vehicle ", vehicle.id, " is done or the next one is starting"

                # finish up the listener for this vehicle
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )

                # remove finished vehicle from grid and document it
                csvGen.exportVehicleToCSV( vehicle, "SUCCESS" )
                common.doneChargingLot.append( vehicle )
                # print "success: ",vehicle.id
                removed = True

                # remove the vehicle that was charging from the front of the schedule
                del schedules[ index ][ 0 ]

                # now add the next vehicle from the schedule, if possible
                if len( schedules[ index ] ) > 0:

                    # next vehicle
                    nextVehicle = schedules[ index ][ 0 ]
                    while nextVehicle is not None and nextVehicle.depTime < common.currentTime:
                        csvGen.exportVehicleToCSV( nextVehicle, "FAILURE" )
                        common.failedLot.append( nextVehicle )
                        # print "failed here: ", nextVehicle.id
                        del schedules[ index ][ 0 ]
                        nextVehicle = None
                        if len(schedules[ index ]) > 0:
                            nextVehicle = schedules[ index ][ 0 ]

                    if nextVehicle is not None:
                        chargePorts.chargePorts[ index ] = nextVehicle

                        # make new listener
                        chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )
                
                    else:
                        chargePorts.chargePorts[ index ] = None

                # no vehicles to add in schedule
                else:
                    chargePorts.chargePorts[index] = None

            # probably not going to be used, but we can still check for depTime
            if common.currentTime >= vehicle.depTime and not removed:

                # this vehicle is on the out, so wrap up its listener
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )

                # remove finished vehicle and document it
                csvGen.exportVehicleToCSV( vehicle, "FAILURE" )
                common.failedLot.append( vehicle )
                # print "failed here2: ", vehicle.id

                del schedules[ index ][ 0 ]

                # now add the next vehicle from the schedule, if possible
                if len( schedules[ index ] ) > 0:

                    # next vehicle
                    nextVehicle = schedules[ index ][ 0 ]
                    while nextVehicle is not None and nextVehicle.depTime < common.currentTime:
                        # print "vehicle ",nextVehicle.id," was next but its depTime passed"
                        csvGen.exportVehicleToCSV( nextVehicle, "FAILURE" )
                        common.failedLot.append(nextVehicle)
                        # print "failed here3: ", nextVehicle.id

                        del schedules[ index ][ 0 ]
                        nextVehicle = None
                        if len(schedules[ index ]) > 0:
                            nextVehicle = schedules[ index ][ 0 ]

                    if nextVehicle is not None:
                        chargePorts.chargePorts[ index ] = nextVehicle

                        # make new listener
                        chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )
                    else:
                        chargePorts.chargePorts[ index ] = None
                else:
                    chargePorts.chargePorts[ index ] = None


# iterate through all schedules
# returns the index (if possible) of the schedule that will be able to
# accommodate a vehicle within it's deadline with the least amount of extra window
# returns -1 if none are possible
def findAppendableChargePort( vehicle ):
    tightestWindowIndex = -1
    bestWindow = vehicle.depTime - common.currentTime

    # iterate througbh each schedulels
    for index, portSchedule in enumerate( schedules ):

        if len(portSchedule) == 0:
            return index

        # look at last vehicle in each schedule
        currentWindow = vehicle.depTime - scheduleEndTime( index )

        # is this window large enough to charge vehicle, and is it more optimal
        if currentWindow > vehicle.timeToCharge and currentWindow < bestWindow:
            bestWindow = currentWindow
            tightestWindowIndex = index

    return tightestWindowIndex


# gets the departure time for the last vehicle in a schedule
def scheduleEndTime( scheduleIndex ):
    lastItem = len( schedules[ scheduleIndex ] ) - 1
    
    if lastItem != -1:
        return schedules[ scheduleIndex ][ lastItem ].startTime + schedules[ scheduleIndex ][ lastItem ].timeToCharge

    # should never happen, make it break
    raise Exception("Schedule should never be empty here, something is wrong")

# checks to see if any vehicles are still in the schedule
# returns true if all schedules are empty
def schedulesEmpty():
    return all( len( subSchedule ) == 0 for subSchedule in schedules )

def totalProfit():
    declinedIds = set()
    deductedProfit = 0
    for vehicle in common.declinedLot:
        declinedIds.add(vehicle.id)
    profit = 0
    for index,vehicle in enumerate( allVehicles ):
        if( not vehicle.id in declinedIds ):
            currentCharge = vehicle.initialCharge +  minutesCharged[vehicle.id] * vehicle.chargeRate / 60.0
            amountNotReceived = vehicle.chargeNeeded - currentCharge
            profit += (vehicle.chargeNeeded - vehicle.initialCharge) * common.electricityPrice
            if amountNotReceived > 0:
                profit -= common.penaltyCoefficient * common.electricityPrice * amountNotReceived
                deductedProfit += common.penaltyCoefficient * common.electricityPrice * amountNotReceived
    return profit

def listHasVehicleId(list, id):
    for item in list:
        if item.id == id:
            return True
    return False

def uniqueVehicles(lot):
    uniqueIds = set()
    for vehicle in lot:
        uniqueIds.add(vehicle.id)
    return uniqueIds

def schedulesToString():
    output = "["
    for index, schedule in enumerate( schedules ):
        if len( schedule ) == 0:
            output += "None"
        else:
            output += "Occupied"
        if index != len( schedules ) - 1:
            output += ", "
    output += "]"
    return output