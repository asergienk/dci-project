# API of the engine analyzer

This repository is used for the development of the API to get the logs data in the appropriate format for the engine. 

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)


## Installation

- clone this repository

- use the package manager [pip](https://pip.pypa.io/en/stable/) to install dciclient:
```console
$ pip install python-dciclient
```
The package provides the API: a python module one can use to interact with a control server (`dciclient.v1.api.*`)


## Configuration

### Remoteci creation

DCI is connected to the Red Hat SSO. You need to log in `https://www.distributed-ci.io` with your redhat.com SSO account. Your user account will be created in our database the first time you connect.

After the first connection you can create a remoteci. Go to [https://www.distributed-ci.io/remotecis](https://www.distributed-ci.io/remotecis) and click `Create a new remoteci` button. Once your `remoteci` is created, you can retrieve the connection information in the `Authentication` column. Save this information in `remoteci.rc` file.

At this point, you can validate your credentials with the following commands:

```console
$ source remoteci.rc
```

If you see your remoteci in the list, everything is working great so far.

