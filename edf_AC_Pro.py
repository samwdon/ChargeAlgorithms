import common
import csvGen
import chargePorts
import chargeEvent
from operator import attrgetter

schedules =  [ [ ] for y in range( chargePorts.numChargePorts ) ]
edfQueue = []

#  ------ EDF ------

earliestDLIndex = -1;

# simulates EDF with the queues for each chargePort
def simulate( arrayOfVehicleArrivals ):

    #global schedules

    # reset global variables such as time, done/failed lots
    common.updateGlobals( arrayOfVehicleArrivals )
    global currentTime
    # global earliestDLIndex

    # initialize a CSV document for storing all data
    csvGen.generateCSV( "edfPro" )

    # iterate through each vehicle in each minute
    for minute, numVehiclesPerMin in enumerate( arrayOfVehicleArrivals ):
        for vehicle in numVehiclesPerMin:
            port = chargePorts.openChargePort()

            # check if it actually needs to be charged
            if vehicle.currentCharge > vehicle.chargeNeeded:
                csvGen.exportVehicleToCSV( vehicle, "Charge Not Needed" )
                common.cantChargeLot.append( vehicle )
                continue

            # a port is open so start charging the vehicle
            if port is not None:

                # add to chargePort and schedule
                chargePorts.chargePorts[ port ] = vehicle
                schedules[ port ].insert( 0 , vehicle )

                if len( schedules[ port ] ) > 1:
                    print "empty chargePort, but shit was scheduled to be there"
                    break

                # initialize a listener object for its charging activity
                chargePorts.chargePortListeners[ port ].insert( 0 , chargeEvent.ChargeEvent( vehicle, common.currentTime ) )

            # no ports available so try to put it in a queue, but have to find one that will work
            else:

                bestSchedule = -1
                scheduleFlex = float( "inf" );
                
                # iterate through every schedule
                for index, schedule in enumerate( schedules ):

                    # insert a vehicle in the schedule and get its admission feasibility
                    insertLocation =  insertIntoSchedule( vehicle , index )
                    insertLocation = int( insertLocation )
                    admissionTest  =  genAdmissionFeasiblity( index )
                   
                    # will it work?
                    tempFlex = admissionFeasibility( index , admissionTest )

                    # check if it can work for this sched
                    if tempFlex == False:

                        # if it can't work, delete from schedule and move on
                        del schedules[ index ][ insertLocation ]
                        continue

                    # now check if it's the best one
                    if tempFlex < scheduleFlex:
                        scheduleFlex = tempFlex
                        bestSchedule = index

                    # regardless, delete from schedule for now
                    del schedules[ index ][ insertLocation ]

                # now will we do an official insert? or decline
                if bestSchedule >= 0 and scheduleFlex > 0:
                    insertIntoSchedule( vehicle , bestSchedule )

                # decline
                else:
                    csvGen.exportVehicleToCSV( vehicle, "DECLINED" )
                    common.declinedLot.append( vehicle )

        updateVehiclesEDFPro()
        common.currentTime += 1

    # vehicles done arriving, now continue with the simulation
    while chargePorts.chargePortsEmpty() == False or not schedulesEmpty():
        updateVehiclesEDFPro()
        common.currentTime += 1

    # print "EDFPro: total number of cars: ", common.numberOfVehiclesInSimulation , \
    #     "  elapsed time: " , common.currentTime , \
    #     "  done charging lot: " , len( common.doneChargingLot ) , \
    #     "  failed charging lot: " , len( common.failedLot ) , \
    #     "  declined lot: ", len( common.declinedLot ), \
    #     "  cant charge lot: " , len( common.cantChargeLot ) , \
    #     "  schedules:  " , schedulesEmpty() , \
    #     "  chargePort " , chargePorts.toString()

    # write a CSV with all the chargePort logs
    csvGen.exportChargePortsToCSV( "edfPro" )
    
    output = [common.calcProfit(), len(common.doneChargingLot), len(common.failedLot), len(common.declinedLot), common.numberOfVehiclesInSimulation, common.currentTime]
    return output


# takes in a scheduleIndex and returns an array with predicted times for
#   each vehicle to finish charging
def genAdmissionFeasiblity( index ):
    
    endTimes = []
    endingTime = common.currentTime

    # iterate through the schedule, for each car, add end time to array
    for i, vehicle in enumerate( schedules[ index ] ):

        # update endingTime for the next vehicle, add it to endTimes
        endingTime += vehicle.timeToCharge + 1
        endTimes.append( endingTime )

    # now have an array of scheduled endTimes for each vehicle
    # index matches with index of vehicle in sorted schedule
    return endTimes


