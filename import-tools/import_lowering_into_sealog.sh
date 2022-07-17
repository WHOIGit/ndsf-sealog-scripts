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

# Directory where the script is being run from
_D="$(pwd)"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Prompt the user to select a backup to use for the restore
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
You chose to import all lowerings within cruise: ${CRUISE}.
EOF
)

else
  LOWERINGS=$opt
  WARNING_MSG=$(cat <<- EOF
You chose to import lowering ${LOWERINGS} within cruise: ${CRUISE}.
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

  if [ ! -d ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING} ]; then
    echo "ERROR: The lowering directory: ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING} does not exist."
    exit 1
  fi

  if [ ! -d ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport ]; then
    echo "ERROR: The directory containing the modified files needed to import the lowering: ${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING} does not exist."
    echo "You need to run the modify_lowering_for_import.sh script to create this directory and the required import files."
    exit 1
  fi


  echo ""


  # Change in Docker: We run the mongoimport command inside the MongoDB container.
  # On harmonyhill, use the `dc` helper tool.
  DC_COMMAND="docker-compose -f /opt/sealog/docker-compose.yml"
  if [ -f /opt/sealog/dc ]; then
    vehicles="Alvin Jason Sandbox"

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

    DC_COMMAND="/opt/sealog/dc $VEHICLE"
  fi

  echo "Importing lowering record..."
  lowering_filename="${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_loweringRecord_mod.json"
  sudo ${DC_COMMAND} exec mongo \
    mongoimport \
      --db sealogDB \
      --collection lowerings \
      --file "/sealog-import/${lowering_filename}" \
      --mode upsert
  echo ""

  echo "Importing lowering events"
  event_filename="${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_eventOnlyExport_mod.json"
  sudo ${DC_COMMAND} exec mongo \
    mongoimport \
      --db sealogDB \
      --collection events \
      --file "/sealog-import/${event_filename}" \
      --jsonArray \
      --mode upsert
  echo ""

  echo "Importing lowering aux data"
  auxdata_filename="${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_auxDataExport_mod.json"
  sudo ${DC_COMMAND} exec mongo \
    mongoimport \
      --db sealogDB \
      --collection event_aux_data \
      --file "/sealog-import/${auxdata_filename}" \
      --jsonArray \
      --mode upsert
  echo ""

  cd "${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport"

  chmod +x "${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_framegrabCopyScript_mod.sh"
  echo "Copying framegrabs"
  pv -p -w 80 "${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_framegrabCopyScript_mod.sh" | bash > /dev/null
  echo ""

  if [ -f "${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_sulisCamCopyScript_mod.sh" ]; then
    echo "Copying SulisCam Stills"
    chmod +x "${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_sulisCamCopyScript_mod.sh"
    pv -p -w 80 "${NEW_CRUISE_DIR}/${CRUISE}/${LOWERING}/modifiedForImport/${LOWERING}_sulisCamCopyScript_mod.sh" | bash > /dev/null
    echo ""
  fi

done
