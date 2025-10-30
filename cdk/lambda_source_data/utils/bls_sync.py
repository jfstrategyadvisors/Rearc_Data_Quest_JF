import requests
import boto3
from bs4 import BeautifulSoup

# BLS productivity data directory URL
BLS_URL = "https://download.bls.gov/pub/time.series/pr/"

# S3 bucket name
S3_BUCKET = "rearc-data-quest-jf"

# S3 prefix (folder path within the bucket where files will be stored)
S3_PREFIX = "time-series/"

"""
Goal
Read the BLS directory listing to pull all pr. filenames.
Returns a list of filenames found in the directory.
Notes
was difficult to parse the BLS, I have never parsed HTML before.
Had to research but found BeautifulSoup made it easy.
Used href to get the file name from the link.
"""
def get_file_list(url):

    headers = {"User-Agent": "joshua.finlayson@outlook.com"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    files = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and "/pr/pr." in href:
            filename = href.split("/")[-1]
            files.append(filename)
    return files

"""
Goal
List all files that we already have in S3 bucket for time seris.

Notes
used boto3 to see what files are already in S3.
"""
def get_s3_files(bucket, prefix):
    s3 = boto3.client("s3")
    files = []
    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" in response:
            for obj in response["Contents"]:
                key = obj["Key"]
                filename = key.split("/")[-1]
                if filename:
                    files.append(filename)
    except Exception as e:
        print(f"Error listing S3 files: {e}")
        return files
    return files


"""
Goal
Sync files from BLS website to S3 bucket.
Only uploads files that don't already exist in S3.

Notes
Compares list of files from BLS website to list of files in S3.
Uploads only the missing files.
Added user agent to requests to avoid 403 errors.
"""

def sync_files_to_s3(bls_url, bucket_name, prefix):
    bls_files = get_file_list(bls_url)
    s3_files = get_s3_files(bucket_name, prefix)
    files_to_upload = [f for f in bls_files if f not in s3_files]
    print(f"\nFiles to upload: {files_to_upload}")
    s3 = boto3.client("s3")
    for file_name in files_to_upload:
        print(f"Downloading {file_name} from BLS...")
        file_url = bls_url + file_name
        headers = {"User-Agent": "joshua.finlayson@outlook.com"}
        response = requests.get(file_url, headers=headers)
        response.raise_for_status()
        print(f"Uploading {file_name} to S3...")
        s3_key = prefix + file_name
        s3.put_object(Bucket=bucket_name, Key=s3_key, Body=response.content)
        print(f"Uploaded {file_name}")

    print(f"\nSync complete! Uploaded {len(files_to_upload)} files.")
