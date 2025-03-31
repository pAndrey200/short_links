import datetime
import string
import secrets
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi_cache.decorator import cache
from sqlalchemy.sql import func
from auth.users import current_active_user, current_optional_user
from auth.db import User
from database import get_async_session
from .schemas import LinkCreate, LinkSearchResponse, LinkStats, LinkResponse
from .model import Link
from urllib.parse import urlparse

router = APIRouter(prefix="/links")

def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def normalize_link(url: str) -> str:
    if '://' in url:
        url = url.split('://', 1)[1]
    if url.startswith('www.'):
        url = url[4:]
    if url.endswith('/'):
        url = url.rstrip('/')
    return url

@router.post("/shorten", response_model=LinkResponse)
async def create_short_link(
    link: LinkCreate,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_optional_user)
):
    if link.custom_alias:
        existing = await db.execute(select(Link).where(Link.custom_alias == link.custom_alias ))
        if existing.scalar():
            raise HTTPException(status_code=400, detail="Alias already exists")
        short_code = link.custom_alias
    else:
        short_code = generate_short_code()
        existing = await db.execute(select(Link).where(Link.short_code == short_code))
        while existing.scalar():
            short_code = generate_short_code()
            existing = await db.execute(select(Link).where(Link.short_code == short_code))

    db_link = Link(
        short_code=short_code,
        original_url=normalize_link(link.original_url),
        user_id=user.id if user else None,
        expires_at=link.expires_at,
        custom_alias=short_code,
        last_clicked_at = func.now()
    )
    
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    
    
    return db_link

@router.get("/search", response_model=List[LinkSearchResponse])
async def search_links(
    original_url: str = Query(..., description="Original URL to search"),  # Изменено с HttpUrl на str
    db: AsyncSession = Depends(get_async_session)
):
    # Нормализуем URL для сравнения

    result = await db.execute(
        select(Link).where(
            Link.original_url == normalize_link(original_url),
            Link.is_active == True,
            (Link.expires_at > func.now()) | (Link.expires_at == None)
        )
    )
    
    links = result.scalars().all()
    
    if not links:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No links found for this URL"
        )
    
    return links

@router.get("/{short_code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
@cache()
async def redirect_link(short_code: str, db: AsyncSession = Depends(get_async_session)):

    result = await db.execute(
        select(Link).where(
            Link.short_code == short_code,
            Link.is_active == True,
            (Link.expires_at > func.now()) | (Link.expires_at == None)
    ))
    link = result.scalar()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.clicks += 1
    link.last_clicked_at = func.now()
    await db.commit()

    return RedirectResponse(url=(f'https://{link.original_url}'))


@router.get("/{short_code}/stats", response_model=LinkStats)
@cache()
async def get_link_stats(short_code: str, db: AsyncSession = Depends(get_async_session)):
    result = await db.execute(
        select(Link).where(
            Link.short_code == short_code,
            Link.is_active == True
        )
    )
    link = result.scalar()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    return {
        "original_url": link.original_url,
        "created_at": link.created_at,
        "clicks": link.clicks,
        "last_clicked_at": link.last_clicked_at,
        "expires_at": link.expires_at
    }

@router.put("/{short_code}", response_model=LinkResponse)
async def update_link(
    short_code: str,
    new_url: HttpUrl,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    result = await db.execute(
        select(Link).where(
            Link.short_code == short_code,
            Link.user_id == user.id
        )
    )
    link = result.scalar()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    link.original_url = normalize_link(str(new_url))
    await db.commit()
    return link

@router.delete("/{short_code}")
async def delete_link(
    short_code: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    result = await db.execute(
        select(Link).where(
            Link.short_code == short_code,
            Link.user_id == user.id
        )
    )
    link = result.scalar()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    link.is_active = False
    link.expires_at = func.now() + datetime.timedelta(hours=6)
    await db.commit()
    return {"status": "success", "message": "Link deleted"}

