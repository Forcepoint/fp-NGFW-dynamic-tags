### AWS Tag collector


### Installation

Clone this repo

`git clone https://github.com/Forcepoint/fp-NGFW-dynamic-tags

Setup a virtualenv where the application packages can be installed:

```
cd fp-NGFW-dynamic-tags/aws
python3 -m venv env
```

NOTE: Depending on your version of python and OS, the above method for
creating a virtualenv may be different.

Enter into virtual env:

`source env/bin/activate`

Update pip:

`python3 -m pip install --upgrade pip`

Install the packages

`pip3 install -r requirements.txt`


### Configure AWS credentials and IAM policy

Within AWS console, navigate to the Identity and Access Management (IAM)
configuration

Select Users

Add User

Specify username

Select AWS credential type: Access key - programmatic access

Give the user account the following roles:

```
AmazonEC2ReadOnlyAccess
AmazonVPCReadOnlyAccess
```

#### Running the program

Authentication to AWS is done using normal boto3 methods documented here
[AWS authentication](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)

The configuration file location will first be attempted from the local directory
where a file named 'config' could be located alongside this script. If it
doesn't exist, normal AWS methods are attempted.

See the config.env example file which just mirrors (and in fact just points to)
the config file location in the current directory as a convenience. It can still
be located whereever and used the same way you normally use your
~.aws/credentials, etc mappings.

