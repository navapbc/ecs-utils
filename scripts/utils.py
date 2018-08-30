"""
Utility functions.
"""
import sys


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def printProgress():
    sys.stdout.write(bcolors.OKBLUE + '.' + bcolors.ENDC)
    sys.stdout.flush()

def printError(msg):
    print(bcolors.FAIL + "ERROR: " + msg + bcolors.ENDC)

def printSuccess(msg):
    print(bcolors.OKGREEN + "SUCCESS: " + msg + bcolors.ENDC)

def printInfo(msg):
    print(bcolors.OKBLUE + "INFO: " + msg + bcolors.ENDC)

def printWarning(msg):
    print(bcolors.WARNING + "WARN: " + msg + bcolors.ENDC)


