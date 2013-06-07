#import Queue
import common
import csvGen
import chargePorts
import chargeEvent

#fcfsac
schedules = [ [ ] for y in range( chargePorts.numChargePorts ) ]


# ------ FCFSAC ------

# the main implementation of the First Come First Serve algorithm
# takes in an array of arrays of vehicle minutes ( 2-level )
def simulate( arrayOfVehicleArrivals ):

    # reset global variables such as time, done/failed lots
    common.updateGlobals( arrayOfVehicleArrivals )
    global currentTime

    # initialize a CSV document for storing all data
    csvGen.generateCSV( "fcfsAC" )

    # iterate through each vehicle in each minute
    for minute, numVehiclesPerMin in enumerate( arrayOfVehicleArrivals ):
        for vehicle in numVehiclesPerMin:       
            port = chargePorts.openChargePort()

            # in case something wrong with distribution, pull vehicle out of system
            if vehicle.currentCharge > vehicle.chargeNeeded:
                csvGen.exportVehicleToCSV( vehicle, "Charge Not Needed" )
                common.cantChargeLot.append( vehicle )
                continue

            # a port is open so start charging the vehicle
            if port is not None:

                # add to chargePort
                chargePorts.chargePorts[ port ] = vehicle
                schedules[ port ].append(vehicle)

                # initialize a listener object for its charging activity
                chargePorts.chargePortListeners[ port ].insert( 0 , chargeEvent.ChargeEvent( vehicle, common.currentTime ) )

            # no ports are available so put the vehicle in the queue
            else:
                # queue.put( vehicle )

                bestPortInfo     =  findEarliestEndingSchedule()
                bestPortIndex    =  bestPortInfo[ 0 ]      #index
                bestPortEndTime  =  bestPortInfo[ 1 ]      #end time

                # vehicle declined because not enough time to charge
                if vehicle.depTime - bestPortEndTime < vehicle.timeToCharge:
                    csvGen.exportVehicleToCSV( vehicle, "DECLINED" )
                    common.declinedLot.append( vehicle )

                # vehicle appended to best schedule
                else:
                    schedules[ bestPortIndex ].append( vehicle )

        updateVehiclesFCFSAC()
        common.currentTime += 1

    # print "status:  " , openChargePort() , "  " , queue.empty()

    # run the clock until all vehicles have ran through the simulation
    while chargePorts.chargePortsEmpty() == False or not schedulesEmpty():
        updateVehiclesFCFSAC()
        common.currentTime += 1

    # print "FCFSAC: total number of cars: ", common.numberOfVehiclesInSimulation , \
    #   "  elapsed time: " , common.currentTime , \
    #   "  done charging lot: " , len( common.doneChargingLot ) , \
    #   "  failed charging lot: " , len( common.failedLot ) , \
    #   "  cant charge lot: " , len( common.cantChargeLot ) , \
    #   "  declined lot: "  , len( common.declinedLot ) , \
    #   "  fcfsACQueue schedules:  " , schedules , \
    #   "  chargePort " , chargePorts.toString()

    # write a CSV for all the chargePort logs
    csvGen.exportChargePortsToCSV( "fcfsAC" )

    output = [common.calcProfit(), len(common.doneChargingLot), len(common.failedLot), len(common.declinedLot), common.numberOfVehiclesInSimulation, common.currentTime]
    return output

# called to update the vehicles for each minute of simulation
def updateVehiclesFCFSAC():

    # check each chargePort
    for index, vehicle in enumerate( chargePorts.chargePorts ):        

        # add 1 minute of charge
        if vehicle is not None:
            vehicle.currentCharge +=  ( vehicle.chargeRate ) / 60.0
            removed = False;

            # check if done charging
            if vehicle.currentCharge >= vehicle.chargeNeeded:

                # this vehicle is on the out, so wrap up its listener
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )

                # remove finished vehicle from grid and document it
                csvGen.exportVehicleToCSV( vehicle, "SUCCESS" )
                common.doneChargingLot.append( vehicle )
                del schedules[ index ][ 0 ] # remove the vehicle from the schedule
                
                # the next vehicle
                if len( schedules[ index ] ) != 0:

                    nextVehicle = schedules[ index ][ 0 ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # and then make a new listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )

                else:
                    chargePorts.chargePorts[ index ] = None
                removed = True;


            # check if deadline reached, should never happen with admission control           
            if common.currentTime >= vehicle.depTime and not removed:

                # print "current time: ", common.currentTime, " depTime: ", vehicle.depTime, " timeLeft: ", vehicle.timeLeftToCharge()

                # this vehicle is on the out, so wrap up its listener
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )
                
                # remove finished vehicle from grid and document it
                csvGen.exportVehicleToCSV( vehicle, "FAILURE" )               
                common.failedLot.append( vehicle )
                del schedules[ index ][ 0 ] # remove the vehicle for the schedule
                
                # the next vehicle
                if len( schedules[ index ] ) != 0:

                    nextVehicle = schedules[ index ][ 0 ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # and then make a new listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )

                else:
                    chargePorts.chargePorts[ index ] = None

# # looks at done and failed lots, and returns the profits based on the vehicles
# def calcProfit():
#     profit = 0

#     # add up profit from each vehicle in done lot
#     for vehicle in common.doneChargingLot:
#         profit += vehicle.profit

#     # now to deal with vehicles in the failed lot
#     if len( common.failedLot ) > 0:
#         for vehicle in common.failedLot:
#             profit += ( vehicle.profit - ( ( vehicle.chargeNeeded - vehicle.currentCharge ) * common.electricityPrice * common.penaltyCoefficient ) )

#     return profit

# iterate through each schedule and find the one that will have an opening the soonest
# return the index, and the time that the shortest schedule will complete the current tasks
def findEarliestEndingSchedule():

    earliestIndex = -1;
    earliestEndTime = float( "inf" );

    # check each schedule
    for index, portSchedule in enumerate( schedules ):
        length = len( portSchedule );
        
        # there will always be the one charging; make it break if its 0 (a failsafe)
        if length == 0:
            raise Exception("Schedule should never be empty here, something is wrong")

        # this car is already in the chargePort and may have started charging
        endTime = portSchedule[ 0 ].timeLeftToCharge()

        # look at cars scheduled for this chargePort and add time to charge to total time
        for i in range ( 1 , length ):
            endTime += portSchedule[ i ].timeToCharge

        # compare and keep the smallest
        if endTime < earliestEndTime:
            earliestIndex = index
            earliestEndTime = endTime

    return ( earliestIndex , earliestEndTime + common.currentTime )


# returns True if there more vehicles in the schedules
def schedulesEmpty():
    return all( len( subSchedule ) == 0 for subSchedule in schedules )