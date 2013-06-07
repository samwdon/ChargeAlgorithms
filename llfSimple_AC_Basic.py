import common
import csvGen
import chargePorts
import chargeEvent
from operator import attrgetter

llfSimpleQueue = []

#  ------ LLF SIMPLE --------
# This algorithm runs under the same premise as the other LLF algorithm except in this instance laxity is only computed once
# upon arrival
# laxity is still defined as freeTime/totalTime where freeTime = (departure - arrival - chargeTime) and totalTime = (departure - arrival) 
# However, since laxity is only calculated once, if a car has a small laxity there is a good chance that it will never be charged 

llfSimpleIndex = -1

def simulate( arrayOfVehicleArrivals ):
    
    # reset global variables such as time, done/failed lots
    common.updateGlobals( arrayOfVehicleArrivals )
    global currentTime
    global llfSimpleIndex

    # initialize a CSV document for storing all data
    csvGen.generateCSV( "llfSimpleACB" )

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

                # make listener
                chargePorts.chargePortListeners[ port ].insert( 0 , chargeEvent.ChargeEvent( vehicle , common.currentTime ) )

            # no open chargePort, append to llfQueue
            else:
                if vehicleCanFit( vehicle ):
                    llfSimpleQueue.append( vehicle )
                    # update the llfIndex if this vehicle is better
                    if llfSimpleIndex == -1 or vehicle.laxity < llfSimpleQueue[ llfSimpleIndex ].laxity:
                        llfSimpleIndex = len( llfSimpleQueue ) - 1
                else:
                    csvGen.exportVehicleToCSV( vehicle, "DECLINED" )
                    common.declinedLot.append( vehicle )

        updateVehiclesLLFSimple()
        common.currentTime += 1

    # vehicles done arriving, now continue with the simulation
    while chargePorts.chargePortsEmpty() == False or len( llfSimpleQueue ) != 0:
        updateVehiclesLLFSimple()
        common.currentTime += 1

    # print "LLF Simple AC Basic: total number of cars: ", common.numberOfVehiclesInSimulation , \
    #     "  elapsed time: " , common.currentTime , \
    #     "  done charging lot: " , len( common.doneChargingLot ) , \
    #     "  failed charging lot: " , len( common.failedLot ) , \
    #     "  declined lot: ", len( common.declinedLot ), \
    #     "  cant charge lot: " , len( common.cantChargeLot ) , \
    #     "  llfQueue size:  " , len( llfSimpleQueue ) , \
    #     "  chargePort " , chargePorts.toString()
        
    # write a CSV of all the data in chargePortListeners
    csvGen.exportChargePortsToCSV( "llfSimpleACB" )

    output = [common.calcProfit(), len(common.doneChargingLot), len(common.failedLot), len(common.declinedLot), common.numberOfVehiclesInSimulation, common.currentTime]
    return output


# called to update the vehicles for each minute of simulation
def updateVehiclesLLFSimple():
    global currentTime
    global llfSimpleIndex

    # increment the charge for the cars that were charging
    for index, vehicle in enumerate( chargePorts.chargePorts ):

        # add one minute of charge
        if vehicle is not None:
            vehicle.currentCharge += ( vehicle.chargeRate ) / 60.0

    # now move cars around so the laxity property is maintained
    for index, vehicle in enumerate( chargePorts.chargePorts ):
        if vehicle is not None:
            removed = False

            #check if done charging
            if vehicle.currentCharge >= vehicle.chargeNeeded:

                # finish up listener
                chargePorts.chargePortListeners[ index][ 0 ].terminateCharge( vehicle , common.currentTime )

                # remove finished vehicle from grid, document it
                csvGen.exportVehicleToCSV( vehicle, "SUCCESS" )
                common.doneChargingLot.append( vehicle )
                
                if len( llfSimpleQueue ) > 0:

                    # get next vehicle, throw in chargePort
                    nextVehicle = llfSimpleQueue[ llfSimpleIndex ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # make it a listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle, common.currentTime ) )
                    
                    # update queue
                    del llfSimpleQueue[ llfSimpleIndex ]  
                    llfSimpleIndex = lowestLaxity()

                else:
                    chargePorts.chargePorts[ index ] = None
                removed = True 

            # check if deadline reached
            if common.currentTime >= vehicle.depTime and not removed:

                # wrap up listener
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )

                # remove finished vehicle, document it
                csvGen.exportVehicleToCSV( vehicle, "FAILURE" )
                common.failedLot.append( vehicle )
        
                if len( llfSimpleQueue ) > 0:

                    # get next vehicle
                    nextVehicle = llfSimpleQueue[ llfSimpleIndex ]
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # make new listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )

                    # update queue 
                    del llfSimpleQueue[ llfSimpleIndex ]
                    llfSimpleIndex = lowestLaxity() # function defined in LLF section, iterates through llfQueue for lowest laxity

                else:
                    chargePorts.chargePorts[ index ] = None

            highestLaxityChargePortIndex = highestLaxityChargePort()

            # check if all cars in chargePorts still have lowest laxity
            while len( llfSimpleQueue ) > 0 and highestLaxityChargePortIndex != -1 and llfSimpleQueue[ llfSimpleIndex ].laxity < chargePorts.chargePorts[ highestLaxityChargePortIndex ].laxity:

                swappingOut = chargePorts.chargePorts[ highestLaxityChargePortIndex ]
                swappingIn  = llfSimpleQueue[ llfSimpleIndex ]

                # close the listener for swappingOut
                chargePorts.chargePortListeners[ highestLaxityChargePortIndex ][ 0 ].terminateCharge( swappingOut , common.currentTime )

                # swap occurs in chargePorts
                chargePorts.chargePorts[ highestLaxityChargePortIndex ] = swappingIn

                # create a new listener
                chargePorts.chargePortListeners[ highestLaxityChargePortIndex ].insert( 0 , chargeEvent.ChargeEvent( swappingIn , common.currentTime ) )

                # swap occurs in the queue
                llfSimpleQueue[ llfSimpleIndex ] = swappingOut

                # now update values for comparison
                llfSimpleIndex = lowestLaxity()
                highestLaxityChargePortIndex = highestLaxityChargePort()


# gets index for the vehicle with the lowest laxity from llf
def lowestLaxity():
    if len( llfSimpleQueue ) == 0:
        return - 1
    return llfSimpleQueue.index( min( llfSimpleQueue, key = attrgetter( 'laxity' ) ) )

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

# Add up all charging time left for vehicles in chargePorts and for vehicles in queue with an earlier deadline
# then divide by number of chargeports to get average time per charge port
def vehicleCanFit( vehicle ):
    totalTime = 0
    for curChargingVehicle in chargePorts.chargePorts:
        if curChargingVehicle is not None:
            totalTime += curChargingVehicle.timeLeftToCharge()
        else:
            raise Exception("Schedule should never be empty here, something is wrong")
    for scheduledVehicle in llfSimpleQueue:
        totalTime += scheduledVehicle.timeToCharge

    averageEndTime = (totalTime * 1.0) / chargePorts.numChargePorts
    averageEndTime += common.currentTime

    # returns true if it can fit, false if it cannot
    return averageEndTime < (vehicle.depTime - vehicle.timeToCharge)

