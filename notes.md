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