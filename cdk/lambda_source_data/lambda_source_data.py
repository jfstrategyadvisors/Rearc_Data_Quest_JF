from utils.bls_sync import sync_files_to_s3, BLS_URL, S3_BUCKET, S3_PREFIX
from utils.api_pull import fetch_and_store_api_data

def handler(event, context):
    # Part 1: Sync BLS files to S3
    sync_files_to_s3(BLS_URL, S3_BUCKET, S3_PREFIX)

    # Part 2: Fetch API data and store in S3
    fetch_and_store_api_data()

    return {"statusCode": 200, "body": "Data ingestion complete"}