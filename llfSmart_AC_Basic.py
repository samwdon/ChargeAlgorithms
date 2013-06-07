import common
import csvGen
import chargePorts
import chargeEvent
from operator import attrgetter

llfQueue = []


#  ------ LLF ------

# laxity is defined as freeTime/totalTime where freeTime = (departure - arrival - chargeTime) and totalTime = (departure - arrival) initially )
# laxity needs to be updated each minute where freeTime = ( departure - current time - chargeTime ) and totalTime = ( departure - currentTime )
# 
# for both cases, caluclate totalTime, then free time will just be totalTime - chargeTime.
#
# this is going to work pretty much the same way as EDF, only difference is we need to constantly update the laxity values of each vehicle
# however we are still hanging on to the same index deal as before
#
#    total time =   departure time - current time
#    free time  =  total time - timeToCharge

llfIndex = -1

def simulate( arrayOfVehicleArrivals ):
    
    # reset global variables such as time, done/failed lots
    common.updateGlobals( arrayOfVehicleArrivals )
    global currentTime
    global llfIndex

    # initialize a CSV document for storing all data
    csvGen.generateCSV( "llfSmartACB" )

    # iterate through each vehicle in each minute
    for minute, numVehiclesPerMin in enumerate( arrayOfVehicleArrivals ):
        for vehicle in numVehiclesPerMin:
            port = chargePorts.openChargePort()

            # check if it actually needs to be charged
            if vehicle.currentCharge > vehicle.chargeNeeded:
                csvGen.exportVehicleToCSV( vehicle, "Charge Not Needed" )
                common.cantChargeLot.append( vehicle )
                continue

            # there is an open chargePort, add vehicle to it
            if port is not None:

                # add to chargePort
                chargePorts.chargePorts[ port ] = vehicle

                # initialize a listener object for its charging activity
                chargePorts.chargePortListeners[ port ].insert( 0, chargeEvent.ChargeEvent( vehicle, common.currentTime ) )

            # no open chargePort, append to llfQueue
            else:
                if vehicleCanFit( vehicle ):
                    llfQueue.append( vehicle )

                    # update the llfIndex if this vehicle is better
                    if llfIndex == -1 or vehicle.laxity < llfQueue[ llfIndex ].laxity:
                        llfIndex = len( llfQueue ) - 1
                else:
                    csvGen.exportVehicleToCSV( vehicle, "DECLINED" )
                    common.declinedLot.append( vehicle )

        updateVehiclesLLF()
        common.currentTime += 1

    # vehicles done arriving, now continue with the simulation
    while chargePorts.chargePortsEmpty() == False or not len( llfQueue ) == 0:
        updateVehiclesLLF()
        common.currentTime += 1

    # print "LLF Complex:  total number of cars: ", common.numberOfVehiclesInSimulation , \
    #     "  elapsed time: " , common.currentTime , \
    #     "  done charging lot: " , len( common.doneChargingLot ) , \
    #     "  failed charging lot: " , len( common.failedLot ) , \
    #     "  declined lot: ", len( common.declinedLot ), \
    #     "  cant charge lot: " , len( common.cantChargeLot ) , \
    #     "  llfQueue size:  " , len( llfQueue ) , \
    #     "  chargePort " , chargePorts.toString()
        
    # write the CSV with all the chargePort logs
    csvGen.exportChargePortsToCSV( "llfSmartACB" )

    output = [common.calcProfit(), len(common.doneChargingLot), len(common.failedLot), len(common.declinedLot), common.numberOfVehiclesInSimulation, common.currentTime]
    return output

