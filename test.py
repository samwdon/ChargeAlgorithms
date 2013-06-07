import sys
import common
import fcfs
import fcfs_AC
import edf
import edf_AC_Basic
import edf_AC_Pro
import llfSimple
import llfSimple_AC_Basic
import llfSimple_AC_Pro
import llfSmart
import llfSmart_AC_Basic
import dsac
import poissonGen
import csvGen
import gc
import vehicle
import chargePorts

if len( sys.argv ) != 2:
    print 'Wrong Number of Arguments you sent', sys.argv , " .. just interval" 
    sys.exit()  

interval = int( sys.argv[ 1 ] )
common.setInterval(interval)

def simulateArrivalChargePorts():

    arrivalRate = 3
    initialChargePorts = 1

    arrivalRateStep = 0
    chargePortStep  = 5

    chargePortCycles = 5
    arrivalRateCycles = 1

    numRunsPerIteration = 3

    heatMap = [ ]

    # gen 1st row of heatMap
    # for now just write the name of the algorithm in by hand for cell (0,0)
    row1 = [ "DSAC" ]

    numChargePorts = initialChargePorts

    for a in range( 1, chargePortCycles + 1 ):
        row1.append( numChargePorts )
        numChargePorts += chargePortStep

    heatMap.append( row1 )

    for i in range( arrivalRateCycles ):
        poissonGen.setArrivalRate( arrivalRate )
        numChargePorts = initialChargePorts

        heatMapRow = [ arrivalRate ]

        for j in range( chargePortCycles ):

            chargePorts.setNumChargePorts( numChargePorts )
            averageProfit = 0

            for k in range( numRunsPerIteration ):

                gc.collect()
                # print "--------------------------"

                simulationInterval = poissonGen.simulateInterval()

                # test one algorithm at a time
                singleTestData = dsac.simulate( simulationInterval )

                # increment profit in spot
                averageProfit += singleTestData[ 0 ]

            # get average 
            averageProfit /= ( 1.0 * numRunsPerIteration )

            heatMapRow.append( averageProfit )
            numChargePorts += chargePortStep

        heatMap.append( heatMapRow )
        arrivalRate += arrivalRateStep

    return heatMap

print simulateArrivalChargePorts()