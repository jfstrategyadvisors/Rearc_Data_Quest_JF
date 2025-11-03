#### Part 1: AWS S3 & Sourcing Notes
Things I didnt know and needed to research:


raise_for_status
https://www.geeksforgeeks.org/python/response-raise_for_status-python-requests/

The raise_for_status() method belongs to the Response object in the requests library. It checks the HTTP status code of the response:

Never used raise for status before, In my current gig we used custom error handling to check for status codes by doing response.status_code == 200 , >= 400 etc


### Findings
found that there was Q05 in the data which doesnt make sense. removed that. Maybe keep it... revisit
There is no data from 2020? COVID year?



### get contents of url: BeautifulSoup
How to pasrse the HTLM to get all the data dynamically
https://stackoverflow.com/questions/2505041/best-library-to-parse-html-with-python-3-and-example

# BS find all 
for link in soup.find_all('a'):
    print(link.get('href'))
https://beautiful-soup-4.readthedocs.io/en/latest/




## Blockers:
  File "/Users/joshfinlayson/Documents/GitHub/Rearc_Data_Quest_JF/.venv/lib/python3.12/site-packages/requests/models.py", line 1026, in raise_for_status
    raise HTTPError(http_error_msg, response=self)
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: https://download.bls.gov/pub/time.series/pr/
Resolution:
Add User-Agent


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

---

## Part 4: AWS CDK Infrastructure & Lambda Deployment

### Infrastructure Overview
Built an automated data pipeline using AWS CDK (Python) with the following components:

**Architecture:**
```
EventBridge (Cron: Daily 9AM EST)
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

**1. Lambda Functions:**
- **IngestLambda**: Downloads BLS data and fetches population API data, stores in S3
  - Runtime: Python 3.12
  - Timeout: 5 minutes
  - Handler: `lambda_source_data.handler`

- **AnalysisLambda**: Runs pandas analysis on datasets from S3
  - Runtime: Python 3.12
  - Timeout: 5 minutes
  - Memory: 512 MB
  - Handler: `lambda_analysis.handler`
  - Uses Klayers Lambda Layer for pandas

**2. Event Orchestration:**
- EventBridge Rule: Scheduled to trigger IngestLambda daily at 15:00 UTC (9 AM EST)
- S3 Event Notification: Triggers when JSON files created in `api-data/` prefix
- SQS Queue: Buffers S3 notifications before Lambda processing

**3. Permissions:**
- IngestLambda: Read/Write to S3
- AnalysisLambda: Read from S3
- SQS: Receive messages from S3, allow Lambda to poll

---

### Major Issues Encountered & Resolutions

#### Issue 1: Pandas Import Error - "Unable to import required dependencies: numpy"

**Problem:**
Lambda function failed with error:
```
Runtime.ImportModuleError: Unable to import module 'lambda_analysis':
Unable to import required dependencies:
numpy: Error importing numpy: you should not try to import numpy from
        its source directory; please exit the numpy source tree, and relaunch
        your python interpreter from there.
```

**Root Cause:**
Installing pandas with `pip install pandas -t lambda_analysis/` on macOS downloads:
- macOS-compiled binaries (incompatible with Lambda's Amazon Linux 2023)
- Numpy development/source files instead of just runtime files
- When Lambda tried to import, it detected source directory and refused to load

**Attempted Solutions (Failed):**
1. ❌ Using AWS Data Wrangler Layer (ARN: `arn:aws:lambda:us-east-1:336392948345:layer:AWSSDKPandas-Python312:24`)
   - Error: `AccessDenied - not authorized to perform lambda:GetLayerVersion`
   - Reason: Layer is from different AWS account, requires special permissions

2. ❌ Installing with platform flag: `pip install --platform manylinux2014_x86_64 --only-binary=:all: --target . pandas`
   - Still included source files that caused import errors

3. ❌ Using Docker without having it installed
   - Command: `docker run --rm -v "$PWD":/var/task public.ecr.aws/lambda/python:3.12 pip install pandas -t /var/task/`
   - Error: `zsh: command not found: docker`

**Working Solution:**
Used **Klayers** - a public Lambda layer repository specifically designed for Python packages:
- Layer ARN: `arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-pandas:17`
- Includes: pandas 2.2.3, numpy 2.2.6, and all dependencies
- Pre-compiled for Lambda's Amazon Linux environment
- Updated monthly with latest package versions

**CDK Implementation:**
```python
pandas_layer = _lambda.LayerVersion.from_layer_version_arn(
    self, "PandasLayer",
    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p312-pandas:17"
)

