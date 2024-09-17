# IVCAP "AI Tool" Demo

This repo template contains an implementation of a
basic _AI Agent Tool_ usable for various agent frameworks
like [crewAI](https://www.crewai.com).

The actual tool implemented in ths repo provides a _web search_
capability by in turn, calling the public API provided by
[DuckDuckGo](https://duckduck.go.com) search engine

* [Use](#use)
* [Test](#test)
* [Build & Deploy](#build)
* [Implementation](#implementation)

## Use <a name="test"></a>

Below is an example of an agent definition which uses this tool:
```
  ...
  "agents": {
    "researcher": {
      "role": "Senior Research Analyst",
      "goal": "Uncover cutting-edge developments in AI and data science",
      "backstory": "You work at a leading tech think tank. Your expertise lies in identifying emerging trends. ...",
      "tools": [
        {
          "id": "urn:ivcap:service:ai-tool.ddg-search",
          "safesearch": "off"
        }
      ],
      ...
```

## Test <a name="test"></a>

In order to quickly test this service, follow these steps:

* `pip install -r requirements.txt`
* `make run`

In a separate terminal, call the service via `curl` or your favorite http testing tool
```
% curl -X 'POST' -H 'Content-Type: application/json' http://localhost:8080 \
    -d '{"action": {"query": "ai tool"}, "service": {}}'

{"query":"ai tool","result":"[snippet: If your company hasn't already adopted artificial intelligence, here are some of the top tools you can choose from., title: The 43 Best AI Tools to Know | Built In, link: https://builtin.com/artificial-intel....
```

A more "web friendly" way is to open [http://localhost:8080/api](http://localhost:8080/api)

## Build & Deploy <a name="build"></a>

The tool needs to be packed into a docker container, and the, together with an IVCAP service description
deployed to an IVCAP platform.

> **Important**: If you adopt this repo template, please make sure to first change the first two variables
`SERVICE_NAME` and `SERVICE_TITLE` at the top of the [Makefile](./Makefile).


> **Note:** Please make sure to have the IVCAP cli tool installed and configured. See the
[ivcap-cli](https://github.com/ivcap-works/ivcap-cli) repo for more details.

The following [Makefile](./Makefile) targets have been provided

* `make docker-build`: Build the docker container
* `make service-register`: Published the container as well as registers the service

## Implementation <a name="implementation"></a>

This service is implemented in [tool.py](./tool.py) using [fastAPI](https://fastapi.tiangolo.com/).

It provides the following API endpoints:

* `GET /`: Returning the tool description
* `POST /`: Requesting the tool to perform an action
* `GET /_healtz`: A "health" endpoint need for operational purposes

In addition:

* `GET /api` and `GET /openapi.json`: Automatically provided by [fastAPI](https://fastapi.tiangolo.com/).

### Service structure

AN AI tool is expected to return a tool description via `GET /` containing two parts:

* `action`: Defining the schema for the action an agent is requesting.
* `service`: Defining the schema for the various configuration options the tool may provide

For this tool, the action schema is simply the query string:
```
class ActionProps(BaseModel):
    query: str = Field(description="search query to look up")
```

while the service schema more closely reflects the service internals, which in this case are:
```
class ServiceProps(BaseModel):
    region: str = Field(description="'wt-wt' the world", default="wt-wt")
    safesearch: SafeSearchE = SafeSearchE.moderate
    timelimit: TimeLimitE = TimeLimitE.y
    max_results: int = 5
    source: SourceE = SourceE.text
```

Finally, an AI tool is expected to return the result of the requested action as string (possibly with some internally structure) in the `result` property of the reply. It may provide additional information, such as the part of the request, for debugging purposes.

```
class Response(BaseModel):
    result: str
    ...
```

### `tools.py`

The code in [lambda.py](tools.py) falls into the following parts:

#### Import packages

```
from enum import Enum
from fastapi import FastAPI, HTTPException
from signal import signal, SIGTERM
import sys
import os
from pydantic import BaseModel, Field

from duckduckgo_search import DDGS
```

#### Setting up a graceful shutdown for kubernetes deployments

```
signal(SIGTERM, lambda _1, _2: sys.exit(0))
```

#### Service description and general `fastAPI` setup

```
description = """
A wrapper around DuckDuckGo Search.
Useful for when you need to answer questions about current events.
Input should be a search query.
"""

app = FastAPI(
    title="AI tool to retrieve infomation via DuckDuckGo Search",
    description=description,
    ...
```

#### Defining the service's data model

```
class StrEnum(str, Enum):
    def __repr__(self) -> str:
        return str.__repr__(self.value)

class SafeSearchE(StrEnum):
    on = "on"
    moderate = "moderate"
    off = "off"

...

class Props(BaseModel):
    action: ActionProps
    service: ServiceProps

class Response(BaseModel):
    query: str
    result: str
```

#### The service description

```
@app.get("/")
def info():
    return {
        "$schema": "urn:sd.platform:schema:ai-tool.1",
        "name": "duckduckgo_search",
        "description": description,
        "action_schema":  ActionProps.model_json_schema(by_alias=False),
        "service_schema": ServiceProps.model_json_schema(),
    }
```

#### The service implementation itself

```
@app.post("/")
def query(req: Props) -> Response:
    """Returns the search results as a serialised list with the following keys:
        snippet - The description of the result.
        title - The title of the result.
        link - The link to the result.
    ...
```

#### And finally, the _Health_ indicator needed by Kubernetes

```
@app.get("/_healtz")
def healtz():
    return {"version": os.environ.get("VERSION", "???")}
```

To test the service, first run `make install` (ideally within a `venv` or `conda` environment) beforehand to install the necessary dependencies. Then `make run` will start the service listing on [http://0.0.0.0:8080](http://0.0.0.0:8080).

### [service.json](./service.json)

This file describes the service as needed for the `ivcap service create ...` command.

> The format is still in flux and we most likely going to reference
the approprite section in the [IVCAP Docs](https://ivcap-works.github.io/ivcap-docs/).

### [Dockerfile](./Dockerfile)

This file describes a simple configuration for building a docker image for
this service. The make target `make docker-build` will build the image, and
the `make docker-publish` target will upload it to IVCAP.
