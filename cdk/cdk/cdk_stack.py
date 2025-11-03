from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_events as events,
    aws_sqs as sqs,
    aws_s3_notifications as s3n,
    aws_lambda_event_sources as lambda_event_sources,
    aws_events_targets as targets,
)
from constructs import Construct


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Reference existing S3 bucket
        data_bucket = s3.Bucket.from_bucket_name(
            self, "DataBucket", 
            "rearc-data-quest-jf"
        )

        # SQS queue for triggering analysis
        data_queue = sqs.Queue(
            self, "DataQueue",
            visibility_timeout=Duration.seconds(300)
        )
        # Lambda 1: Ingest data from BLS and API (Parts 1 & 2)
        lambda_source_data = _lambda.Function(
            self, "IngestLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_source_data.handler",
            code=_lambda.Code.from_asset("lambda_source_data"),
            timeout=Duration.minutes(5),
        )
        # Lambda 2: Analysis (Part 3)
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

        # Grant S3 permissions to both Lambdas
        data_bucket.grant_read_write(lambda_source_data)
        data_bucket.grant_read(lambda_analysis)


        # Notify SQS when a new JSON file is created in the API data prefix
        data_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SqsDestination(data_queue),
            s3.NotificationKeyFilter(prefix="api-data/", suffix=".json"),
        )
        # EventBridge Rule: Schedule ingest Lambda to run daily at 10 AM EST
        events.Rule(
            self,
            "DailyIngestSchedule",
            schedule=events.Schedule.cron(hour="15", minute="0"),
            targets=[targets.LambdaFunction(lambda_source_data)],
        )