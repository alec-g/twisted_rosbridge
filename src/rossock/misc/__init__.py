
import os
import sys
import time
import numpy
import cPickle
import traceback

if os.name == "posix":
	colors = {
		"RED": '\033[91m',
		"BLUE": '\033[94m',
		"GREEN": '\033[92m',
		"ORANGE": '\033[93m',
		"CYAN": '\033[97m',
		"DARKCYAN": '\033[36m',
		"MAGENTA": '\033[95m',
		"BOLD": '\033[1m',
		"UNDERLINE": '\033[4m',
		"ENDC": '\033[0m'
	}

else:
	colors = {
		"RED": '',
		"BLUE": '',
		"GREEN": '',
		"ORANGE": '',
		"CYAN": '',
		"DARKCYAN": '',
		"MAGENTA": '',
		"BOLD": '',
		"UNDERLINE": '',
		"ENDC": ''
	}

def formatted_print(msg, color=None, status=None):
	final_str = msg

	if color is None and status is not None:
		if status.lower() == "success":
			color = "GREEN"
		elif status.lower() == "error":
			color = "RED"
		elif status.lower() == "warning":
			color = "ORANGE"
		elif status.lower() == "connecting":
			color = "MAGENTA"

	if color is not None:
		final_str = colors[color.upper()] + msg + colors["ENDC"]

	print final_str

def print_safe_except_report(msg="", *args):
	print RED + msg + ENDC
	print "--------------------- Safe Error Report ----------------------"
	exc_type, exc_value, exc_traceback = sys.exc_info()
	traceback.print_exception(exc_type, exc_value, exc_traceback)
	print "---------------------------- End -----------------------------"
