#!/bin/bash
#
# Purpose: This script is used to restore the mongo database that powers
#          sealog from a backup.
#
#   Usage: sealog_restoreSealogDB.sh
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-11

# Parent Directory of sealog database backups
BACKUP_DIR="/home/sealog/sealog-backups"

# Directory where the script is being run from
PWD=pwd

# Goto the backup directory, get the list of database backups and return to
# where we started
cd $BACKUP_DIR
dirs=(*)
cd $PWD

# Prompt the user to select a backup to use for the restore
echo "Restore from which backup (pick a number):"
PS3="> "
select opt in ${dirs} "Quit"; do
    [[ -n $opt ]] && break || {
        echo "Please pick a valid option"
    }
done

if [ $opt == "Quit" ];then
  exit 0
fi

# Stress the potential dangers of continues and confirm the selection
echo "You chose to restore from: '$opt'"
echo "Proceeding with this restore will replace any/all data currently in"
echo "the database with the data contained within the selected backup."
echo "THIS CANNOT BE UNDONE!!"
read -p "Please confirm this selection (y/n)?" -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "it's on now!"
    exec mongorestore --drop ${BACKUP_DIR}/$opt
    echo "Database restore process is complete."
    echo "Please review the text above to determine if any errors were encountered."
fi


