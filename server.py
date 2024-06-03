# encoding: utf-8
import logging
import os

import fastapi.logger
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi_utils.tasks import repeat_every
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse

from helper.LimitUploadSize import LimitUploadSize
from sedrad.SedradMultiClient import SedradMultiClient

fastapi.logger.logger.setLevel(logging.WARNING)

app = FastAPI(
    title="Sedra REST-API server",
    description="This server is to communicate with sedra network via REST-API",
    version=os.getenv("VERSION", "tbd"),
    contact={
        "name": "lAmeR1"
    },
    license_info={
        "name": "MIT LICENSE"
    }
)

app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(LimitUploadSize, max_upload_size=200_000)  # ~1MB

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PingResponse(BaseModel):
    serverVersion: str = "0.12.2"
    isUtxoIndexed: bool = True
    isSynced: bool = True


@app.get("/ping",
         include_in_schema=False,
         response_model=PingResponse)
async def ping_server():
    """
    Ping Pong
    """
    try:
        info = await sedrad_client.sedrads[0].request("getInfoRequest")
        assert info["getInfoResponse"]["isSynced"] is True

        return {
            "server_version": info["getInfoResponse"]["serverVersion"],
            "is_utxo_indexed": info["getInfoResponse"]["isUtxoIndexed"],
            "is_synced": info["getInfoResponse"]["isSynced"]
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Sedrad not connected.")


sedrad_hosts = []

for i in range(100):
    try:
        sedrad_hosts.append(os.environ[f"SEDRAD_HOST_{i + 1}"].strip())
    except KeyError:
        break

if not sedrad_hosts:
    raise Exception('Please set at least SEDRAD_HOST_1 environment variable.')

sedrad_client = SedradMultiClient(sedrad_hosts)


@app.exception_handler(Exception)
async def unicorn_exception_handler(request: Request, exc: Exception):
    await sedrad_client.initialize_all()
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"
                 # "traceback": f"{traceback.format_exception(exc)}"
                 },
    )


@app.on_event("startup")
@repeat_every(seconds=60)
async def periodical_blockdag():
    await sedrad_client.initialize_all()
