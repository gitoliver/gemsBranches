#!/usr/bin/env python3
from enum import Enum, auto
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
from pydantic.schema import schema
from gemsModules.common.loggingConfig import *
from gemsModules.common.transaction import *
from gemsModules.project.projectUtil import *

if loggers.get(__name__):
    pass
else:
    log = createLogger(__name__)


##    Enums

##    @class JobStatusEnum(str, Enum)
#    @brief    The possible statuses of a given job.
class JobStatusEnum(str, Enum):
    new = "new"
    building = "building"
    ready = "ready"
    submitted = "submitted"
    complete = "complete"
    failed = "failed"
    delayed = "delayed"



##    @class RotamerConformation
#    @brief    An object that represents a single requested pose for a single linkage
class RotamerConformation(BaseModel):
    ##Linkage Labels may be arbitrary, but they must be unique.
    linkageLabel : str = ""
    dihedralName : str = ""
    rotamer : str = ""

##   @class BuildState
#    @brief An object that represents one requested build state.
#    @TODO: Add more fields, ringPucker, protonationState, etc...
class BuildState(BaseModel):
    ## Labels may be either "structure" if there is only one for this project.
    #    or, they may be a terse label,
    #    or they may be uuids if the terse label is > 32 char long.
    structureLabel : str = ""
    simulationPhase : SimulationPhaseEnum = Field(
        "gas-phase",
        title = "Type",
        alias = "type",
        description = "The possible simulation phases, example: gas-phase or solvent."
        ) ##Use an enum here. gas-phase, solvent

    status : JobStatusEnum = Field(
        None,
        title = "status",
        alias = "status",
        description = "The possible statuses of a given job."
        ) ##Use an enum here. new, building, ready, submitted, complete, failed, delayed

    date : datetime = None
    addIons : str = "default" ## Is there a benefit for this to be a String? Boolean?
    energy : str = None ## kcal/mol
    forceField : str = None ## TODO: This needs to be a class. Schedule design with Lachele.
    sequenceConformation : List[RotamerConformation] = None

##    @class StructureInfo
#    @brief An object to represent the data previously held in the Structure_Mapping_Table.
#    @detail This object holds the data that describes a series of ways that this single structure
#            has been built. Each variation of a rotamer or from gas-phase to solvated, etc...
#            represents a different build state, and each gets a record in this object.
#            This object can be used to track a request, and a copy of it could be used to track 
#            the progress of that requested series of jobs.
class StructureInfo(BaseModel):
    ## Useful to know what this all applies to.
    sequence : str = ""
    ## A build state is a descriptive object that can be used to request a pdb file 
    #    of a sequence in a specific pose, with various other settings as well.
    buildStates : List[BuildState] = None


##  @brief Object for tracking the parsing of rotamerData
#   @param rotamerData is list of nested dict objects from the frontend that 
#          represents user's rotamer selections.
#   @TODO: Move this to a better file for this stuff.
class RotamerCounter():
    linkages = []
    activeLevel = 0
    rootHits = 0

    def __init__(self, rotamerData):
        for linkage in rotamerData:
            label = linkage['linkageLabel']
            for dihedral in linkage['dihedrals']:
                name = dihedral['dihedralName']
                count = len(dihedral['selectedRotamers'])
                log.debug("count: " + str(count))
                thisLinkageCountingObj = {
                    'label' : label,
                    'dihedral' : name,
                    'count' : count,
                    'currentIndex' : count - 1
                }
                self.linkages.append(thisLinkageCountingObj)

        ## Instantiate to the index of the last element in the list.
        self.activeLevel = len(self.linkages) - 1


    def __str__(self):
        result = "\nactiveLevel: " + str(self.activeLevel)
        result = result + "\nlinkages: " 
        for linkage in self.linkages:
            result = result + "\n" + str(linkage)

        return result


