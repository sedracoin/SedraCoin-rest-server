# encoding: utf-8

from typing import List

from fastapi import Path, HTTPException
from pydantic import BaseModel

from server import app, sedrad_client


class OutpointModel(BaseModel):
    transactionId: str = "ef62efbc2825d3ef9ec1cf9b80506876ac077b64b11a39c8ef5e028415444dc9"
    index: int = 0


class ScriptPublicKeyModel(BaseModel):
    scriptPublicKey: str = "20c5629ce85f6618cd3ed1ac1c99dc6d3064ed244013555c51385d9efab0d0072fac"


class UtxoModel(BaseModel):
    amount: str = "11501593788",
    scriptPublicKey: ScriptPublicKeyModel
    blockDaaScore: str = "18867232"


class UtxoResponse(BaseModel):
    address: str = "sedra:qrzk988gtanp3nf76xkpexwud5cxfmfygqf42hz38pwea74s6qrj75jee85nj"
    outpoint: OutpointModel
    utxoEntry: UtxoModel


@app.get("/addresses/{sedraAddress}/utxos", response_model=List[UtxoResponse], tags=["Sedra addresses"])
async def get_utxos_for_address(sedraAddress: str = Path(
    description="Sedra address as string e.g. sedra:qqkqkzjvr7zwxxmjxjkmxxdwju9kjs6e9u82uh59z07vgaks6gg62v8707g73",
    regex="^sedra\:[a-z0-9]{61,63}$")):
    """
    Lists all open utxo for a given sedra address
    """
    resp = await sedrad_client.request("getUtxosByAddressesRequest",
                                       params={
                                           "addresses": [sedraAddress]
                                       }, timeout=120)
    try:
        return (utxo for utxo in resp["getUtxosByAddressesResponse"]["entries"] if utxo["address"] == sedraAddress)
    except KeyError:
        if "getUtxosByAddressesResponse" in resp and "error" in resp["getUtxosByAddressesResponse"]:
            raise HTTPException(status_code=400, detail=resp["getUtxosByAddressesResponse"]["error"])
        else:
            return []
