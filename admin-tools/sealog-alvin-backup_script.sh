#!/bin/bash
TIMESTAMP=`date +%F-%H%M`
APP_NAME="sealog-alvin"
DATABASE_NAME="sealogDB_alvin"
BACKUP_DIR="/home/sealog/sealog-backups"
BACKUP_NAME="${APP_NAME}-${TIMESTAMP}.bkp"
BACKUP_LOG="${BACKUP_DIR}/${APP_NAME}-backup.log"

MONGOBIN_PATH="/usr/bin"
MONGO_HOST="localhost"
MONGO_PORT="27017"

mkdir -p ${BACKUP_DIR}
cd ${BACKUP_DIR}

echo "Deleting following backup files older than 30 days:" >> ${BACKUP_LOG}
find ${BACKUP_DIR} -type d -name '${APP_NAME}-*' -mtime +30 >> ${BACKUP_LOG}
find ${BACKUP_DIR} -type d -name '${APP_NAME}-*' -mtime +30 -exec rm -rf {} +

#Run the daily backup of remaining databases.
echo "Starting daily backup of ${DATABASE_NAME}...." >> ${BACKUP_LOG}
${MONGOBIN_PATH}/mongodump --host ${MONGO_HOST}:${MONGO_PORT} --db ${DATABASE_NAME} >> ${BACKUP_LOG} 2>&1

if [ $? != 0 ]; then
echo "Failed to make backup of database on `date +%F_%T`"
#| mailx -s "MongoDB backup failed" amolbarsagade@in.ibm.com
fi


echo "Renaming backup directory to ${BACKUP_NAME}" >> ${BACKUP_LOG}
mv dump ${BACKUP_NAME}

echo "End of backup run `date`" >> ${BACKUP_LOG}
echo "----------------------------------" >> ${BACKUP_LOG}

