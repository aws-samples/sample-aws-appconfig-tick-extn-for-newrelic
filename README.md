# AWS AppConfig Deployment Tick New Relic Sample Extension

This is a sample AWS AppConfig
[extension](https://docs.aws.amazon.com/appconfig/latest/userguide/working-with-appconfig-extensions-about.html)
to show integrating the `AT_DEPLOYMENT_TICK` event with New Relic - that is,
allowing AppConfig to be aware of the state of 3rd party monitoring as a
deployment runs.

The Lambda function is invoked regularly by AWS AppConfig during a deployment
(including the baking period at the end), and checks an Amazon SQS Queue for
messages. The New Relic environment is configured to send a message to this
Queue if there is an issue with an environment, via the New Relic Workflows
feature. If the Lambda function receives a message from the Queue, then it
responds to AWS AppConfig to tell it to roll back the deployment.

## Prerequisites

Please see the [AWS AppConfig
documentation](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html)
for details on configuring the service.

You will need a New Relic account with one or more workloads configured as
required to monitor your environment.

Ensure you have an up-to-date Python install available, and [AWS CDK
v2](https://docs.aws.amazon.com/cdk/v2/guide/home.html) installed.

You will need Docker or an equivalent installed and running for CDK to build
the Lambda function.

## Setting up

1. Clone this repo
2. In the cloned repo, create a Python virtual environment: `python -m venv .venv`
3. Activate your virtual environment: `source .venv/bin/activate`
4. Install the Python dependencies: `pip install -r requirements.txt`
5. Ensure you have suitable AWS credentials (and a region) configured in your environment
6. If you have not bootstrapped this AWS account/region for CDK previously, run
   `cdk bootstrap`. (It's safe to rerun if you're not sure.)
7. If needed, adjust the Lambda architecture in
   `appconfig_newrelic_tick_extn/appconfig_newrelic_tick_extn_stack.py` around
   line 69 to match your build environment.
8. Deploy this CDK app by running `cdk deploy`.
9. Note the value of the `nrqueue` and `nrpolicy` outputs from CDK as you'll
   need it in a moment. If you miss them, you can find it again by running these
   commands or by looking at the Outputs for the
   `AppconfigNewRelicTickExtnStack` in the CloudFormation console:
   ```bash
   aws cloudformation describe-stacks \
       --stack-name AppconfigNewRelicTickExtnStack \
       --query 'Stacks[0].Outputs[?OutputKey==`nrqueue`].OutputValue' \
       --output text
   aws cloudformation describe-stacks \
       --stack-name AppconfigNewRelicTickExtnStack \
       --query 'Stacks[0].Outputs[?OutputKey==`nrpolicy`].OutputValue' \
       --output text
   ```
10. Follow the New Relic [set up
    instructions](https://docs.newrelic.com/docs/workflow-automation/setup-and-configuration/set-up-aws-credentials/)
    to create an IAM role in your AWS Account which New Relic can assume. When
    you get to the **Add Permissions** step, attach the policy created by CDK
    (the `nrpolicy` Output). There is no need to attach other policies unless
    you have a specific requirement for them. Make a note of the Role's ARN for
    the next step.
11. In your New Relic account, create a Workflow using the **Deployment
    rollback** template. See New Relic's [Use a
    template](https://docs.newrelic.com/docs/workflow-automation/create-a-workflow-automation/use-a-template/)
    documentation for details. When running the Workflow, use the value of the
    `nrqueue` output for `AwsQueueUrl`, specify the region this sample was
    deployed to for `AwsRegion`, and the ARN of the IAM Role you created above
    for `AwsRoleArn`. Do not enter values for `NotificationHeaders` or
    `NotificationUrl`.
12. You can now associate the Extension with AWS AppConfig Applications,
    Environments, or Configuration Profiles (see the **Usage** section below).

## Usage

1. Navigate to the AppConfig console, then choose **Extensions**
2. Choose the **Sample New Relic Monitor Tick** extension, then choose **Add to
   resource**
3. Choose the **Resource Type** to associate the Extension with, and populate
   the following fields as required
4. Choose **Create Association to Resource**

You can now deploy a configuration (under a resource to which the extension is
attached) and your New Relic environment will be monitored during the
deployment.

If the workflow in New Relic publishes a message to the SQS Queue, the
deployment will automatically roll back.

You can find more details about the roll back by examining the event log for
the deployment. For example, using the AWS CLI:

```bash
aws appconfig get-deployment \
    --application-id 123abc \
    --environment-id 456def \
    --query '[State,EventLog]' \
    --deployment-number 1
```

## Cleaning up

1. Detach the policy created above from the IAM Role you created. If no longer
   required, delete the IAM role
2. Navigate to the AppConfig console, then choose **Extensions**
3. Choose the **Sample New Relic Monitor Tick** extension
4. For each entry under **Associated resources**, choose the radio button then
   choose **Remove association**, then choose **Delete**
5. Once you have removed all the Associated resources, you can run `cdk
   destroy` to remove all resources created by the app
6. Delete the New Relic Workflow you created if it is no longer required

## Additional resources

* [Monitoring deployments for automatic rollback](https://docs.aws.amazon.com/appconfig/latest/userguide/monitoring-deployments.html)
* [Creating a custom AppConfig Extension](https://docs.aws.amazon.com/appconfig/latest/userguide/working-with-appconfig-extensions-creating-custom-extensions.html)
* New Relic blog post: [Automatic Feature Flag Rollbacks](https://newrelic.com/blog/news/aws-appconfig-and-new-relic-workflow-automation)
* [New Relic Workflow Automation](https://newrelic.com/blog/news/workflow-automation-ga)

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This sample is licensed under the MIT-0 License. See the LICENSE file.
