import requests
import boto3
import json
from datetime import datetime

# DataUSA API endpoint for population data
API_URL = "https://honolulu-api.datausa.io/tesseract/data.jsonrecords?cube=acs_yg_total_population_1&drilldowns=Year%2CNation&locale=en&measures=Population"

# S3 bucket name
S3_BUCKET = "rearc-data-quest-jf"

# S3 prefix (folder path for API data)
S3_API_PREFIX = "api-data/"

"""
Fetch population data from the DataUSA API.
Returns the JSON response as a Python dictionary.
"""

def fetch_api_data(api_url):
    print(f"Fetching data from API...")
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

"""
Upload JSON data to S3 with date-based folder structure (YYYY-MM-DD).
Returns the S3 key where the file was stored.
"""
def upload_json_to_s3(data, bucket_name, prefix, filename="population_data.json"):
    s3 = boto3.client("s3")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    s3_key = f"{prefix}{date_folder}/{filename}"
    print(f"Saving data to S3: s3://{bucket_name}/{s3_key}")
    json_data = json.dumps(data)
    s3.put_object(
        Bucket=bucket_name,
        Key=s3_key,
        Body=json_data.encode("utf-8"),
        ContentType="application/json",
    )
    print("Data uploaded to S3 successfully.")
    return s3_key



"""
calls both functions to fetch data from API and store in S3."""
def fetch_and_store_api_data():
    data = fetch_api_data(API_URL)
    s3_key = upload_json_to_s3(data, S3_BUCKET, S3_API_PREFIX)
    return {"s3_location": f"s3://{S3_BUCKET}/{s3_key}", "s3_key": s3_key}
