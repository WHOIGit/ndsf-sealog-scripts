#!/bin/bash
#
# Purpose: This script is modifies the lowering files exported by the at-sea
#          instance of Sealog so that the lowering can be directly ingested
#          by the Shoreside instance of Sealog.
#
#   Usage: modify_lowering_for_import.sh
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2019-05-11
#Modified: 2019-05-22


# Directory containing the sealog data to be modified.
NEW_CRUISE_DIR="/home/sealog/Cruises"

# Possible vehicle choices
vehicles="Alvin Jason"

# Directory where the script is being run from
_D="$(pwd)"

# Parent directory of this script
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

cd ${NEW_CRUISE_DIR}/${CRUISE}
lowering_dirs=`find . -maxdepth 1 -type d -exec basename {} \; | egrep -v '\.|modified'`

cd "${_D}"

echo "Which lowering (pick a number):"
select opt in "All" ${lowering_dirs} "Cancel"; do
    [[ -n $opt ]] && break || {
        echo "Which lowering?"
    }
done

if [ $opt == "Cancel" ];then
  exit 0
fi

if [ $opt == "All" ]; then
  LOWERINGS=${lowering_dirs}
  WARNING_MSG=$(cat <<- EOF
You chose to modify all lowerings within cruise: ${CRUISE}.
Proceeding with this will create the following subdirectory in each lowering directory:
 - <lowering_dir>/modifiedForImport
This subdirectory will contain the modified files for that lowering.
EOF
)

else
  LOWERINGS=$opt
  WARNING_MSG=$(cat <<- EOF
You chose to modify lowering ${LOWERINGS} within cruise: ${CRUISE}.
Proceeding with this will create the following subdirectory:
 - ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERINGS}/modifiedForImport
This subdirectory will contain the modified files for that lowering.
EOF
)

fi

# Stress the potential dangers of continues and confirm the selection
echo ""
echo "$WARNING_MSG"
read -p "Please confirm this selection (y/n)?" -n 1 -r
if ! [[ $REPLY =~ ^[Yy]$ ]]; then
  echo ""
  exit 0
fi

for LOWERING in $LOWERINGS; do
  echo ""
  echo "Processing Lowering ${LOWERING}"
  if [ ! -d ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING} ]; then
    echo "ERROR: The lowering directory: ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING} does not exist."
    exit 1
  fi

  mkdir -p ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport

  echo "Processing Lowering Record..."
  FILENAME=${LOWERING}_loweringRecord.json
  python3 ${SCRIPT_DIR}/convert_lowering_records.py --vehicle ${VEHICLE} ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/${FILENAME} > ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_loweringRecord_mod.json
  if [ $? -ne 0 ]; then
    exit 1
  fi

  echo "Processing Event Records..."
  FILENAME=${LOWERING}_eventOnlyExport.json
  python3 ${SCRIPT_DIR}/convert_event_records.py --vehicle ${VEHICLE} ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/${FILENAME} > ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_eventOnlyExport_mod.json
  if [ $? -ne 0 ]; then
    exit 1
  fi

  echo "Processing Aux Data Records..."
  FILENAME=${LOWERING}_auxDataExport.json
  python3 ${SCRIPT_DIR}/convert_aux_data_records.py --vehicle ${VEHICLE} ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/${FILENAME} > ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_auxDataExport_mod.json
  if [ $? -ne 0 ]; then
    exit 1
  fi

  echo "Processing Framegrab copy script..."
  FILENAME=${LOWERING}_framegrabCopyScript.sh
  python3 ${SCRIPT_DIR}/convert_framegrab_copy_script.py --vehicle ${VEHICLE} ${LOWERING} ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/${FILENAME} > ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_framegrabCopyScript_mod.sh
  if [ $? -ne 0 ]; then
      exit 1
  fi

  if [ -f ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/${LOWERING}_sulisCamCopyScript.sh ]; then
      echo "Processing SulisCam copy script..."
      python3 ${SCRIPT_DIR}/convert_sulisCam_copy_script.py ${LOWERING} ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/${LOWERING}_sulisCamCopyScript.sh > ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_sulisCamCopyScript_mod.sh
  else
      echo "WARNING: No SulisCam copy script detected"
  fi
done
