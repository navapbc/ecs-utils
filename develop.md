## Setup

To develop and run tests you should have python and AWS set up properly.

You need to first install python3: https://www.python.org/downloads/release/python-363/ or `brew install python3` on osx

From the root of this directory:
```sh
python3 -m venv ecs-utils
source ecs-utils/bin/activate
pip install -r requirements.txt
python setup.py develop
```
 
You'll need to run `source mps/bin/activate` from the root folder of the project any time you create a new shell so that you'll have the correct python dependencies.

### Configure AWS access

These scripts use AWS boto which assumes you have an AWS account and have set up credentials on your local machine:

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
