## ecs-utils

ecs-utils is a collection of useful python scripts and libraries for use with AWS Elastic Container Service (ECS). The scripts:
- rolling-replace: performs a no-downtime replacement of instances in an ECS cluster (autoscaling group)
- service-check: polls an ECS service for health (deployment completion)
- param: a wrapper script for interacting with AWS Parameter store
- kms-create: wrapper for creating kms keys
- kms-crypt: wrapper for creating kms encrypted data
- documentation for using the above tools in a production environment

AWS provides many examples of best practices for ECS in the context of using Cloudformation. These tools and docs were created to support an environment provisioned with Terraform. An example implementation of an ECS cluster in terraform and an example application that uses AWS parameter store (and these scripts) can be found here: https://github.com/navapbc/tf-ecs-example

### Installation

Have a recent version of python 3 (>= 3.6) and pip installed. Then install with pip.

```
pip install git+git://github.com/navapbc/ecs-utils.git@v0.0.2
```

### Configure AWS access

These scripts use AWS boto which assumes you have an AWS account and have set up credentials on your local machine:

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html

### rolling-replace

rolling-replace Rolling ASG replacement script.

This script provides a pattern for replacing EC2 instances in an Autoscaling
group running ECS (e.g. when updating to the latest ECS agent AMI).

It fits into a deployment pattern where the Autoscaling Group resource is updated with a new launch configuration (with a new AMI). That change must be followed with an orchestration where old instance are replaced. This script performs that orchestration, safely. It assumes you have already updated the launch cfg.(e.g. updated the desired AMI id, with terraform). This script does not update the launch cfg.

1. Set an instance to draining (see: AWS docs on container instance draining)
2. Wait for it to drain
   (recommendation: lower the AWS default deregistration delay of 300s)
3. Terminate the instance
4. Wait for the new instance (with the new AMI) to launch and tasks to
   be scheduled there and tasks to pass container health checks.
5. Exit if that times out, or
6. Continue, repeating steps 1-5, for each instance
7. Return 0 if successful

The script does the above in batches, size chosen by the user.

The script makes every effort to avoid getting you into a bad place
1. It discovers the ECS services in your cluster, then checks that your ECS services are in a steady state *before* proceeding with instance replacement.
2. For simplicity, it follows a break one, make one pattern but does so in user defined batch size (default is 3 batches) to ensure a small loss in capacity.
3. It will balk if the batch size equals the current capacity
(because that will cause downtime).
4. You can optional specify the ami id that you're upgrading to, which will allow it to skip instances that have already been upgraded. Otherwise, it will just replace all of your instances, in batches.

WARNING: review your current autoscaling scaling configuration before using this script.

This script does not rollback. If your new AMI is failing, the script will exit after the first batch is deployed and leave it to you to rollback the launch configuration (to the original AMI) and run the script again.

NOTE: this script considers it's work complete once all instances have been terminated and your ECS services have been restored to a steady state.  e.g. if steady state has been acheived it won't wait for the last batch of instances to come up.

Usage:
```
rolling-replace --cluster-name dev-vpc-cluster-a --region us-east-1 --ami-id ami-yournewamiid --batches 3
```

--ami-id is optional. If you don't provide it, rolling-replace will perform the rolling replacement without checking the running ami id.

--batches is optional (default is 3). Choose this value carefully. Each batch can take 5-10 minutes. However, a batch size of 3 implies a 1/3 loss in capacity, so you must ensure that is acceptable in your production system. You can do instance replacement in off hours, over-provision your ASG, or choose a higher --batches value.

Note: the script assumes that you have container health checks configured for any currently running service.

### service-check

This script polls an ECS service after a task configuration change (e.g. docker image update) and returns 0 when all tasks show container 'HEALTHY' and the deployment 'PRIMARY' with the desired number of tasks running.

Usage:
```
service-check --cluster-name dev-vpc-cluster-a --region us-east-1 your-ecs-service-name
```

If the script detects a deployment that is not recent it considers it "stale" and waits for new info to show up. You must run this script within 2 minutes of updating your service/task_definition. You can increase the stale threshold by providing the flag ```--stale-s``` 

### kms-create

kms-create creates a kms key. See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.create_key

Usage:
```
kms-create --region us-east-1 --alias foo
```

### kms-crypt

kms-crypt encrypts and decrypts data in kms. See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/kms.html#KMS.Client.encrypt

Usage
```
# encrypt with an existing kms key (alias: foo)
kms-crypt --region us-east-1 --alias foo --context '{"foo":"bar"}' encrypt foosecret

# decrypt (using output from previous script)
kms-crypt --region us-east-1 --context '{"foo":"bar"}' decrypt ENCRYPTED_BLOB
```

### param

param is a boto3 wrapper for use with AWS Parameter store. It supports get, put, delete and list. See: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.put_parameter

Usage:
```
# store an value encrypted with an existing kms key
param --region us-east-1 --kms-key-alias foo put /myservice/foo mysecret123
# list params matching the namespace
param --region us-east-1 list /myservice
# get a param value
param --region us-east-1 get /myservice/foo
```
