#!/bin/bash -eu
#
# Purpose: This script backs up sealog data to file including the cruise 
#          record, lowering record and event_templates.
#
#   Usage: Type sealog_postdive.sh [-d dest_dir] [-c cruise_id] <lowering_id> to run the script.
#          - [-d dest_dir] --> where to save the data, the default location
#                              is defined in the BACKUP_DIR_ROOT variable
#          - [-c dest_dir] --> the cruise ID (RR1802).  If this is defined 
#                              the script will first create a folder with 
#                              the cruiseID and then save the lowering data 
#                              within that directory 
#          - <lowering_id> --> the lowering ID (J2-1042)
#
#  Author: Webb Pinner webbpinner@gmail.com
# Created: 2018-09-26

# Note: This should be the URL to the API endpoint from *outside* of Docker,
# since you are running this script on the host.
API_SERVER_URL="https://localhost/sealog/server"

# JWT authentication token
TOKEN=$(cd .. && python3 -c 'from python_sealog.settings import token; print(token)')

GET_LOWERING_OID_SCRIPT='python3 /home/jason/sealog-server/misc/getLoweringId.py'
GET_CRUISE_OID_SCRIPT='python3 /home/jason/sealog-server/misc/getCruiseId.py'
GET_FRAMEGRAB_SCRIPT='python3 /home/jason/sealog-server/misc/getFramegrabList.py'
GET_SULISCAM_SCRIPT='python3 /home/jason/sealog-server/misc/getSulisCamList.py'

# Root data folder for Sealog
BACKUP_DIR_ROOT="/home/jason/sealog-backup"
FRAMEGRAB_DIR="images"
SULISCAM_DIR="images/SulisCam"
CRUISE_ID=""
CRUISE_OID=""
LOWERING_ID=""
LOWERING_OID=""

getLoweringData(){
	echo "LOWERING_OID = ${LOWERING_OID}"

	echo "Export lowering record"
	curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${LOWERING_DIR}'/'${LOWERING_ID}'_loweringRecord.json' ${API_SERVER_URL}'/api/v1/lowerings/'${LOWERING_OID}

	echo "Exporting event data"
	curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${LOWERING_DIR}'/'${LOWERING_ID}'_eventOnlyExport.json' ${API_SERVER_URL}'/api/v1/events/bylowering/'${LOWERING_OID}

	echo "Exporting aux data"
	curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${LOWERING_DIR}'/'${LOWERING_ID}'_auxDataExport.json' ${API_SERVER_URL}'/api/v1/event_aux_data/bylowering/'${LOWERING_OID}

	echo "Exporting events with aux data as json"
	curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${LOWERING_DIR}'/'${LOWERING_ID}'_sealogExport.json' ${API_SERVER_URL}'/api/v1/event_exports/bylowering/'${LOWERING_OID}

	echo "Exporting event with aux data as csv"
	curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${LOWERING_DIR}'/'${LOWERING_ID}'_sealogExport.csv' ${API_SERVER_URL}'/api/v1/event_exports/bylowering/'${LOWERING_OID}'?format=csv'
}

getFramegrabs(){
	${GET_FRAMEGRAB_SCRIPT} ${LOWERING_DIR}'/'${LOWERING_ID}'_auxDataExport.json'
}

getSulisCam(){
	${GET_SULISCAM_SCRIPT} ${LOWERING_DIR}'/'${LOWERING_ID}'_eventOnlyExport.json'
}

usage(){
cat <<EOF
Usage: $0 [-?] [-d dest_dir] [-c cruise_id] <lowering_id>
	-d <dest_dir>   Where to store the backup, the default is:
	                ${BACKUP_DIR_ROOT}
	-c <cruise_id>  The cruise id for the lowering, if specified
	                the lowering backup will be stored within a 
	                <cruise_id> directory. 
	-?              Print this statement.
	<lowering_id>   The dive ID i.e. 'J2-1107'
EOF
}

while getopts ":d:c:" opt; do
  case $opt in
   d)
      # echo ${OPTARG}
      BACKUP_DIR_ROOT=${OPTARG}
      ;;
   c)
      CRUISE_ID="${OPTARG}"
      ;;

   \?)
      usage
      exit 0
      ;;
  esac
done

shift $((OPTIND-1))

