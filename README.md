## ecs-util

ecs-util is a collection of useful python scripts and libraries for use with AWS Elastic Container Service (ECS). Highlights include:
- rolling_replace: performs a no-downtime replacement of instances in an ECS cluster (autoscaling group)
- service_check: polls an ECS service for health (deployment completion)
- param: a wrapper script for interacting with AWS Parameter store
- documentation for using the above tools in a production environment

AWS provides many examples of best practices for ECS in the context of using Cloudformation. These tools and docs were created to support an environment provisioned with Terraform (TODO: provide link to the example Terraform ECS template). 

### Installation

Have a recent version of python 3 (>= 3.5) and pip installed. Then install with pip.

```
pip install git+git://github.com/navapbc/ecs-scripts#egg=ecs-util
```

### Configure AWS access

These scripts use AWS boto which assumes you have an AWS account and have set up credentials on your local machine:

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
