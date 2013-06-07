import csv
import os
import datetime
import common
import chargePorts


# --------- Exporting to CSV -----------

# every time an alrogithm is run, it will create csv files for vehicles and chargePorts
# files will be save in /csv/<algorithm type>/timeStamp/
# NOTE: folderName must be a String of one of our algorihtm names: "fcfs" , "edf" , or "llfSmart" , "llfSimple"

def generateCSV( folderName ):
    if common.csvOn:
        global vehiclePath
        global vehicleCSV
        global timeStamp

        # generate a unique fipame with a time stampg
        timeStamp = datetime.datetime.now().strftime( "%H-%M-%S%f-%m-%d-%Y" )

        # thank stack overflow for making this easy
        # setup file to save in a directory
        script_dir = os.path.dirname( os.path.abspath(__file__) )
        dest_dir = os.path.join( script_dir, 'csv', folderName , timeStamp )    
        try:
                os.makedirs(dest_dir)

        except OSError:
                pass # already exists
        
        # make a CSV for both Vehicle and ChargePorts
        vehiclePath = os.path.join( dest_dir, "vehicles.csv" )
        
        # and now write them up
        vehicleCSV = csv.writer( open( vehiclePath , "wb" ) )

        # write some basic info info in vehicleCSV

        # basic stats
        vehicleCSV.writerow( [ "Interval time" , common.interval , "Number of vehicles" , common.numberOfVehiclesInSimulation ] )

        # initialize some columns
        vehicleCSV.writerow( [ "Vehicle ID" , \
                                             "Status" , \
                                             "Arrival Time" , \
                                             "Departure Time" , \
                                             "Initial Charge" , \
                                             "Current Charge" , \
                                             "Charge Rate" , \
                                             "Charge Level Needed" , \
                                             "Max Capacity" , \
                                             "Charge Time Needed" , \
                                             "Original Free Time" , \
                                             "Original Total Time" , \
                                             "Original Laxity" \
                                                ] )

# when a vehicle is leaving a lot, throw it into the CSV so we can study it
def exportVehicleToCSV( vehicle, status ):
    if common.csvOn:
        global vehiclePath
        global vehicleCSV

        vehicleCSV.writerow( [ vehicle.id , \
                                             status , \
                                             vehicle.arrivalTime , \
                                             vehicle.depTime , \
                                             vehicle.initialCharge , \
                                             vehicle.currentCharge , \
                                             vehicle.chargeRate , \
                                             vehicle.chargeNeeded , \
                                             vehicle.maxCapacity , \
                                             vehicle.timeToCharge , \
                                             vehicle.freeTime , \
                                             vehicle.totalTime , \
                                             vehicle.originalLaxity \
                                             ] )


def exportChargePortsToCSV( folderName ):
    if common.csvOn:
        global chargePortCSV
        global chargePortPath
        global timeStamp

        # should already be built
        # timeStamp = datetime.datetime.now().strftime( "%Y%m%d-%H%M%S" )

        # make and write a CSV file for the logs of each chargePort
        for index, chargePort in enumerate( chargePorts.chargePortListeners ):

                # thank stack overflow for making this easy
                # setup file to save in a directory
                script_dir = os.path.dirname( os.path.abspath( __file__ ) )
                dest_dir = os.path.join( script_dir, 'csv' , folderName , timeStamp , 'chargePorts' )    

                try:
                        os.makedirs(dest_dir)
                except OSError:
                        pass # already exists

                # make file name and reference path
                fileName = 'port' + str( index ) + '.csv'

                # print 'fileName:   ' , fileName

                portPath = os.path.join( dest_dir, fileName )

                # write the file
                portCSV = csv.writer( open( portPath , "wb" ) )

                # basic stats
                portCSV.writerow( [ "Interval time" , common.interval , "Number of charge ports" , chargePorts.numChargePorts ] )

                # initialize some columns for stuff
                # the duplicate Vehicle ID is a parity check. If they don't match, shit broke
                portCSV.writerow( [ "ChargePort Instance ID" , \
                                                        "Start Time" , \
                                                        "End Time" , \
                                                        "Time Charging" , \
                                                        "Initial Charge" , \
                                                        "Charge Requested" , \
                                                        "Vehicle ID" ,  \
                                                        "Vehicle ID" , \
                                                        "Final Charge" \
                                                    ] )

                # iterate through the chargePort and write it all out
                for index, chargeEvent in enumerate( chargePort ):

                        # csvPrep does all the labor
                        portCSV.writerow( chargeEvent.csvPrep() )

def exportSimulationDataToCSV( simulationData , title ):

        # generate a unique fipame with a time stamp
        timeStamp = datetime.datetime.now().strftime( "%H-%M-%S%f-%m-%d-%Y" )

        # thank stack overflow for making this easy
        # setup file to save in a directory
        script_dir = os.path.dirname( os.path.abspath(__file__) )
        dest_dir = os.path.join( script_dir, 'csv', 'simulations' )    
        
        try:
                os.makedirs(dest_dir)
        except OSError:
                pass # already exists

        # make a CSV of it all
        csvPath = os.path.join( dest_dir, title + timeStamp + '.csv' )
        
        # and now write them up
        writeCSV = csv.writer( open( csvPath , "wb" ) )

        # write some basic info info in vehicleCSV

        # columns
        writeCSV.writerow( [ "Arrival Rate" , "FCFS" , "FCFS-AC" , "EDF" , "EDF-AC-Basic" , "EDF-AC-Pro" , "LLFsimple" , "LLFsimple-AC-Basic" , "LLFsimple-AC-Pro" , "LLFsmart" , "LLFsmart-AC" , "DSAC" ] )
        
        # write each row
        for index, simulationRound in enumerate( simulationData ):
                writeCSV.writerow( simulationData[ index ] )