if [ $# -ne 1 ]; then
        echo ""
        echo "Missing dive number"
        echo ""
        usage
        exit 1
fi

LOWERING_ID="${1}"

# echo "LOWERING ID SCRIPT:" ${GET_LOWERING_OID_SCRIPT} ${1}
if [ ${CRUISE_ID} != "" ]; then
	CRUISE_OID=`${GET_CRUISE_OID_SCRIPT} ${CRUISE_ID}`

	if [ -z ${CRUISE_OID} ]; then
		echo ""
		echo "Unable to find cruise data for cruise id: ${CRUISE_ID}"
		echo ""
		exit 1
	fi

	echo "CRUISE_OID:" ${CRUISE_OID}

fi

LOWERING_OID=`${GET_LOWERING_OID_SCRIPT} ${1}`
if [ -z ${LOWERING_OID} ]; then
	echo ""
	echo "Unable to find lowering data for dive id: ${1}"
	echo ""
	exit 1
fi
echo "LOWERING_OID:" ${LOWERING_OID}

echo ""
echo "-----------------------------------------------------"
echo "Backup Directory:" ${BACKUP_DIR_ROOT}/${CRUISE_ID}/${LOWERING_ID}
echo "-----------------------------------------------------"
read -p "Continue? (Y/N): " confirm && [[ $confirm == [Yy] || $confirm == [Yy][Ee][Ss] ]] || exit 1

if [ ! -z ${CRUISE_ID} ]; then
	BACKUP_DIR=${BACKUP_DIR_ROOT}/${CRUISE_ID}
else
	BACKUP_DIR=${BACKUP_DIR_ROOT}
fi

LOWERING_DIR=${BACKUP_DIR}/${LOWERING_ID}

if [ ! -d ${LOWERING_DIR} ]; then
    read -p "Create backup directory? (Y/N): " confirm && [[ $confirm == [Yy] || $confirm == [Yy][Ee][Ss] ]] || exit 1
    mkdir -p ${LOWERING_DIR}
    if [ ! -d ${LOWERING_DIR} ]; then
            echo "Unable to create backup directory... quitting"
            exit 1
    fi
    mkdir ${LOWERING_DIR}/${FRAMEGRAB_DIR}
    if [ ! -d ${LOWERING_DIR}/${FRAMEGRAB_DIR} ]; then
            echo "Unable to create framegrab directory... quitting"
            exit 1
    fi
    mkdir ${LOWERING_DIR}/${SULISCAM_DIR}
    if [ ! -d ${LOWERING_DIR}/${SULISCAM_DIR} ]; then
            echo "Unable to create SulisCam directory... quitting"
            exit 1
    fi
fi

if [ ${CRUISE_OID} != '' ]; then
	echo "Export cruise record"
	curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${BACKUP_DIR}'/'${CRUISE_ID}'_cruiseRecord.json' ${API_SERVER_URL}'/api/v1/cruises/'${CRUISE_OID}

	echo "Export event templates"
	curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${BACKUP_DIR}'/'${CRUISE_ID}'_eventTemplates.json' ${API_SERVER_URL}'/api/v1/event_templates'
fi

echo "Export event templates"
curl -X GET --header 'Accept: application/json' --header 'authorization: '${TOKEN} --output ${LOWERING_DIR}'/'${LOWERING_ID}'_eventTemplates.json' ${API_SERVER_URL}'/api/v1/event_templates'

getLoweringData

getFramegrabs | awk -v dest=${LOWERING_DIR}/${FRAMEGRAB_DIR} 'BEGIN{print "#!/bin/bash"} {printf "cp -v %s %s/\n", $0, dest}' > ${LOWERING_DIR}/${LOWERING_ID}_framegrabCopyScript.sh
pico ${LOWERING_DIR}/${LOWERING_ID}_framegrabCopyScript.sh
read -p "Proceed with copying framegrabs? (Y/N): " confirm && [[ $confirm == [Yy] || $confirm == [Yy][Ee][Ss] ]] || exit 1
echo "Copying framegrabs"
chmod +x ${LOWERING_DIR}/${LOWERING_ID}_framegrabCopyScript.sh
${LOWERING_DIR}/${LOWERING_ID}_framegrabCopyScript.sh

# This should be harmless if there are no Sulis images
getSulisCam | awk -v dest=${LOWERING_DIR}/${SULISCAM_DIR} 'BEGIN{print "#!/bin/bash"} {printf "cp -v %s %s/\n", $0, dest}' > ${LOWERING_DIR}/${LOWERING_ID}_sulisCamCopyScript.sh
pico ${LOWERING_DIR}/${LOWERING_ID}_sulisCamCopyScript.sh
read -p "Proceed with copying SulisCam images? (Y/N): " confirm && [[ $confirm == [Yy] || $confirm == [Yy][Ee][Ss] ]] || exit 1
echo "Copying SulisCam images"
chmod +x ${LOWERING_DIR}/${LOWERING_ID}_sulisCamCopyScript.sh
${LOWERING_DIR}/${LOWERING_ID}_sulisCamCopyScript.sh

echo "Done!"
