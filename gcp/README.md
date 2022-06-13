### GCP Tag collector

`https://cloud.google.com/python/docs/reference`

### Installation

Clone this repo

`git clone https://github.com/Forcepoint/fp-NGFW-dynamic-tags

Setup a virtualenv where the application packages can be installed:

```
cd fp-NGFW-dynamic-tags/gcp
python3 -m venv env
```

NOTE: Depending on your version of python and OS, the above method for creating
a virtualenv may be different.

Enter into virtual env:

`source env/bin/activate`

Update pip:

`python3 -m pip install --upgrade pip`

Install the packages

`pip3 install -r requirements.txt`

### Configure credentials for IAM policy

Go to IAM & Admin and select `Service Accounts`

Under service accounts, create a new name and description and give Grant
ReadOnly access to compute resources

Once your service account is created, you can download the json formatted
credential config file which will be required for auth to GCP.
