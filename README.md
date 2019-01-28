# Before starting


## Github Organization

You need to create a Github Organization: https://github.com/account/organizations/new

So far you need nothing but the organization name. Further steps while require additional data.

## Github user

You need a **master** user, which is recommended not to be you main Github user, as you will need to provide an API Key with advanced permissions.

Create a new user on Github and then create an API Key with at least *push, clone*, including private repos, rights from: https://github.com/settings/tokens

**Take not from that key, it will only show once**.

Now, add this user to the organization you just created. That can be done from: https://github.com/orgs/YOUR-ORG/people, where "YOUR_ORG" is the name of the organization you created before.

# Running locally:

## What you need

* Python 3.x
* MongoDB

## How

Once you have mongo running (`mongod`), install all dependencies

```bash
pip install -r requirements.txt
```

Start the webhooks/tests server with

```bash
python start_service.py --github-api-key=<YOUR API KEY> --github-org=<YOUR ORGANIZATION NAME> --broadcast-secret=<SOME RANDOM LETTERS> --mongo-host=localhost
```

For example:

```bash
python start_service.py --github-api-key=231af25d0 --github-org=TNUI-UB --broadcast-secret=qwead123 --mongo-host=localhost
```

# Running with docker

## What you need

* Docker
* Docker-compose

## How

First (and everytime you change something, ie. code), build the dockers (you might need `sudo`)

```bash
./build.sh
```

First time only, copy the file `docker-compose.yml.template` to `docker-compose.yml` and make sure to replace all `<XXXX>` values inside for its corresponding values.

Once it's ready, run it:
```bash
./run.sh
```