# called to update the vehicles for each minute of simulation
def updateVehiclesLLF():
    global currentTime
    global llfIndex

    # increment the charge for the cars that were charging
    for index, vehicle in enumerate( chargePorts.chargePorts ):

        # add one minute of charge
        if vehicle is not None:
            vehicle.currentCharge += ( vehicle.chargeRate ) / 60.0

            # print "Charge:  " , vehicle.currentCharge , "   " , vehicle.chargeNeeded
            # print "Timing:  " , currentTime , "   ",  vehicle.depTime 
    
    # update the laxity for all the peeps
    updateLaxityForAll()

    # now move cars around so the laxity property is maintained
    for index, vehicle in enumerate( chargePorts.chargePorts ):
        if vehicle is not None:
            removed = False

            #check if done charging
            if vehicle.currentCharge >= vehicle.chargeNeeded:

                # finish up the listener for this vehicle
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle, common.currentTime )

                # remove finished vehicle and document it
                csvGen.exportVehicleToCSV( vehicle, "SUCCESS" )
                common.doneChargingLot.append( vehicle )
                
                if len( llfQueue ) > 0:

                    # get next vehicle and throw in chargePort
                    nextVehicle = llfQueue[ llfIndex ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # make it a listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle, common.currentTime ) )

                    # update queue
                    del llfQueue[ llfIndex ]  
                    llfIndex = lowestLaxity()

                else:
                    chargePorts.chargePorts[ index ] = None
                removed = True

            # check if deadline reached
            if common.currentTime >= vehicle.depTime and not removed:

                # wrap up the listener
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle, common.currentTime )

                # remove finished vehicle and document it
                csvGen.exportVehicleToCSV( vehicle, "FAILURE" )
                common.failedLot.append( vehicle )
                
                if len( llfQueue ) > 0:

                    # get next vehicle
                    nextVehicle = llfQueue[ llfIndex ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # make it a listener
                    chargePorts.chargePortListeners[ index ].insert( 0, chargeEvent.ChargeEvent( nextVehicle, common.currentTime ) )
                    
                    # update queue
                    del llfQueue[ llfIndex ]
                    llfIndex = lowestLaxity()

                else:
                    chargePorts.chargePorts[ index ] = None

            # check to make sure all the cars in the chargePorts are the best possible choices

            # get index of the worst that is charging
            highestLaxityChargePortIndex = highestLaxityChargePort()

            # check if all cars in chargePorts still have lowest laxity
            while len( llfQueue ) > 0 and highestLaxityChargePortIndex != -1 and llfQueue[ llfIndex ].laxity < chargePorts.chargePorts[ highestLaxityChargePortIndex ].laxity:

                swappingOut = chargePorts.chargePorts[ highestLaxityChargePortIndex ]
                swappingIn  = llfQueue[ llfIndex ]

                # close the listener for swappingOut
                chargePorts.chargePortListeners[ highestLaxityChargePortIndex ][ 0 ].terminateCharge( swappingOut, common.currentTime )

                # swap occurs in the chargePorts
                chargePorts.chargePorts[ highestLaxityChargePortIndex ] = swappingIn
                
                # create a new listener for swappingIn
                chargePorts.chargePortListeners[ highestLaxityChargePortIndex ].insert( 0 , chargeEvent.ChargeEvent( swappingIn , common.currentTime ) )

                # swap finishes up in the queue
                llfQueue[ llfIndex ] = swappingOut

                # now update values for comparison
                llfIndex = lowestLaxity()
                highestLaxityChargePortIndex = highestLaxityChargePort()


# gets index for the vehicle with the lowest laxity from llf
def lowestLaxity():
    if len( llfQueue ) == 0:
        return -1
    return llfQueue.index( min( llfQueue, key = attrgetter( 'laxity' ) ) )

# finds the chargePort with the highest laxity
def highestLaxityChargePort():
    highestLaxityIndex = -1
    highestLaxity = -1
    for index, port in enumerate( chargePorts.chargePorts ):
        if port is not None:
            if port.laxity > highestLaxity:
                highestLaxity = port.laxity
                highestLaxityIndex = index
    return highestLaxityIndex  

# laxity constantly changes as time advances and certain cars are charged
def updateLaxityForAll():

    # first do chargePorts
    for index, vehicle in enumerate( chargePorts.chargePorts ):
        if vehicle is not None:
            vehicle.updateLaxity( common.currentTime )

    # now do the llfQueue
    for index, vehicle in enumerate( llfQueue ):
        vehicle.updateLaxity( common.currentTime )

# Add up all charging time left for vehicles in chargePorts and for vehicles in queue with an earlier deadline
# then divide by number of chargeports to get average time per charge port
def vehicleCanFit( vehicle ):
    totalTime = 0
    for curChargingVehicle in chargePorts.chargePorts:
        if curChargingVehicle is not None:
            totalTime += curChargingVehicle.timeLeftToCharge()
        else:
            raise Exception("Schedule should never be empty here, something is wrong")
    for scheduledVehicle in llfQueue:
        totalTime += scheduledVehicle.timeToCharge

    averageEndTime = (totalTime * 1.0) / chargePorts.numChargePorts
    averageEndTime += common.currentTime

    # returns true if it can fit, false if it cannot
    return averageEndTime < (vehicle.depTime - vehicle.timeToCharge)
