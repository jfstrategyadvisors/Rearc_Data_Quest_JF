from analysis import load_both_datasets, run_all_analyses

def handler(event, context):
    # Load both datasets (BLS and API) from S3 into pandas DataFrames
    bls_df, api_df = load_both_datasets()
    # Run all analysis functions
    run_all_analyses(bls_df, api_df)

    return {"statusCode": 200, "body": "Data analysis complete"}