import itertools


def getAllPossibleSubSchedulesOld(schedule, minSize):
    fullSet = set()
    getAllPossibleSubSchedulesHelper(schedule, minSize, fullSet)
    # return [list(x) for x in set(tuple(x) for x in fullSet)] 
    fullList = []
    for item in fullSet:
        fullList.append(list(item))
    return fullList

# recursive method to get all sub-schedules (order matters) of sizes: (n-1, n-2, ... , numLargerVehicles)
# works by iterating through list, removing one element and finding all permutations of each smaller list
# while recursively calling the method again on each smaller list, this method will return duplicates so that has to be checked
def getAllPossibleSubSchedulesHelper( schedule, minSize, fullSet ):
    if len(schedule) == minSize:
        return fullSet
    else:
        newSubSchedules = set()
        for index,vehicle in enumerate(schedule):
            curTuple = schedule[0:index] + schedule[index+1:]
            for combo in itertools.permutations(curTuple):
                newSubSchedules.add(combo)
                fullSet.add(combo)
        for newSubSchedule in newSubSchedules:
            getAllPossibleSubSchedulesHelper( newSubSchedule, minSize, fullSet)


# iterative method, much faster
def getAllPossibleSubSchedules( schedule, minSize):
    fullSet = set()
    curSet = set()
    curSet.add(tuple(schedule))
    for i in reversed(range(minSize, len(schedule))):
        permutations = set()
        # print "curSet: ",curSet
        for curTuple in curSet:
            permutationsList = list(itertools.permutations(curTuple, i))
            for permutation in permutationsList:
                permutations.add(permutation)
        # print "permutations: ",permutations
        # print "-------"
        curSet = set()
        for permutation in permutations:
            curSet.add(permutation)
            fullSet.add(permutation)
    fullList = []
    for item in fullSet:
        fullList.append(list(item))
    return fullList

# this is the fastest of them all but it still can't handle numbers larger than 10 very well
# uses memory allocation better so it is faster
def allPermutations(seq):
    return (x for i in range(len(seq),0,-1) for x in itertools.permutations(seq, i))

schedule = range(10)

# mySet = getAllPossibleSubSchedulesOld(schedule, 1)
mySet = list(allPermutations(schedule))
print " length: ", len(mySet)

















