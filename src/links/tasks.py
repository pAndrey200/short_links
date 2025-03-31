from datetime import datetime, timedelta
import pytz
from sqlalchemy import  delete
from database import  async_session_maker
from .model import Link
import asyncio
from config import settings

async def delete_expired_links():
    while True:
        session = None
        try:
            session = async_session_maker()
            
            stmt = delete(Link).where(
                Link.expires_at < datetime.now(tz=pytz.timezone('Europe/Moscow')),
                Link.is_active == True
            )
            await session.execute(stmt)
            await session.commit()
            
            print(f"Deleted expired links at {datetime.now(tz=pytz.timezone('Europe/Moscow'))}")

        except Exception as e:
            print(f"Error deleting expired links: {e}")
            if session:
                await session.rollback()
        finally:
            if session:
                await session.close()
        
        await asyncio.sleep(600)

async def delete_unused_links():
    while True:
        session = None
        try:
            session = async_session_maker()
            cutoff_date = datetime.now(tz=pytz.timezone('Europe/Moscow')) - timedelta(days=settings.UNUSED_LINKS_TTL_DAYS)

            stmt = delete(Link).where(
                Link.last_clicked_at < cutoff_date,
                Link.is_active == True
            )
            
            await session.execute(stmt)
            await session.commit()

            print(f"Cleaned up unused links at {datetime.now(tz=pytz.timezone('Europe/Moscow'))}")

        except Exception as e:
            print(f"Cleanup error: {str(e)}")
            if session:
                await session.rollback()
        finally:
            if session:
                await session.close()

        await asyncio.sleep(600) 