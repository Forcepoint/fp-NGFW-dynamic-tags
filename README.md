# Public Cloud Tags for  Forcepoint NGFW Security Policy

These examples shows how to populate Microsoft Azure,
Amazon Web Services (AWS) and Google Cloud (GCP) tags to Forcepoint NGFW and NGFW Security Management Center (SMC).

These examples are provided *as-is* and the support is best effort based.

## Setup

Setup consists of cloning this repo, then installing package requirements from at least one of the cloud provider 
directories.

Clone this repo

`git clone https://github.com/Forcepoint/fp-NGFW-dynamic-tags`

### Configure for a cloud provider

Configuration for all cloud providers will be similar in nature, although some may have slight varianaces in runtime parameters depending on differing terminology or requirements.

For example, in GCP you must provide a `project_id` field to specify the resource, whereas in Azure you can provide a `subscription_id`.

*NOTE*: Check the README within each directory for specific installation requirements for each module.

All configurations are assuming that within a given cloud provider directory a unique python virtual environment will be used (RECOMMENDED).

A common pattern to install any given module (using GCP as an example):

Navigate to GCP directory and setup a virtualenv where the application packages can be installed:

```
cd fp-NGFW-dynamic-tags/gcp
python3 -m venv env
```

*NOTE*: Depending on your version of python and OS, the above method for creating
a virtualenv may be different.

Enter into virtual env:

`source env/bin/activate`

Update pip:

`python3 -m pip install --upgrade pip`

Install the cloud provider specific packages:

`pip3 install -r requirements.txt`

*NOTE*: Since all repo's share the same [Forcepoint smc-python](https://github.com/Forcepoint/fp-NGFW-SMC-python) requirement, you could create the virtaulenv at the base directory and use this for all provider packages.

### Run host element discovery

Each provider discovery provides a similar interface, although command line options may vary between providers.

To view all available commands, run with `--help` for more information:

```
cd gcp
python3 main.py --help`
```

For more information, each provider hosts a README that is specific to operations performed and available for each respective cloud.