##  @brief  Makes decisions about what rotamers the next sequence should use.
#   @detail Behaves like an odometer: iteration needs to allow for rotamer reuse after
#           a reset. Between resets, decrements are used.
#   @param  rotamerCounter
#   @TODO: Move this to a better file for this stuff.
def decrementCounters(rotamerCounter):
    log.info("decrementCounters() was called.")
    leafNode = rotamerCounter.linkages[len(rotamerCounter.linkages) - 1]

    if leafNode['currentIndex'] == 0:
        updateCount = 1
        thisIndex = len(rotamerCounter.linkages) - 1

        #All decrementing work to be done above the active level.
        while thisIndex > rotamerCounter.activeLevel:
            rotamerCounter.linkages[thisIndex]['currentIndex'] = rotamerCounter.linkages[thisIndex]['count'] - 1
            thisIndex = thisIndex - 1

        ## The active linkage.
        activeLinkage = rotamerCounter.linkages[rotamerCounter.activeLevel]
        ## reset active linkage and increment its parent once.
        activeLinkage['currentIndex'] = activeLinkage['count'] - 1

        ## decrement the parent, when appropriate.
        parentIndex = rotamerCounter.activeLevel - 1
        parentLinkage = rotamerCounter.linkages[parentIndex]
        if parentIndex > 0:
            parentLinkage['currentIndex'] = parentLinkage['currentIndex'] - 1
            rotamerCounter.activeLevel = parentIndex
        elif parentIndex == 0:
            if parentLinkage['currentIndex'] > 0:
                parentLinkage['currentIndex'] = parentLinkage['currentIndex'] - 1
                rotamerCounter.rootHits = rotamerCounter.rootHits + 1
                rotamerCounter.activeLevel = len(rotamerCounter.linkages) - 1
                resetCount = 1
                while resetCount < len(rotamerCounter.linkages):
                    rotamerCounter.linkages[resetCount]['currentIndex'] = rotamerCounter.linkages[resetCount]['count'] - 1
                    resetCount = resetCount + 1
            else:
                log.debug("I think we are done with updating parent linkages?")

        updateCount = updateCount + 1
    else:
        leafNode['currentIndex'] = leafNode['currentIndex'] - 1


##  @brief  Updates the sequence with the next config object for a linkage based on the counterObj
#   @detail Within a sequence, a conformer represents the state (rotamer) of a single label-dihedral pair.
#           Just gets whatever rotamer is indicated in counterObj['currentIndex'], which puts all
#           selection responsibility in the counter and decrementCounters(). Does not increment indices.
#   @param  rotamerData
#   @param  counterObj
#   @param  sequence  Not the string, but a list of conformers currently being built.
#   @TODO: Move this to a better file for this stuff.
def addNextConformer(rotamerData, counterObj, sequence):
    log.debug("addNextConformer() was called.")
    myLabel = counterObj['label']
    myDihedral = counterObj['dihedral']
    myCount = counterObj['count']
    myCurrentIndex = counterObj['currentIndex']

    for linkageData in rotamerData:
        linkageLabel = linkageData['linkageLabel'].strip()
        log.debug("Looking for linkageLabel: " + linkageLabel)
        if linkageLabel == myLabel:
            log.debug("Found the linkage. Looking for the dihedral.")

            for dihedral in linkageData['dihedrals']:
                dihedralName = dihedral['dihedralName']
                log.debug("Looking for dihedralName: " + dihedralName)  
                if dihedralName == myDihedral:
                    log.debug("Found the dihedral for this linkage.")
                    log.debug("myCurrentIndex: " + str(myCurrentIndex))
                    rotamer = dihedral['selectedRotamers'][myCurrentIndex]
                    log.debug("rotamer: " + rotamer)
                
                    conformer = {
                        'linkageLabel' : linkageLabel,
                        'dihedralName' : dihedralName,
                        'rotamer' : rotamer
                    }
                    sequence.append(conformer)


