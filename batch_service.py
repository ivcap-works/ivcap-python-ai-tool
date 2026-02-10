import os

from ivcap_service import Service, start_batch_service
from tool_service import is_prime

service = Service(
    name="is-prime-tool",
    version=os.environ.get("VERSION", "???"),
    contact={
        "name": "Max Ott",
        "email": "max.ott@data61.csiro.au",
    },
)

if __name__ == "__main__":
    start_batch_service(service, is_prime)