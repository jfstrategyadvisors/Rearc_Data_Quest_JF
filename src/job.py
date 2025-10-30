from utils.bls_sync import (
    sync_files_to_s3,
    get_file_list,
    get_s3_files,
    BLS_URL,
    S3_PREFIX,
    S3_BUCKET,
)
from utils.api_pull import fetch_and_store_api_data
from utils.analysis import load_both_datasets, run_all_analyses


if __name__ == "__main__":
    # ========== PART 1: BLS Data Sync ==========
    print("\n[PART 1] Syncing BLS data to S3...")
    print("-" * 70)

    print("Fetching files from BLS...")
    bls_files = get_file_list(BLS_URL)
    print(f"Found {len(bls_files)} files on BLS.")

    print("\nChecking S3 bucket...")
    s3_files = get_s3_files(S3_BUCKET, S3_PREFIX)
    print(f"Found {len(s3_files)} files in S3.")

    sync_files_to_s3(BLS_URL, S3_BUCKET, S3_PREFIX)

    print("\n" + "=" * 70)

    # ========== PART 2: API Data Fetch ==========
    print("\n[PART 2] Fetching data from DataUSA API...")
    print("-" * 70)

    result = fetch_and_store_api_data()

    # ========== PART 3: Data Analysis ==========
    print("\n[PART 3] Running Data Analysis...")
    print("-" * 70)

    bls_df, api_df = load_both_datasets()
    analysis_results = run_all_analyses(bls_df, api_df)

