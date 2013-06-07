# a chargingEvent is the basic object used for logging what's going on with each chargePort
# We will be using an array that's the same length of chargePorts
# each index will contain an array of chargingEvents
# the first index of this array will be the chargePort's log of the first vehicle that it dealth with
# the last index of these arrays will log the most recent chargingEvent for that specific chargePort

# to create, pass in the vehicle and currentTime
# when a vehicle is done charging, it will need the updated version of the same vehicle and again the currentTime

# readouts of -1 for endTime, endVehicle, and timeCharging will denote that it's either still listening or something went very wrong

import vehicle

class ChargeEvent:
    numEvents = 0

    def __init__( self, vehicle, startTime ):

        # parameters for each vehicle, not all are used for each algorithm implementation
        self.id                 =     ChargeEvent.numEvents 
        self.startTime          =     startTime                 # the time that this vehicle began charging
        self.initialVehicle     =     vehicle                   # we wil have all the stats of our vehicle object when it entered
        self.endTime            =     -1                        # update to endTime
        self.endVehicle         =     -1                        # will write its properties when it exits
        self.timeCharging       =     -1

        # keep tabs of the number of vehicles that have entered the model
        ChargeEvent.numEvents += 1

    # when the vehicle is done charging, we'll gather its stats
    def terminateCharge( self, vehicle, currentTime ):
        self.endTime        =   currentTime
        self.endVehicle     =   vehicle
        self.timeCharging   =   currentTime - self.startTime

    # probably useful to have
    def toString( self ):

        body = ''

        # ID
        body += 'ID: ' , self.id , ' '
        
        # Start time
        body += 'Start time: ' , self.startTime , ' '

        # End time ( will be -1 if there's an issue )
        body += 'End time: ' , self.endTime , ' '

        # Initial Charge
        body += 'Initial charge: ' , self.initialCharge , ' '

        # Time charging ( will be -1 if there's an issue )
        body += 'Time charging: ' , self.timeCharging , ' '

        # Charge Needed
        body += 'Charge needed: ' , self.initialVehicle.chargeNeeded , ' '

        # Initial Vehicle ID
        body += 'Vehicle ID: ' , self.initialVehicle.id , ' '

        # check if it exists to avoid an error
        if self.endVehicle != -1:

            # End Vehicle ID ( parity check )
            body += 'End Vehicle ID: ' , self.endVehicle.id , ' '

            # Final Charge
            body += 'Final charge: ' , self.endVehicle.currentCharge

        else:
            body += 'Unable to locate end vehicle'
            
        return body

    # this will be a line in the CSV file, just have writerow jot down this stuff
    # everything is tossed into an array and then the array is returned
    def csvPrep( self ):

        row = []

        # first write down what we can
        
        # ID
        row.append( self.id )
        
        # Start time
        row.append( self.startTime )

        # End time ( will be -1 if there's an issue )
        row.append( self.endTime )

        # Time charging ( will be -1 if there's an issue )
        row.append( self.timeCharging )

        # Initial Charge
        row.append( self.initialVehicle.initialCharge )

        # Charge Needed
        row.append( self.initialVehicle.chargeNeeded )

        # Initial Vehicle ID
        row.append( self.initialVehicle.id )

        # check it exists to avoid an error
        if self.endVehicle != -1:

            # End Vehicle ID ( parity check )
            row.append( self.endVehicle.id )

            # Final Charge
            row.append( self.endVehicle.currentCharge )

        # in case we lost vehicle ID, still fill up row
        else:
            row.append( -1 )
            row.append( -1 )

        return row

