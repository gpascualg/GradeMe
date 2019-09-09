# Before starting


## Github Organization

You need to create a Github Organization: https://github.com/account/organizations/new

So far you need nothing but the organization name. Further steps while require additional data.

## Github user

You need a **master** user, which is recommended not to be you main Github user, as you will need to provide an API Key with advanced permissions.

Create a new user on Github and then create an API Key with at least *push, clone*, including private repos, rights from: https://github.com/settings/tokens

**Take not from that key, it will only show once**.

Now, add this user to the organization you just created. That can be done from: https://github.com/orgs/YOUR-ORG/people, where "YOUR_ORG" is the name of the organization you created before.

# Common steps

Create the user-password combinations for the rabbit queues
```bash
printf <user> | docker secret create rabbit-user
printf <pass> | docker secret create rabbit-pass
```

# Running locally:

## What you need

* Python 3.x
* Docker (for mongo)

## How

Install required Python libraries
```bash
pip install -r servers/webhooks/requirements.txt
pip install -r servers/frontend/requirements.txt
```

Create docker networks for test execution
```bash
docker network create --driver bridge backend
docker network create --internal results
```

Fire up mongo on Docker (**note** change /tmp/data if you want permanent storage)
```bash
docker run --name mongo -p 27017:27017 -v /tmp/data:/data/db --rm --network backend -d mongo
```

Build now (and everytime you change agents), build the dockers (you might need `sudo`)
```bash
./build.sh
```

Start the webhooks/tests server with

```bash
python start_service.py --github-api-key=<YOUR API KEY> --github-org=<YOUR ORGANIZATION NAME> --broadcast-secret=<SOME RANDOM LETTERS> --mongo-host=localhost
```

For example:

```bash
python start_service.py --port 8080 --github-org-id 123 --no-github-init --github-api-key=231af25d0 --github-org=TNUI-UB --broadcast-secret=qwead123 --mongo-host=localhost
```

Processing tests synchronously instead of in a processes pool can be achieved by setting the environment variable `DISABLE_POOL` to 1, for example:

```bash
DISABLE_POOL=1 python start_service.py --github-api-key=231af25d0 --github-org=TNUI-UB --broadcast-secret=qwead123 --mongo-host=localhost
```

This proves to be useful when debugging `Job`s or blocking for tests completion.

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

# Creating tests

Each organization must have its own docker volume for the data. Suppose your organization name is "TNUI-UB" and your tests to be executed are "tests-assignment-2018". The following is to be done:

```bash
docker run -ti --rm --mount source=TNUI-UB-tests-assignment-2018,target=/tests alpine/git clone <TESTS_GIT_URL> /tests/_
```

Notice how the `source` argument is composed of `<ORGANIZATION>-<TESTS>`.
