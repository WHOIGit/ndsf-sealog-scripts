#!/bin/bash -eu
#
# Purpose: This script is used to import the modded lowering into Sealog
#
#   Usage: import_lowering_into_sealog.sh
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-22
#Modified: 2019-05-22

# Parent Directory of sealog database backups
NEW_CRUISE_DIR="/home/sealog/Cruises"

vehicles="Alvin Jason"

# Directory where the script is being run from
_D="$(pwd)"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Prompt the user to select a backup to use for the restore
echo "Which vehicle (pick a number):"
PS3="> "
select opt in ${vehicles} "Cancel"; do
    [[ -n $opt ]] && break || {
        echo "Please pick a valid option"
    }
done

if [ $opt == "Cancel" ];then
  exit 0
fi

VEHICLE=$opt
echo ""

cd ${NEW_CRUISE_DIR}
cruise_dirs=`ls ${NEW_CRUISE_DIR}`
cd "${_D}"

echo "Which cruise (pick a number):"
select opt in ${cruise_dirs} "Cancel"; do
    [[ -n $opt ]] && break || {
        echo "Which cruise?"
    }
done

if [ $opt == "Cancel" ];then
  exit 0
fi

CRUISE=$opt
echo ""

cruise_filename="${CRUISE}/modifiedForImport/${CRUISE}_cruiseRecord_mod.json"

if [ ! -f "${NEW_CRUISE_DIR}/${cruise_filename}" ]; then
  echo "ERROR: The modified cruise record $cruise_filename does not exist."
  exit 1
fi

# Stress the potential dangers of continues and confirm the selection
echo "You chose to import ${VEHICLE} cruise: ${CRUISE}."
read -p "Do you want to proceed with the import (y/n)? " -n 1 -r
if ! [[ $REPLY =~ ^[Yy]$ ]]; then
  echo ""
  exit 0
fi

echo ""

echo "Importing cruise record..."

# Change in Docker: We use the `dc` helper tool to run the mongoimport command
# inside the MongoDB container
sudo /opt/sealog/dc "$VEHICLE" exec mongo \
  mongoimport \
    --db sealogDB \
    --collection cruises \
    --file "/sealog-import/${cruise_filename}" \
    --jsonArray \
    --mode upsert

echo ""