##  @brief Grab the next sequence indicated by the rotamerCounter object. 
#   @detail Handles things at the sequence level, grabbing conformer config dicts 
#       and updating the rotamerCounter object so the next one will be the correct one.
#   @TODO: Move this to a better file for this stuff.
def getNextSequence(rotamerData, rotamerCounter, sequences):
    log.debug("getNextSequence() was called.")
    sequence = []

    log.debug("\n\nrotamerCounter before building a sequence: \n" + str(rotamerCounter) + "\n")

    ##Iterate through the rotamerCounter grabbing the keys for
    #   grabbing the right rotamers from rotamer date
    for i in range(len(rotamerCounter.linkages)) :
        counterObj = rotamerCounter.linkages[i]
        log.debug("Looking up this linkage at i: " + str(i) + ": " +  str(counterObj))

        if len(sequences) == 0: 
            log.debug("first sequence. Getting the first thing found for each label-dihedral pair.")
            ##First sequence. Grab the first element found in each element.
            addNextConformer(rotamerData, counterObj, sequence)
            if i == len(rotamerCounter.linkages) - 1:
                log.debug("decrementing counters for the first time.")
                log.debug("\n\nrotamerCounter before: \n" + str(rotamerCounter))
                decrementCounters(rotamerCounter)
                log.debug("\n\nrotamerCounter after: \n" + str(rotamerCounter))
        else:
            log.debug("Sequences exist, need to check against those.")
            ## The lastLeafConformer  is the conformer of the leaf of the previous sequence.
            addNextConformer(rotamerData, counterObj, sequence)
            if i == len(rotamerCounter.linkages) - 1:
                log.debug("\n\nrotamerCounter before: \n" + str(rotamerCounter))
                decrementCounters(rotamerCounter)
                log.debug("\n\nrotamerCounter after: \n" + str(rotamerCounter))
        
    log.debug("\n\nreturning this sequence: \n " + str(sequence) + "\n")
    return sequence


##  @brief Uses the rotamerCounter to multiply the number of rotamer selections for each
#       linkage-dihedral pair
#   @param rotamerCounter
#   @TODO: Move this to a better file for this stuff.
def getRequestedStructureCount(rotamerCounter):
    log.info("getRequestedStructureCount() was called.")
    requestedStructureCount = 1
    for linkage in rotamerCounter.linkages:
        x = int(linkage['count'])
        requestedStructureCount = requestedStructureCount * x

    return requestedStructureCount

##  @brief  Finds rotamerData in the transaction
#   @param  Transaction
#   @return rotamerData
#   @TODO: Move this to a better file for this stuff.
def getRotamerDataFromTransaction(thisTransaction: Transaction):
    log.info("getRotamerDataFromTransaction() was called.")
    request = thisTransaction.request_dict
    if "options" in request.keys():
        if "geometryOptions" in request['options'].keys():
            if 'rotamerData' in request['options']['geometryOptions'].keys():
                rotamerData = request['options']['geometryOptions']['rotamerData']
                
                return rotamerData
            else:
                raise AttributeError("rotamerData")
        else:
            raise AttributeError("geometryOptions")

##  @brief Pass in a sequence (list of rotamerConformations), get a terse label.
#   @detail Translate the more verbose sequenceConf object into a terse string that is useful
#           for naming directories and describing interesting geometry in a build.
#   @param sequenceConf List[rotamerConformation]
#   @return string structureLabel
def buildStructureLabel(sequenceConf):
    log.info("buildStructureLabel() was called.\n\n")
    structureLabel = ""
    log.debug("this sequenceConf: \n" + str(sequenceConf))

    #Assess each rotamer conf obj
    for rotamerConf in sequenceConf:
        log.debug("this rotamerConf: \n" + str(rotamerConf))

        ##Decide whether or not to add the label.
        if structureLabel == "":
            structureLabel = rotamerConf['linkageLabel']
        elif rotamerConf['linkageLabel'] not in structureLabel:
            structureLabel = structureLabel + "_"+ rotamerConf['linkageLabel']
        else:
            log.debug("adding to the same linkage.")
            structureLabel = structureLabel + "_"

        ##Decide which abbreviated dihedral is needed
        dihedralAbbreviation = ""
        if rotamerConf['dihedralName'] == "phi":
            dihedralAbbreviation = "h"
        elif rotamerConf['dihedralName'] == "psi":
            dihedralAbbreviation = "s"
        elif rotamerConf['dihedralName'] == "omega":
            dihedralAbbreviation = "o"
        elif rotamerConf['dihedralName'] == "chi":
            dihedralAbbreviation = "c"
        else:
            log.debug("Unrecognized dihedralName: " + str(rotamerConf['dihedralName'])) 

        structureLabel = structureLabel + dihedralAbbreviation

        ##Add the rotamer value
        structureLabel = structureLabel + rotamerConf['rotamer']


    return structureLabel


