## Part 1: Data Sourcing & Initial Research

### New Learnings

#### `raise_for_status()` Method
- **Documentation:** [GeeksforGeeks - Response raise_for_status()](https://www.geeksforgeeks.org/python/response-raise_for_status-python-requests/)
- **What it does:** Method from the `requests` library that checks HTTP status codes and raises an exception for error status codes
- **Previous approach:** In my current role, we used custom error handling with `response.status_code == 200`, `>= 400`, etc.

#### BeautifulSoup for HTML Parsing
- **Purpose:** Dynamically parse HTML to extract data
- **Resources:**
  - [Stack Overflow - Best library to parse HTML with Python 3](https://stackoverflow.com/questions/2505041/best-library-to-parse-html-with-python-3-and-example)
  - [BeautifulSoup Documentation](https://beautiful-soup-4.readthedocs.io/en/latest/)

### Data Quality Issues

**Q05 Quarter Issue**
- Found "Q05" entries in the dataset, which doesn't make sense for quarterly data
- **Resolution:** Removed invalid Q05 entries

**Missing 2020 Data**
- No data available from 2020 (COVID year)

### Blockers & Resolutions

#### HTTP 403 Forbidden Error

**Problem:**
```
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: 
https://download.bls.gov/pub/time.series/pr/
```

**Resolution:**
- Added `User-Agent` header to the request
- Included email in headers as required by BLS website

---

## Part 2: Infrastructure Decision Making

### Tool Selection Research

**Context:**
Need to create an automated data pipeline with:
- Lambda function to pull data from two sources (public dataset + API)
- S3 bucket for data storage
- Lambda function for data analysis
- SQS queue triggered by S3 file creation
- Automation of the entire workflow

**Options Evaluated:**
1. AWS CloudFormation (native)
2. AWS CDK (Cloud Development Kit)
3. Terraform

### Decision: AWS CDK with Python

## Part 3: Infrastructure Implementation

### Architecture Diagram
```
EventBridge (Cron: Daily 10AM EST)
    ↓
IngestLambda (Python 3.12)
    ↓
S3 Bucket (rearc-data-quest-jf)
    ↓ (S3 Event Notification)
SQS Queue
    ↓ (Event Source Mapping)
AnalysisLambda (Python 3.12 + pandas)
    ↓
CloudWatch Logs (Analysis Results)
```

### CDK Stack Components

#### Lambda Functions
1. **IngestLambda**
   - Downloads BLS time series data
   - Fetches population API data
   - Stores both datasets in S3

2. **AnalysisLambda**
   - Runs pandas-based analysis on datasets
   - Joins data from both sources
   - Calculates statistics and generates reports

#### Project Structure
```
cdk/
|-- app.py                        # CDK app entry point
|-- cdk/
│   |-- cdk_stack.py             # Infrastructure definition
|-- lambda_source_data/
│   |-- lambda_source_data.py    # Ingest Lambda handler
│   |-- utils/                   # BeautifulSoup, requests
|-- lambda_analysis/
    |-- lambda_analysis.py        # Analysis Lambda handler
    |-- analysis.py               # Pandas analysis functions
```

---

## Part 4: Major Issues & Resolutions

### Issue: Pandas Import Error in Lambda

#### Problem
Lambda function crashed with:
```
Runtime.ImportModuleError: Unable to import module 'lambda_analysis':
Unable to import required dependencies:
numpy: Error importing numpy: you should not try to import numpy from
        its source directory; please exit the numpy source tree, and relaunch
        your python interpreter from there.
```

#### Root Cause
Installing pandas with `pip install pandas -t lambda_analysis/` on macOS:
- Downloads macOS-compiled binaries (incompatible with Lambda's Amazon Linux 2023)

#### Solution: Klayers (Lambda Layer)

**What is Klayers?**
- Public Lambda layer repository for Python packages
- Pre-compiled for Lambda's Amazon Linux environment

**Implementation:**
```python
pandas_layer = _lambda.LayerVersion.from_layer_version_arn(
    self, "PandasLayer",
    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-pandas:17"
)
```

---

## Part 5: Analysis Results

### Population Statistics (2013-2018)
- **Mean:** 322,069,808
- **Standard Deviation:** 4,158,441

### Best Year per Series
Successfully calculated the best performing year for all series_ids in the dataset
``` series_id  year   value
 PRS30006011  2022  16.400
 PRS30006012  2022  13.000
 PRS30006013  1998 564.713
 PRS30006021  2010  14.200
 PRS30006022  2010   8.900
 PRS30006023  2014 402.512
 PRS30006031  2022  16.400
 PRS30006032  2021  13.900
 PRS30006033  1998 561.703
 PRS30006061  2022  29.600
```
### Series PRS30006032 Report
Generated report with 10 records including joined population data
```
 series_id    year   period  value  Population
 PRS30006032  2013    Q01    0.5   316128839
 PRS30006032  2014    Q01   -0.1   318857056
 PRS30006032  2015    Q01   -1.7   321418821
 PRS30006032  2016    Q01   -1.4   323127515
 PRS30006032  2017    Q01    0.9   325719178
 PRS30006032  2018    Q01    0.5   327167439
 PRS30006032  2019    Q01   -1.6   328239523
 PRS30006032  2021    Q01    0.7   331893745
 PRS30006032  2022    Q01    5.3   333287562
 PRS30006032  2023    Q01    0.3   334914896
```
---

## Resources & References

### Klayers (Lambda Layers)
- **GitHub Repository:** https://github.com/keithrozario/Klayers
- **API Endpoint:** https://api.klayers.cloud/api/v2/p3.12/layers/us-east-1/pandas

### AWS CDK Documentation
- **Lambda Constructs:** https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda.html
- **S3 Notifications:** https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3_notifications.html

### Python Libraries
- **BeautifulSoup4:** https://beautiful-soup-4.readthedocs.io/en/latest/
- **Requests Library:** https://www.geeksforgeeks.org/python/response-raise_for_status-python-requests/

### Data Sources
- **BLS Time Series Data:** https://download.bls.gov/pub/time.series/pr/




### AI Question:

Prompt:
"I have to create a data pipeline that grabs data from two sources one is a public dataset from a link that was provided to me, the other is a API url that was also provided. I need to save each of the sources data to an S3 bucket then write a python script to so analysis on the data and create a report. Now that i finished all three of those steps i need to use AWS CloudFormation, AWS CDK, or Terraform to create a data pipeline that will automate the steps listed above. In the pipeline i need a lambda to run the data pull and a lambda to perform the data analysis. It also needs to include a sqs queue that will populate every time the json file is written to s3.
I have experience working with a cloud formation template with lambdas but it seems like it would be the most work to configure AIM roles and Event bridge schedules to make the pipeline run. I dont have any experience with Terraform and AWS CDK. 
Based on all of that information which is the best choice for me to use?"

Response:

Based on your situation, AWS CDK (with Python) is the best choice for you. Here's why:
Why AWS CDK is Ideal for Your Case
1. Leverage Your Existing Python Skills

You're already writing Python scripts for data analysis
CDK lets you define infrastructure in Python - no new language to learn (unlike Terraform's HCL)
Your pipeline logic and infrastructure code can use the same language

2. Dramatically Reduces Boilerplate

CDK's high-level constructs automatically handle IAM roles, policies, and permissions
S3 → SQS → Lambda wiring is just a few lines of code
Example: bucket.add_event_notification(s3.EventType.OBJECT_CREATED, s3n.SqsDestination(queue)) handles all the configuration CloudFormation would require dozens of lines for

3. Built for Your Exact Use Case

CDK has constructs specifically for Lambda functions with automatic bundling of Python dependencies
EventBridge scheduling is simplified with built-in patterns
S3 event notifications are trivial to configure

4. Lower Learning Curve Than Terraform

Since you have CloudFormation experience, CDK will feel familiar (it synthesizes to CloudFormation)
You can always run cdk synth to see the generated CloudFormation if you need to debug
Terraform requires learning HCL, state management, and a completely different ecosystem

Quick Comparison
CloudFormation: You already know it's verbose for your needs - lots of manual IAM configuration
CDK: ~50-100 lines of readable Python vs. 300+ lines of YAML for the same pipeline
Terraform: Would work, but requires learning HCL from scratch when CDK lets you use Python