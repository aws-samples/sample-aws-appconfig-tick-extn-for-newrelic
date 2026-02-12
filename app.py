#!/usr/bin/env python3

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import App, Aspects
from appconfig_newrelic_tick_extn.appconfig_newrelic_tick_extn_stack import AppconfigNewrelicTickExtnStack
from cdk_nag import AwsSolutionsChecks


app = App()
AppconfigNewrelicTickExtnStack(app, "AppconfigNewRelicTickExtnStack")

Aspects.of(app).add(AwsSolutionsChecks(verbose=True))

app.synth()