lambda_analysis = _lambda.Function(
    self, "AnalysisLambda",
    runtime=_lambda.Runtime.PYTHON_3_12,
    handler="lambda_analysis.handler",
    code=_lambda.Code.from_asset("lambda_analysis"),
    events=[lambda_event_sources.SqsEventSource(data_queue)],
    timeout=Duration.minutes(5),
    memory_size=512,
    layers=[pandas_layer],
)
```

**Key Learnings:**
- Lambda requires Linux-compatible binaries, not macOS/Windows versions
- Lambda layers are the cleanest solution for large dependencies like pandas
- AWS's own layers may have access restrictions; community layers like Klayers are reliable alternatives
- Docker method works but requires Docker Desktop installed locally

---

#### Issue 2: Understanding SQS Queue Behavior

**Confusion:**
Expected to see messages sitting in SQS queue, but queue showed 0 messages despite pipeline working.

**Resolution:**
This is **expected behavior**. SQS with Lambda event source mapping works as:
1. S3 sends message to SQS
2. Lambda polls queue and immediately picks up message (becomes "invisible")
3. Lambda processes successfully
4. Lambda **automatically deletes** message from queue
5. Queue returns to 0 messages

**Queue Metrics:**
```bash
ApproximateNumberOfMessages: 0              # No messages waiting
ApproximateNumberOfMessagesNotVisible: 0   # No messages being processed
ApproximateNumberOfMessagesDelayed: 0      # No delayed messages
```

An empty queue = healthy, fast-processing system. Messages only pile up if:
- Lambda is failing
- Lambda is disabled/misconfigured
- Processing is slower than incoming rate

---

### CDK Deployment Process

**Setup:**
```bash
cd cdk
python -m venv .venv
source .venv/bin/activate
pip install aws-cdk-lib constructs
```

**Deployment Commands:**
```bash
cdk bootstrap  # First time only - creates CDK staging bucket
cdk synth      # Preview CloudFormation template
cdk deploy     # Deploy stack to AWS
cdk destroy    # Tear down all resources
```

**File Structure:**
```
cdk/
├── app.py                    # CDK app entry point
├── cdk/
│   └── cdk_stack.py         # Infrastructure definition
├── lambda_source_data/
│   ├── lambda_source_data.py # Ingest Lambda handler
│   └── [dependencies]        # BeautifulSoup, requests
└── lambda_analysis/
    ├── lambda_analysis.py    # Analysis Lambda handler
    └── analysis.py           # Pandas analysis functions
```

---

### Performance Metrics

**AnalysisLambda Execution:**
- Duration: 330-440ms (warm start), ~2.5s (cold start with layer)
- Memory Used: 185 MB / 512 MB allocated
- Init Duration (cold): 1.8 seconds (loading pandas layer)
- Cost per invocation: ~$0.000002 (very cheap)

**Analysis Results:**
- Population Statistics (2013-2018): Mean = 322,069,808, StdDev = 4,158,441
- Best Year per Series: Successfully calculated for all series_ids
- Series PRS30006032 Report: 10 records with joined population data

---

### Resources & References

**Klayers (Lambda Layers):**
- GitHub: https://github.com/keithrozario/Klayers
- API: https://api.klayers.cloud/api/v2/p3.12/layers/us-east-1/pandas
- Updates monthly with latest package versions

**AWS CDK Documentation:**
- Lambda Constructs: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda.html
- S3 Notifications: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3_notifications.html

**Alternative Solutions Considered:**
1. CDK Asset Bundling - Rejected due to complexity and Docker requirement
2. Creating custom Lambda Layer - Time-consuming, reinventing the wheel
3. AWS Data Wrangler managed layer - Access denied, account restrictions