# properly inserts a vehicle into a schedule, returns its index
# maintains a properly sorted schedule, based on deadlines 
def insertIntoSchedule( vehicle, scheduleIndex ):

    reference = -1
    depTime = vehicle.depTime
    spotted = False

    # if there's stuff there, we'll search through and find the spot to insert
    if len( schedules[ scheduleIndex ] ) > 0:

        # try finding a spot to insert
        for index, car in enumerate( schedules[ scheduleIndex ] ):

            if not spotted and depTime <= car.depTime:
                reference =  index
                spotted   =  True
                break

        # now try and insert

        # found a spot in the middle of the deal
        if spotted:
            schedules[ scheduleIndex ].insert( reference , vehicle )

        # it needs to go at the end
        else:
            spotted = True
            reference = len( schedules[ scheduleIndex ] )
            schedules[ scheduleIndex ].append( vehicle )

    # otherwise there's nothing and we can just throw it in
    else:
        reference =  0
        spotted   =  True
        schedules[ scheduleIndex ].append( vehicle )

    # a quick QA check:
    if len( schedules[ scheduleIndex ] ) > 1:
        prev = schedules[ scheduleIndex ][ 0 ]
        for i in range( 1 , len( schedules[ scheduleIndex ] ) ):
            # the prev car should always have a depTime <= to current
            if prev.depTime > schedules[ scheduleIndex ][ i ].depTime:
                return "insert not working, schedules out of order"
            
            # update prev
            prev = schedules[ scheduleIndex ][ i ]

    if spotted and reference >= 0:
        return reference
    else:
        return "insert isn't working right"


# takes in an index and a list of scheduled end times for vehicles
# returns False if it can't fit, the "flexibility" if it can
# a lower flexibility indicates a tighter fit
def admissionFeasibility( scheduleIndex , feasibilityArray ):

    # first make sure our comparison arrays match up
    if len( schedules[ scheduleIndex ] ) != len( feasibilityArray ):
        return "comparison arrays aren't same length"

    flexibility = float( "inf" );

    # iterate through arrays, comparing depTimes with predicted end charging times
    for index, vehicle in enumerate( schedules[ scheduleIndex ] ):

        tempFlex = vehicle.depTime - feasibilityArray[ index ]

        # can it finish before depTime?
        if tempFlex < 0:
            return False

        if tempFlex < flexibility:
            flexibility = tempFlex

    return flexibility


# returns True if there more vehicles in the schedules
def schedulesEmpty():
    return all( len( subSchedule ) == 0 for subSchedule in schedules )


# update vehicles for the pro edf algorithm
def updateVehiclesEDFPro():
    #global schedules

    # cheack each chargePort
    for index, vehicle in enumerate( chargePorts.chargePorts ):

        # add one minute of charge
        if vehicle is not None:
            vehicle.currentCharge += ( vehicle.chargeRate ) / 60.0
            removed = False

            #check if done charging
            if vehicle.currentCharge >= vehicle.chargeNeeded:

                # finish up the listener for this vehicle
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )

                # remove finished vehicle from grid and document it
                csvGen.exportVehicleToCSV( vehicle, "SUCCESS" )
                common.doneChargingLot.append( vehicle )

                del schedules[ index ][ 0 ] # remove the vehicle from the schedule
                
                # the next vehicle
                if len( schedules[ index ] ) > 0:

                    # get next vehicle and throw in chargePort
                    nextVehicle = schedules[ index ][ 0 ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # make it a listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )

                else:
                    chargePorts.chargePorts[ index ] = None
                removed = True


            # check if deadline reached
            # shouldn't run into this with adminControl, but practice safe algorithms
            if common.currentTime >= vehicle.depTime and not removed:

                # this vehicle is on the out, so wrap up its listener
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )

                # remove finished vehicle and document it
                csvGen.exportVehicleToCSV( vehicle, "FAILURE" )
                common.failedLot.append( vehicle )
                del schedules[ index ][ 0 ] # remove the vehicle for the schedule
                
                if len( schedules[ index ] ) > 0:

                    # get nextVehicle
                    nextVehicle = schedules[ index ][ 0 ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # make new listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )

                else:
                    chargePorts.chargePorts[ index ] = None

        # a quick QA check
        if len( schedules[ index ] ) > 1:
            prev = schedules[ index ][ 0 ]
            for i in range( 1 , len( schedules[ index ] ) ):
                # the prev car should always have a depTime <= to current
                if prev.depTime > schedules[ index ][ i ].depTime:
                    return "insert not working, schedules out of order"
                
                # update prev
                prev = schedules[ index ][ i ]


    # there are cases when a new car arrived with the earliestDL, but all swaps are done at discrete intervals
    # in this case, it is currently at index 0, but not being charged. This part will change that

    # look through each schedule
    for index, schedule in enumerate( schedules ):

        # compare schedule[ 0 ].depTime with that in the chargePort. swap out if different
        if len( schedule ) > 0:
            if schedule[ 0 ].depTime < chargePorts.chargePorts[ index ].depTime:

                # close the listener for swappingOut
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( chargePorts.chargePorts[ index ] , common.currentTime )

                # swap occurs in the chargePorts
                chargePorts.chargePorts[ index ] = schedules[ index ][ 0 ]

                # create a new listener for the vehicle that just got swapped in
                chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( schedules[ index ][ 0 ] , common.currentTime ) )


# takes in an index and  prints out a specific schedule from schedules
def scheduleToString( index ):
    statement = "[ "
    for position, vehicle in enumerate( schedules[ index ] ):
        statement += vehicle.toStringID()
        statement += " , "
    return statement + " ] "

