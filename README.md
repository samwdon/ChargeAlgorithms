Charging Algorithms
================

# About
This repository is part of a research project that I worked on for a semester with [@samwdon](https://github.com/samwdon) through the School of Engineering and Applied Sciences at Washington University in St. Louis.  The goal of the project was to test different scheduling and queueing algorithms to determine which is most effective in charging electric vehicles.  To test the algorithms, we built out this entire simulation and then compared their performance on a few different metrics.

# Simulation
The simulation operates in discrete time at intervals of 1 minute.  Before running an algorithm, we simulate a window in which vehicles will arrive, and then iterate through the simulation minute by minute.  The arrival of vehicles is based on a poisson distribution, which is easily changeable.  In our model, we commonly change the value of the arrival rate, which is the frequency of occurrences of our distribution.
As each algorithm progresses through time, it attempts to make decisions based on its current state.  No algorithm can know the future, and at each interval it only has information about its current state and any vehicle that just arrived.

# Vehicles
To know the best method for charging a vehicle, an algorithm is going to need some information about its needs.  Vehicle objects thus have the following basic properties:
* Arrival time
* Departure time
* Initial charge (amount of KWh upon arrival)
* Charge needed (amount of KWh needed at departure)
* Battery capacity
* Charging rate

Aside from arrival time and charging rate, these values are calculated from a normal distribution.  Arrival time is fixed into the poisson distribtuion, while charging rate is fixed and part of the charge ports.

# The Algorithms
We implemented 11 different algorithms.  These algorithms are built on 5 fundamentally different scheduling approaches.  They are defined as follows:
* FCFS - First Come First Serve - This is just a typical queue, as vehicles are kept in the order in which they arrive.
* EDF - Earliest Deadline First - This is a type of priorty queue.  It prioritizes vehicles based on their deadline.  A vehicle with a deadline approaching will skip up in priority.
* LLF-Simple - Least Laxity First - Laxity is defined as 1 - (time needed to charge / total time available for charging ).  In this version, laxity is calculated when a vehicle enters the simulation and the priority queues use only that initial value for all sorting.
* LLF-Smart - Here laxity is taken slightly differently.  Instead, it is defined as 1 - ( time left to charge / time until deadline ).  The difference between LLF-Smart is that the value of laxity is updated for all vehicles at the end of every discrete interval of simulation.
* DSAC - Decision Scheduling Admission Control - This algorithm was suggested in a [paper](http://acsp.ece.cornell.edu/papers/ChenJiTong12PES.pdf) by researchers at Cornell University.  It adds the ability to admit or decline a vehicle when it arrives.  It will admit a vehicle if it finds that it can increase its projected profit.  This was the most difficult algorithm to write mostly because vehicle objects needed to be cloned, acted upon independently, but updated in unison.

Initially, we built FCFS, EDF, and both of the LLF algorithms where they were required to admit all vehicles.  Since DSAC had the power of admission control, we also created a version of each that took advantage of admission control.  Furthermore, our initial 4 algorithms used 1 queue for all charging ports, whereas DSAC had a separate queue for each port.  To fairly compare DSAC, we implemented an additional admission control algorithm for FCFS, EDF, and LLF-Simple.  It didn't make much sense for LLF-Smart in both implementation or practicality.  These additions brought the total algorithm count to 11; they are as follows:
* FCFS (single queue)
* FCFS-AC (single queue)
* EDF-AC-Basic (single queue)
* EDF-AC-Pro (multiple queues)
* LLF-Simple (single queue)
* LLF-Simple-AC-Basic (single queue)
* LLF-Simple-AC-Pro (multiple queues)
* LLF-Smart (single queue)
* LLF-Smart-AC (single queue)
* DSAC (multiple queues)

The reason the multiple queue algorithms are referred to as pro is that they absolutely guarantee that no failure will ever occur when they admit a vehicle.  The basic ones will make a very accurate guess (about 99%, but not definite).

# Charge Ports
There is no charge port object, we just used an array.  The algorithms perform all swaps between schedules and ports.  For each time a vehicle enters a charge port, a charging activity object is created.  This is stored in an array of the sime size, and just documents how long the vehicle was charging there and what it did.

# Trying It Out
main.py will run all algorithms and return a csv file with some of their performances.  To get started, just pull in this entire repository into an empty directory.  I have been running everything on Python 2.7.2 (standard on Macs); not sure how well previous versions are supported.  When you simulate, you can also get a CSV output on every vehicle and chargePort activity.  I suggest keeping that off for big simulations as it slows everything down a lot.
In main.py, you will have to define some components of your simulation: how many simulations to run, across what intervals, and how many to run for an average.
main.py will take in an integer, which is the interval of time that vehicles can arrive.

# More Information
A full write up on our findings plus a better explanation of this model will be available on a separate website soon.  In the meantime, please email hess@wustl.edu with any questions.