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


def print_progress():
    sys.stdout.write(bcolors.OKBLUE + '.' + bcolors.ENDC)
    sys.stdout.flush()


def print_error(msg):
    print(bcolors.FAIL + msg + bcolors.ENDC)


def print_success(msg):
    print(bcolors.OKGREEN + msg + bcolors.ENDC)


def print_info(msg):
    print(bcolors.OKBLUE + msg + bcolors.ENDC)


def print_warning(msg):
    print(bcolors.WARNING + msg + bcolors.ENDC)
