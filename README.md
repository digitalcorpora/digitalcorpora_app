[![codecov](https://codecov.io/gh/digitalcorpora/digitalcorpora_app/branch/main/graph/badge.svg?token=E6GE1KIGAT)](https://codecov.io/gh/digitalcorpora/digitalcorpora_app)

# digitalcorpora.org python app
This repo provides the custom-written Python code to for the https://DigitalCorpora.org/ website.

The website runs with WordPress. This repo runs in a sub-domain https://downloads.digitalcorproa.org/ provides the browsing functionality of the S3 bucket.  Our development website is https://dev.digitalcorpora.org/

The repo is designed to be check out as ~/downloads.digitalcorpora.org/ on a Dreamhost user account. It runs the python application in Bottle using the Dreamhost Passenger WSGI framework. The repo can also be checked out into other domain directories for development and testing. You can also modify the config file to browse other S3 buckets, should you wish to use this on another website.
