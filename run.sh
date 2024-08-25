#!/bin/sh
echo "INFO     AI tool to retrieve infomation via DuckDuckGo Search - $VERSION"
fastapi run tool.py --proxy-headers --port 8080