from enum import Enum
from fastapi import FastAPI, HTTPException
from signal import signal, SIGTERM
import sys
import os
from pydantic import BaseModel, Field

from duckduckgo_search import DDGS


# shutdown pod cracefully
signal(SIGTERM, lambda _1, _2: sys.exit(0))

description = """
A wrapper around DuckDuckGo Search.
Useful for when you need to answer questions about current events.
Input should be a search query.
"""

app = FastAPI(
    title="AI tool to retrieve infomation via DuckDuckGo Search",
    description=description,
    version=os.environ.get("VERSION", "???"),
    contact={
        "name": "Max Ott",
        "email": "max.ott@data61.csiro.au",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/license/MIT",
    },
    docs_url="/api",
    root_path=os.environ.get("IVCAP_ROOT_PATH", "")
)

class StrEnum(str, Enum):
    def __repr__(self) -> str:
        return str.__repr__(self.value)

class SafeSearchE(StrEnum):
    on = "on"
    moderate = "moderate"
    off = "off"

class TimeLimitE(StrEnum):
    d = "d"
    w = "w"
    m = "m"
    y = "y"

class SourceE(StrEnum):
    text = "text"
    news = "news"

class ServiceProps(BaseModel):
    region: str = Field(description="'wt-wt' the world", default="wt-wt")
    safesearch: SafeSearchE = SafeSearchE.moderate
    timelimit: TimeLimitE = TimeLimitE.y
    max_results: int = 5
    source: SourceE = SourceE.text

class ActionProps(BaseModel):
    query: str = Field(description="search query to look up")

class Props(BaseModel):
    action: ActionProps
    service: ServiceProps

class Response(BaseModel):
    query: str
    result: str

@app.get("/")
def info():
    return {
        "$schema": "urn:sd.platform:schema:ai-tool.1",
        "name": "duckduckgo_search",
        "description": description,
        "action_schema":  ActionProps.model_json_schema(by_alias=False),
        "service_schema": ServiceProps.model_json_schema(),
    }

@app.post("/")
def query(req: Props) -> Response:
    """Returns the search results as a serialised list with the following keys:
        snippet - The description of the result.
        title - The title of the result.
        link - The link to the result.

    Args:
        req (Props): defining the query as well as properties of the search function

    Raises:
        501 Not Implemented: If a source is not implemented

    Returns:
        a Response object
    """
    query = req.action.query
    sargs = req.service.model_dump()
    source = sargs.pop('source', None)
    if source == SourceE.text:
        ra = DDGS().text(keywords=query, **sargs)
        # pprint(ra)
        ra2 = [
            {"snippet": r["body"], "title": r["title"], "link": r["href"]}
            for r in ra
        ]
        ra3 = [", ".join([f"{k}: {v}" for k, v in d.items()]) for d in ra2]
        result = ", ".join([f"[{rs}]" for rs in ra3])
        return Response(query=query, result=result)
    else:
        raise HTTPException(status_code=501, detail=f"source '{source.value}' not implemented")

# Allows platform to check if everything is OK
@app.get("/_healtz")
def healtz():
    return {"version": os.environ.get("VERSION", "???")}
