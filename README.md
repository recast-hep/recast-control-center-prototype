# RECAST Control Center

[![Build Status](https://travis-ci.org/recast-hep/recast-control-center-prototype.svg?branch=master)](https://travis-ci.org/recast-hep/recast-control-center-prototype)
[![Code Health](https://landscape.io/github/recast-hep/recast-control-center-prototype/master/landscape.svg?style=flat)](https://landscape.io/github/recast-hep/recast-control-center-prototype/master)

## Introduction
This is an early prototype for the RECAST control center. This web application is used to launch jobs for different back-ends that perform the reinterpretation requested on the RECAST frtonend currently hosted at the [Perimeter Institute](http://recast.perimeterinstitute.ca). The goal for RECAST is to allow analysis reinterpretation for the community. 

It supports CERN SSO authentication which will allow for fine-grained control over which users are able to launch the reinterpretation jobs and/or upload the results to the front-end. This web application provides a plugin model for analyses. Currently, we have a template plugin for Rivet analyses that runs quickly. We are working with CERN IT's analysis preservation product to provide a template plugin for reinterpretation based on the full simulation, reconstruction, and event selection.

For convenience, one can initiate a request directly from the control center, which will be uploaded to the front-end.

## Prerequsites

* [Python 2.7](http://www.python.org/)
* redis
* python-devel
* gcc

## Basic Steps To Lunch Control Center

1. Install prerequisites
2. Install recast-control-center
3. Run server.py

## Quick Instructions For People That Think They Know What They Are Doing

```
wget https://github.com/recast-hep/recast-control-center-prototype/archive/master.zip
unzip master.zip
cd recast-control-center-prototype-master/
sudo pip install --process-dependency-links .
```

## Instructions for RHEL7

Install prerequsites:
```
sudo yum install redis python-devel gcc
sudo easy_install pip
```

Get the code:
```
wget https://github.com/recast-hep/recast-control-center-prototype/archive/master.zip
unzip master.zip
cd recast-control-center-prototype-master/
```

Install control center
```
sudo pip install --process-dependency-links .
```
If this is for a development server you may want to use
```
sudo pip install --process-dependency-links -e .
```
to see you edits in real time.

Finally, run the server
```
python server.py
```

## Special Help For RHEL6
Install python 2.7 out of the box we need to install it. Start with the tools we need to build Python and its modules:

```
yum install gcc gdbm-devel readline-devel ncurses-devel zlib-devel \
            bzip2-devel sqlite-devel db4-devel openssl-devel tk-devel \
            bluez-libs-devel libxslt libxslt-devel libxml2-devel libxml2
````

Download and compile Python 2.7.1:

```
VERSION=2.7.9
mkdir /tmp/src 
cd /tmp/src/
wget http://python.org/ftp/python/$VERSION/Python-$VERSION.tgz
tar xzf Python-$VERSION.tgz
rm Python-$VERSION.tgz
cd Python-$VERSION 
./configure
make
sudo make altinstall
```

Now we need to install Python setuputils:

```
cd /tmp/src
wget http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg
sudo sh setuptools-0.6c11-py2.7.egg
```

Now install pip to install the rest of our dependencies:

```
sudo easy_install-2.7 pip
```

Install RECAST Control Center prerequsites:
```
sudo yum install redis gcc
```

Get the code:
```
wget https://github.com/recast-hep/recast-control-center-prototype/archive/master.zip
unzip master.zip
cd recast-control-center-prototype-master/
```

Install
```
sudo pip-2.7 install --process-dependency-links .
```
If this is for a development server you may want to use
```
sudo pip-2.7 install --process-dependency-links -e .
```
to see you edits in real time.

Run the server
```
python27 server.py
```
