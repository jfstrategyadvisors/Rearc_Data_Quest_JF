from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct


class CdkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_source_data = _lambda.Function(
            self, "IngestLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_source_data.handler",
            code=_lambda.Code.from_asset("lambda_source_data"),
        )
        lambda_analysis = _lambda.Function(
            self, "AnalysisLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_analysis.handler",
            code=_lambda.Code.from_asset("lambda_analysis"),
        )