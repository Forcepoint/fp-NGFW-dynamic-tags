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

