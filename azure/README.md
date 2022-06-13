### Azure Tag to IPList

Retrieve Azure tags and virtual machine IP addresses within an Azure subscription.
Each Azure tag / value will generate a new IPList with format `tag_value`.

For example, if the azure tag value associated with a given VM was
tag = 'type' and value was 'linux' (for example), the SMC IPList would be
named "type_linux".

Any host IP values retrieved from the Azure SDK client are then used
to populate the SMC using IPList.update_or_create.

If an existing IPList already exists and the contents of that list
are identical, the act of calling IPList.update_or_create should not yield a
pending change in SMC (ie. this should be an idempotent call since the state
is the same).

#### Setup

Clone this repo

`git clone https://github.com/Forcepoint/fp-NGFW-dynamic-tags

Setup a virtualenv where the application packages can be installed:

```
cd fp-NGFW-dynamic-tags/azure
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

Run the script with help:

`python3 main.py --help`

#### Running the program

Before running this, you will need to create a file ".env" within the base
directory of this repo on your local system.

Within the .env, set the following vars:

```
AZURE_TENANT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
AZURE_CLIENT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
AZURE_CLIENT_SECRET="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

You can optionally provide a subscription ID as well:

`AZURE_SUBSCRIPTION_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"`

*NOTE*: If subscription ID is NOT provided, ALL authorized subscription IDs
available for the API client ID will be processed.

For more information on authentication from the azure SDK clients:

[Authenticate Azure services using service principals](https://docs.microsoft.com/en-us/azure/developer/python/sdk/authentication-local-development-service-principal?tabs=azure-portal)

To allow IP Lists to be updated within SMC, you must also provide SMC
connection related information within the same .env.

To do this, first go to SMC and create an API Client
(Configuration -> Administration) and generate an authentication key.

Add the following parameters to the .env (same as above) for the SMC, see also:

```
SMC_ADDRESS=https://xx.xx.xxx.xxx:8082
SMC_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXX
SMC_CLIENT_CERT=/path/to/cert
SMC_TIMEOUT=30
SMC_API_VERSION=6.11
```

For more information on SMC related env vars available,
[Forcepoint SMC-python](https://fp-ngfw-smc-python.readthedocs.io/en/latest/pages/session.html#creating-the-session)

*NOTE*: Since this script leverages both Azure and Forcepoint client SDKs,
it can be run from anywhere as long as there is connectivity between this
script client and the authorization endpoints (SMC/Azure). It could be run
in Azure, on the SMC, on a remote host in AWS, etc.


#### Using optional Docker container

If you prefer to use a docker container, a Dockerfile is provided along
with wrapper scripts to build and run.

To build the container for your environment, run build:

```
sh build.sh
```

Once the docker container is built, you can run it using the helper bash script:

```
chmod +x fp-azure-tag-to-iplist.sh
sh fp-azure-tag-to-iplist.sh --help
```

*NOTE*: The dockerized version still requires the .env file with credentials
in the current directory.

Pass switches to the script like you would normally, i.e. to report only:

```
sh fp-azure-tag-to-iplist.sh --report_only
```

#### Certificate Validation

This client requires certificate validation to communicate with the SMC API.
To set up API for SSL validation, see also
[Forcepoint SMC-python sessions](https://fp-ngfw-smc-python.readthedocs.io/en/latest/pages/session.html)

Use the SMC_CLIENT_CERT env variable to set the fully qualified path for
the certificate / CA that signed the SMC API certificate.

When using docker, the certificate is mounted directly into the container and
can therefore be replaced easily.

