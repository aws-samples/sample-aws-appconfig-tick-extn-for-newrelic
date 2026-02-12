# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from typing import cast
from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_appconfig,
    aws_lambda,
    aws_iam as iam,
    aws_lambda_python_alpha as aws_python,
    aws_sqs,
)
from cdk_nag import NagSuppressions, NagPackSuppression
from constructs import Construct


class AppconfigNewrelicTickExtnStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        queue = aws_sqs.Queue(
            self,
            "NewRelicAppconfigQueue",
            retention_period=Duration.minutes(1),
            enforce_ssl=True,
        )
        NagSuppressions.add_resource_suppressions(
            queue,
            [
                NagPackSuppression(
                    id="AwsSolutions-SQS3",
                    reason="Messages on this queue are only relevant at the time they're received, so no DLQ is required",
                )
            ],
        )

        policy = iam.ManagedPolicy(
            self,
            "appconfig_nr_policy",
            description="Managed Policy for sample AWS AppConfig New Relic Extension",
            statements=[
                iam.PolicyStatement(
                    actions=["sqs:SendMessage"],
                    resources=[queue.queue_arn],
                    effect=iam.Effect.ALLOW,
                )
            ],
        )

        function = aws_python.PythonFunction(
            self,
            "tick_fn",
            index="index.py",
            runtime=aws_lambda.Runtime.PYTHON_3_14,
            handler="lambda_handler",
            entry="lambda",
            bundling=aws_python.BundlingOptions(
                asset_excludes=[
                    ".venv",
                    ".mypy_cache",
                    ".ruff_cache",
                    "requirements-dev.txt",
                ]
            ),
            description="AppConfig Extension to handle deployment tick with New Relic",
            # NOTE: adjust this if needed to match your build environment (ARM_64 or X86_64)
            architecture=aws_lambda.Architecture.ARM_64,
            environment={
                "NR_QUEUE": queue.queue_url,
            },
        )
        queue.grant_consume_messages(function)

        NagSuppressions.add_resource_suppressions(
            function,
            [
                NagPackSuppression(
                    id="AwsSolutions-IAM4",
                    reason="Managed Policy just allows Lambda access to CWL",
                    applies_to=[
                        "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                ),
            ],
            apply_to_children=True,
        )

        appconfig_svc_role = iam.Role(
            self,
            "appconfig_role",
            assumed_by=cast(
                iam.IPrincipal, iam.ServicePrincipal("appconfig.amazonaws.com")
            ),
        )
        function.grant_invoke(appconfig_svc_role)

        NagSuppressions.add_resource_suppressions(
            appconfig_svc_role,
            [
                NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Wildcard applies to function aliases and version; policy is restricted to function by arn",
                    applies_to=["Resource::<tickfnB386E70B.Arn>:*"],
                ),
            ],
            apply_to_children=True,
        )

        aws_appconfig.Extension(
            self,
            "tick_extn",
            actions=[
                aws_appconfig.Action(
                    action_points=[aws_appconfig.ActionPoint.AT_DEPLOYMENT_TICK],
                    event_destination=aws_appconfig.LambdaDestination(
                        cast(aws_lambda.IFunction, function)
                    ),
                    execution_role=cast(iam.IRole, appconfig_svc_role),
                    description="Deployment Tick action point",
                )
            ],
            description="A sample Extension to watch New Relic status queue during a deployment and roll back if messages are received",
            extension_name="Sample New Relic Monitor Tick",
        )

        CfnOutput(
            self,
            "nrqueue",
            value=queue.queue_url,
            description="The SQS Queue URL to which messages should be posted to notify of issues",
        )
        CfnOutput(
            self,
            "nrpolicy",
            value=policy.managed_policy_name,
            description="The IAM Policy to attach to the Role for New Relic",
        )
