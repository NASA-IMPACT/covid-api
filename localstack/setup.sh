
if awslocal s3 ls s3://"${DATA_BUCKET_NAME}"/"${DATASET_METADATA_FILENAME}"
then
    echo "Dataset metadata file found in local S3 bucket. To force re-generation: 
        run `docker-compose down --volumes` to clear the S3 bucket, and start 
        the api again"
else
    awslocal s3 mb s3://"${DATA_BUCKET_NAME}" 
    echo "Dataset metadata file not found in local S3 bucket. Generating..."
    python3 /docker-entrypoint-initaws.d/main.py
    echo "Done!"
fi