##  @brief Parses user's selected rotamers (rotamerData) into a list of 
#           structures to request.
#   @detail With a limit of 64 structures to request at a time, users select
#           each rotamer they want for each linkage. This code creates the 
#           list of unique permutations possible for those selections.
#   @param Transaction 
#   @TODO: Move this to a better file for this stuff.
def buildStructureInfo(thisTransaction : Transaction):
    log.info("buildStructureInfo() was called.")

    structureInfo = StructureInfo()
    structureInfo.buildStates = []
    try:
        sequence = getSequenceFromTransaction(thisTransaction)
        log.debug("sequence: " + str(sequence))
        structureInfo.sequence = sequence
        ##TODO: Also grab the following from the request, or set defaults:
        ##    buildType, ions, forceField, date.
    except Exception as error:
        log.error("There was a problem getting the sequence from the transaction: " + str(error))
        raise error
    else:
        try:
            #RotamerData is the list of dict objects describing each linkage
            rotamerData = getRotamerDataFromTransaction(thisTransaction)
        except Exception as error:
            log.error("There was a problem getting rotamerData from the transaction: " + str(error))
            raise error
        else:
            sequences = []
            linkageCount = len(rotamerData)
            log.debug("linkageCount: " + str(linkageCount))
            log.debug("\nrotamerData:\n" + str(rotamerData))

            ##Rotamer counter objects allow the logic to track the rotamer selection.
            rotamerCounter = RotamerCounter(rotamerData)
            log.debug("rotamerCounter: " + str(rotamerCounter.__dict__))

            ##How many structures have been requested?
            requestedStructureCount = getRequestedStructureCount(rotamerCounter)
            log.debug("requestedStructureCount: " + str(requestedStructureCount))
            
            ##Define when to stop.
            while len(sequences) < requestedStructureCount and len(sequences) <= 64:
                buildState = BuildState()
                ##Build the sequenceConformation
                sequenceConf = getNextSequence(rotamerData, rotamerCounter, sequences)
                buildState.sequenceConformation = sequenceConf
                
                ##Build the structureLabel
                buildState.structureLabel = buildStructureLabel(sequenceConf)
                log.debug("structureLabel: \n" + buildState.structureLabel)

                ##Check if the user requested a specific simulationPhase
                buildState.simulationPhase = checkForSimulationPhase(thisTransaction)
                log.debug("simulationPhase: " + buildState.simulationPhase)

                ##Set the initial status
                buildState.status = JobStatusEnum.new
                log.debug("status: " + buildState.status)

                ##Set the date
                buildState.date = datetime.now()
                log.debug("date: " + str(buildState.date))

                ## Check if the user requested to add ions
                buildState.addIons = checkForAddIons(thisTransaction)

                ##sequences is needed for progress tracking.
                sequences.append(sequenceConf)     
                log.debug("sequence list length: " + str(len(sequences)))
                structureInfo.buildStates.append(buildState)
                
            ##Useful logging for maintenance
            log.debug("sequences: ")
            for element in sequences:
                log.debug("~")
                for item in element:
                    log.debug( str(item) )

            log.debug("sequenceCount: " + str(len(sequences)))

##  @brief Checks a transaction for user requests that specify adding ions.
#   @detail Default value is "default" - which depends on other software's defauts.
#   @param Transaction
def checkForAddIons(thisTransaction: Transaction):
    log.info("checkForAddIons() was called.")

    result = "default"
    request = thisTransaction.request_dict
    if "project" in request.keys():
        if "ion" in request['project'].keys():
            result = request['project']['ion']
    
    ##If both a project and options exist, let the options override the
    #   project.
    if "options" in request.keys():
        if "add_ions" in request['options'].keys():
            result = request['options']['add_ions']

    return result


##  @brief Checks a transaction for user requests that specify simulation phase
#   @detail Default value is gas_phase
#   @param Transaction
def checkForSimulationPhase(thisTransaction: Transaction):
    log.info("checkForSimulationPhase() was called.")

    simulationPhase = "gas_phase"
    request = thisTransaction.request_dict
    if "project" in request.keys():
        if "solvation" in request['project'].keys():
            if request['project']['solvation'] == "yes":
                simulationPhase = "solvent"

    ##If both a project and options exist, let the options override the
    #   project.
    if "options" in request.keys():
        if "solvation" in request['options'].keys():
            if request['options']['solvation'] == "yes":
                simulationPhase = "solvent"

    return "gas_phase"


def main():
    log.info("main() was called.")

if __name__ == "__main__":
    main()