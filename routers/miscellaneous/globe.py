from typing import List, Dict
from pydantic import TypeAdapter
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from modules.misc.glob import retrieve_countries, retrieve_single_country, retrieve_currencies, retrieve_single_currency
from database.schema import ErrorResponse, PlainResponse, CountryModel, CountryResponseModel, CurrencyModel, CurrencyResponseModel
from database.db import get_db
from sqlalchemy.orm import Session
from fastapi_pagination import LimitOffsetPage, Page

router = APIRouter(
    prefix="/global",
    tags=["global"]
)

@router.get("/countries", response_model=Page[CountryModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def countries_get_all(request: Request, db: Session = Depends(get_db), name: str = Query(None), status: int = Query(None)):
    filters = {}
    if name:
        filters['name'] = name
    if status:
        filters['status'] = status
    return retrieve_countries(db=db, filters=filters)

@router.get("/countries/get_single/{country_id}", response_model=CountryResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def countries_get_single(request: Request, db: Session = Depends(get_db), country_id: int = 0):
    return retrieve_single_country(db=db, id=country_id)

@router.get("/currencies", response_model=Page[CurrencyModel], responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def currencies_get_all(request: Request, db: Session = Depends(get_db), name: str = Query(None), status: int = Query(None)):
    filters = {}
    if name:
        filters['name'] = name
    if status:
        filters['status'] = status
    return retrieve_currencies(db=db, filters=filters)

@router.get("/currencies/get_single/{currency_id}", response_model=CurrencyResponseModel, responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}})
async def currencies_get_single(request: Request, db: Session = Depends(get_db), currency_id: int = 0):
    return retrieve_single_currency(db=db, id=currency_id)
