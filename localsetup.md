## Setup

Python is used for all of the deployment scripts. You need to first install python3: https://www.python.org/downloads/release/python-363/ or `brew install python3` on osx

From the root of this directory:
```sh
python3 -m venv ecs-scripts
source ecs-scripts/bin/activate
pip install -r requirements.txt
python setup.py install
```
 
If you're going to be actively developing, run `python setup.py develop`.

You'll need to run `source mps/bin/activate` from the root folder of the project any time you create a new shell so that you'll have the correct python dependencies.

After installing the python requirements, you should have the `aws-mfa` command. This allows you to mfa into aws from the command line and is a quick way to refresh your credentials.

### Configure AWS access

First you need an AWS account and a user with MFA set up in order to run the setup.

Set your credentials in your `~/.aws/credentials` file. It should look something like:

```
[your-aws-account-long-term]
aws_access_key_id = xxxxx
aws_secret_access_key = xxxx
aws_mfa_device = arn:aws:iam::xxx:mfa/xxxx

[your-aws-account]
assumed_role = False
```


You can then add this alias

```sh
alias <my-account>='export AWS_PROFILE=your-aws-account'
```

Note: 'your-aws-account' used in the credentials file and alias is an arbitrary name which you can change as needed (ie, 'cms-account', etc)

When you open a new shell to pick up those changes to your `~/.bashrc` file, you will be able to mfa by doing the following:

```sh
<my-account>
aws-mfa
```

### Install Terraform

Install version 0.11.7. This can be done manually from
https://releases.hashicorp.com/terraform/0.11.7/ or using [tfenv](https://github.com/kamatama41/tfenv), for example:

```sh
# Mac OS X:
brew install tfenv
tfenv install 0.11.7
```

### Install Docker

For Mac OS X: Follow the instructions https://docs.docker.com/docker-for-mac/install/
