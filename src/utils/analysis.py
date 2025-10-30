import pandas as pd
import boto3
import io
import json
from datetime import datetime


S3_BUCKET = "rearc-data-quest-jf"
BLS_DATA_PREFIX = "time-series/"
API_DATA_PREFIX = "api-data/"
s3_client = boto3.client("s3")

""" 
Goal
Download the pr.data.0.Current file from use read_csv 
function to take the tab delimited file from S3 and load into a pandas dataframe.
notes
use the io.BytesIO to read the S3 object body directly into pandas.
cleaned up the dataframe by stripping whitespace from column names and string values.
Converted year to int and value to float for proper data types.
"""
def read_bls_data(
    bucket=S3_BUCKET, prefix=BLS_DATA_PREFIX, filename="pr.data.0.Current"
):
    s3 = s3_client
    s3_key = f"{prefix}{filename}"

    obj = s3.get_object(Bucket=bucket, Key=s3_key)
    df = pd.read_csv(io.BytesIO(obj["Body"].read()), sep="\t")

    df.columns = df.columns.str.strip()

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].str.strip()

    df["year"] = df["year"].astype(int)
    df["value"] = df["value"].astype(float)

    return df


"""
Goal
Download the population data JSON file from S3 and load into a pandas dataframe.
Notes
Used io.BytesIO to read the S3 object body directly.
Assuming we will be running this on a daily basis, 
I added a date_folder for good practice so we arent overwriting each days data
converted Population to int
"""
def read_api_data(
    bucket=S3_BUCKET,
    prefix=API_DATA_PREFIX,
    date_folder=None,
    filename="population_data.json",
):
    if date_folder is None:
        date_folder = datetime.now().strftime("%Y-%m-%d")
    s3 = s3_client
    s3_key = f"{prefix}{date_folder}/{filename}"

    obj = s3.get_object(Bucket=bucket, Key=s3_key)
    data = json.loads(obj["Body"].read())
    df = pd.DataFrame(data["data"])
    df["Population"] = df["Population"].astype(int)
    return df


"""
Goal
Load both BLS and API datasets into dataframes.
Notes
Seperated load for both datasets for clarity.
"""

def load_both_datasets():
    # Load both datasets
    bls_df = read_bls_data()
    api_df = read_api_data()

    return bls_df, api_df


""" 
Analysis Functions
Prompt:
Using the dataframe from the population data API (Part 2), 
generate the mean and the standard deviation of the annual US 
population across the years [2013, 2018] inclusive.

Goal
Pull in api_df and filter to years 2013-2018 then calculate mean and std dev
round to nearest whole number for display


"""


def analyze_population_trends(api_df):
    print("\nPopulation Statistics (2013-2018)")
    print("=" * 50)

    filtered_df = api_df[(api_df["Year"] >= 2013) & (api_df["Year"] <= 2018)]
    mean_population = filtered_df["Population"].mean()
    std_population = filtered_df["Population"].std()

    print(f"Years Analyzed: 2013-2018")
    # rounded to nearest whole number
    print(f"Mean Population (2013-2018): {mean_population:,.0f}")
    print(f"Standard Deviation (2013-2018) : {std_population:,.0f}")
    return {"mean_population": mean_population, "std_population": std_population}

"""
Prompt:
Using the dataframe from the time-series (Part 1), For every series_id, 
find the best year: the year with the max/largest sum of "value" for all quarters in that year.
 Generate a report with each series id, the best year for that series, and the 
summed value for that year. For example, if the table had the following values:

Goal:
find best yeart per series id by summing all quater together then finding the max year for each series id

Notes
pulled in bls_df and filtered to only use Q01 to Q04 since there are only four quarters in a year
group by series_id and year then sum the value column
for each series_id find the year with the maximum sum
sort by series_id
"""

def analyze_best_year_per_series(bls_df):
    quarterly_df = bls_df[bls_df["period"].isin(["Q01", "Q02", "Q03", "Q04"])].copy()
    yearly_sums = (
        quarterly_df.groupby(["series_id", "year"])["value"].sum().reset_index()
    )

    # For each series_id, find the year with the maximum sum
    best_years = yearly_sums.loc[yearly_sums.groupby("series_id")["value"].idxmax()]

    # Sort by series_id for readability
    best_years = best_years.sort_values(by="series_id").reset_index(drop=True)

    print(f"\nBest Year per Series_id")
    print("=" * 50)
    print(f"\nSample of Best Years (Top 10):")
    print(best_years.head(10).to_string(index=False))

    return best_years



"""
Prompt:
Using both dataframes from Part 1 and Part 2, generate a report that will provide the value 
for series_id = PRS30006032 and period = Q01 and the population for that given year
 (if available in the population dataset). The below table shows an example of one row that
 might appear in the resulting table:

Goal
have an output table with series_id, year, period, value, Population
join bls_df and api_df on year

Notes

need  Columns :series_id	year	period	value	Population in final report
api:
    {
      "Nation ID": "01000US",
      "Nation": "United States",
      "Year": 2016,
      "Population": 323127515
    },

BLS:
series_id   year period	value	footnote_codes

Combined table fields
BLS.series_id	(Both join on year)year	BLS.period	BLS.value	API.Population
filter series id = PRS30006032 and period = Q01

renamed Year to year in api_df for join and to match sample output
Did a left join since year 2020 is missing and there is more data in bls
filtered out rows where Population is null since we only want years with population data
"""

def analyze_series_and_population(
    bls_df, api_df, series_id="PRS30006032", period="Q01"
):
    print(f"\n[ANALYSIS 3] Series {series_id} with Population Data")
    print("=" * 50)

    filtered_bls = bls_df[
        (bls_df["series_id"] == series_id) & (bls_df["period"] == period)
    ].copy()

    api_df_clean = api_df[["Year", "Population"]].copy()
    api_df_clean.rename(columns={"Year": "year"}, inplace=True)

    merged = filtered_bls.merge(api_df_clean, on="year", how="left")

    result = merged[["series_id", "year", "period", "value", "Population"]]
    result = result[result["Population"].notnull()]
    result = result.sort_values("year").reset_index(drop=True)

    print(f"Found {len(result)} records for series_id={series_id}, period={period}")
    print(f"\nReport Preview:")
    print("-" * 70)
    result_display = result.copy()
    result_display["Population"] = result_display["Population"].astype(int)
    print(result_display.to_string(index=False))

    return result


"""
Used run_all_analyses to call all three analysis functions and return their results in a dictionary.
"""

def run_all_analyses(bls_df, api_df):
    pop_stats = analyze_population_trends(api_df)
    best_years_report = analyze_best_year_per_series(bls_df)
    series_population_report = analyze_series_and_population(bls_df, api_df)
    return {
        "population_stats": pop_stats,
        "best_years_report": best_years_report,
        "series_population_report": series_population_report,
    }
