#!/bin/bash
#
# Purpose: This script is modifies the cruise records exported by the at-sea
#          instance of Sealog so that the cruise can be directly ingested
#          by the Shoreside instance of Sealog.
#
#   Usage: modify_cruise_for_import.sh
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-11
#Modified: 2019-09-10


# Directory containing the sealog data to be modified.
NEW_CRUISE_DIR="/home/sealog/Cruises"

# Directory where the script is being run from
_D="$(pwd)"

# Parent directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

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

# Stress the potential dangers of continues and confirm the selection
echo "You chose to modify the cruise record for cruise: ${CRUISE}"
read -p "Please confirm this selection (y/n)?" -n 1 -r
if ! [[ $REPLY =~ ^[Yy]$ ]]; then
  echo ""
  exit 0
fi

echo ""
echo "Processing Lowering Record..."
FILENAME=${CRUISE}_cruiseRecord.json

if [ ! -f ${NEW_CRUISE_DIR}/${CRUISE}/${FILENAME} ]; then
  echo "ERROR: The cruise record: ${NEW_CRUISE_DIR}/${CRUISE}/${FILENAME} does not exist."
  exit 1
fi

mkdir -p ${NEW_CRUISE_DIR}/${CRUISE}/modifiedForImport
python3 ${SCRIPT_DIR}/convert_cruise_records.py ${NEW_CRUISE_DIR}/${CRUISE}/${FILENAME} > ${NEW_CRUISE_DIR}/${CRUISE}/modifiedForImport/${CRUISE}_cruiseRecord_mod.json
if [ $? -ne 0 ]; then
  exit 1
fi
