import Queue
import common
import csvGen
import chargePorts
import chargeEvent

#fcfs
queue = Queue.Queue( 0 )


# ------ FCFS ------

# the main implementation of the First Come First Serve algorithm
# takes in an array of arrays of vehicle minutes ( 2-level )
def simulate( arrayOfVehicleArrivals ):
    
    # reset global variables such as time, done/failed lots
    common.updateGlobals( arrayOfVehicleArrivals )
    global currentTime

    # initialize a CSV document for storing all data
    csvGen.generateCSV( "fcfs" )

    # iterate through each vehicle in each minute
    for minute, numVehiclesPerMin in enumerate( arrayOfVehicleArrivals ):
        for vehicle in numVehiclesPerMin:       
            port = chargePorts.openChargePort()

            if vehicle.currentCharge > vehicle.chargeNeeded:
                csvGen.exportVehicleToCSV( vehicle, "Charge Not Needed" )
                common.cantChargeLot.append( vehicle )
                continue

            # a port is open so start charging the vehicle
            if port is not None:

                # add to chargePort
                chargePorts.chargePorts[ port ] = vehicle
            
                # initialize a listener object for its charging activity
                chargePorts.chargePortListeners[ port ].insert( 0 , chargeEvent.ChargeEvent( vehicle, common.currentTime ) )
                
            # no ports are available so put the vehicle in the queue
            else:
                queue.put( vehicle )

        updateVehiclesFCFS()
        common.currentTime += 1

    # print "status:  " , openChargePort() , "  " , queue.empty()
    
    # run the clock until all vehicles have ran through the simulation
    while chargePorts.chargePortsEmpty() == False or not queue.empty():
        updateVehiclesFCFS()
        common.currentTime += 1

    # print "FCFS: total number of cars: ", common.numberOfVehiclesInSimulation , \
    #     "  elapsed time: " , common.currentTime , \
    #     "  done charging lot: " , len( common.doneChargingLot ) , \
    #     "  failed charging lot: " , len( common.failedLot ) , \
    #     "  cant charge lot: " , len( common.cantChargeLot ) , \
    #     "  fcfsQueue size:  " , queue.qsize() , \
    #     "  chargePort " , chargePorts.toString()

    # write a CSV for all the chargePort logs
    csvGen.exportChargePortsToCSV( "fcfs" )
    
    output = [common.calcProfit(), len(common.doneChargingLot), len(common.failedLot), len(common.declinedLot), common.numberOfVehiclesInSimulation, common.currentTime]
    return output

# called to update the vehicles for each minute of simulation
def updateVehiclesFCFS():

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
                
                # the next vehicle
                if not queue.empty():

                    nextVehicle = queue.get()
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # and then make a new listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )

                else:
                    chargePorts.chargePorts[ index ] = None
                removed = True;


            # check if deadline reached            
            if common.currentTime >= vehicle.depTime and not removed:

                # this vehicle is on the out, so wrap up its listener
                chargePorts.chargePortListeners[ index ][ 0 ].terminateCharge( vehicle , common.currentTime )
                
                # remove finished vehicle from grid and document it
                csvGen.exportVehicleToCSV( vehicle, "FAILURE" )               
                common.failedLot.append( vehicle )
                
                # the next vehicle
                if not queue.empty():

                    nextVehicle = queue.get()
                    chargePorts.chargePorts[ index ] = nextVehicle

                    # and then make a new listener
                    chargePorts.chargePortListeners[ index ].insert( 0 , chargeEvent.ChargeEvent( nextVehicle , common.currentTime ) )

                else:
                    chargePorts.chargePorts[ index ] = None
