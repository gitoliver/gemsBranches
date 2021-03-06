#!/bash/bin

usage() {
	cat << USAGE >&2


Usage: bash logs/clearLogs.sh LOGNAME

	LOGNAME: Target logfile or ALL. Default to ALL
		error
		info
		debug

Example: 

	bash clearLogs.sh error

Clears the error log file.


USAGE
	exit 1
}

if [ "$1" == "help" ]; then
	usage
fi

if [ "$1" == "" ]; then
	if [ -f "./logs/git-ignore-me_gemsDebug.log" ]; then
		echo "" > ./logs/git-ignore-me_gemsDebug.log
		echo "" > ./logs/git-ignore-me_gemsInfo.log
		echo "" > ./logs/git-ignore-me_gemsError.log
	else
		echo Log files not found. Please run this script from programs/gems
		
	fi
fi

if [ "$1" == "debug" ]; then
	echo "" > ./logs/git-ignore-me_gemsDebug.log
fi

if [ "$1" == "info" ]; then
	echo "" > ./lologsgs/git-ignore-me_gemsInfo.log
fi

if [ "$1" == "error" ]; then
	echo "" > ./logs/git-ignore-gemsError.log
fi

exit 0