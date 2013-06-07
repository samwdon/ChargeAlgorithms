import common
import copy
import math

class Vehicle:
    numVehiclesMade = 0

    def __init__( self, arrivalTime, depTime, chargeNeeded, currentCharge, chargeRate, maxCapacity ):
        self.id = common.numVehiclesMade
        
        # keep tabs of the number of vehicles that have entered the model
        common.numVehiclesMade += 1

        # can't have a negative currentCharge, also keeps the distribution within a range
        if ( 1.0 * currentCharge / maxCapacity ) >= 0:
            if ( 1.0 * currentCharge / maxCapacity ) <= .55:
                self.currentCharge  =   currentCharge
                self.initialCharge  =   currentCharge
            else:
                self.currentCharge  =   .55 * maxCapacity
                self.initialCharge  =   .55 * maxCapacity
        else:
            self.currentCharge  =   0
            self.initialCharge  =   0

        # same goes with chargeRequest
        if ( 1.0 * chargeNeeded / maxCapacity ) >= .8:
            if ( 1.0 * chargeNeeded / maxCapacity ) <= 1:
                self.chargeNeeded   =   chargeNeeded
            else:
                self.chargeNeeded   =   maxCapacity
        else:
            self.chargeNeeded   =   .8 * maxCapacity


        self.timeToCharge = math.ceil( 60 * ( ( self.chargeNeeded - self.currentCharge ) * 1.0 ) / chargeRate )  #linear

        # check to see if it's possible to charge the vehicle within its timespan
        if self.timeToCharge > ( depTime - arrivalTime ):
            self.depTime = arrivalTime + self.timeToCharge + 1
        else:
            self.depTime = depTime

        # parameters for each vehicle, not all are used for each algorithm implementation
        self.arrivalTime         =     arrivalTime
        self.startTime           =     arrivalTime
        self.chargeRate          =     chargeRate
        self.maxCapacity         =     maxCapacity
        self.timeToCharge        =     math.ceil( 60 * ( ( self.chargeNeeded - self.currentCharge ) * 1.0 ) / self.chargeRate )  #linear
        self.totalTime           =     depTime - arrivalTime
        self.freeTime            =     self.totalTime - self.timeToCharge
        self.laxity              =     self.freeTime / self.totalTime
        self.originalLaxity      =     self.freeTime / self.totalTime
        self.profit              =     ( self.timeToCharge / 60.0) * self.chargeRate * common.electricityPrice

        # return self

    def duplicate(self):
        return copy.deepcopy(self)

    def getProfit(self):
        # print "profit function should return ",(self.timeToCharge / 60.0) * self.chargeRate * common.electricityPrice
        return (self.timeToCharge / 60.0) * self.chargeRate * common.electricityPrice

    def toString( self ):
        body =  'ID: ' , self.id , \
                '  initialCharge:  ' , self.initialCharge, \
                '  current charge: ' , self.currentCharge , \
                '  charge needed: ' , self.chargeNeeded , \
                '  departure time: ' , self.depTime , \
                '  laxity: ', self.laxity
        return 

    def toStringID( self ):
        return 'ID: ' + str( self.id ) + '  ' + str( self.depTime )

    def toStringIDL( self ):
        return 'ID: ' + str( self.id ) + '  ' + str( self.laxity )

    # updates the laxity for vehicle. Requires the current time of the simulation
    def updateLaxity( self, currentTime ):
        timeToCharge =  ( self.chargeNeeded - self.currentCharge ) / self.chargeRate
        totalTime    =  self.depTime - currentTime
        freeTime     =  totalTime - timeToCharge

        # in case time ends up, we can't divide by 0
        if totalTime == 0:
            self.laxity = 1
        else:
            self.laxity  =  freeTime / totalTime

    # alter the starting time
    def updateStartTime( self, newStartingTime ):
        self.startTime = newStartingTime

    def resetVehicleCharge( self ):
        self.currentCharge = self.initialCharge
        self.timeToCharge = math.ceil( 60 * ( ( self.chargeNeeded - self.currentCharge ) * 1.0 ) / self.chargeRate )  #linear

    def timeLeftToCharge( self ):
        return math.ceil( 60 * ( ( self.chargeNeeded - self.currentCharge ) * 1.0 ) / self.chargeRate )


 #   def getStartingTime( self ):
 #       return max( self.startTime 

#    def getInfo(self):
#        return [self.arrivalTime, self.depTime, self.chargeNeeded, self.currentCharge, self.chargeRate, self.maxCapacity]