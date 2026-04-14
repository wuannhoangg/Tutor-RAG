from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


class FolderRepository:
    async def create(self, *, user_id: str, name: str, is_system: bool = False, db: AsyncSession) -> models.Folder:
        folder = models.Folder(
            folder_id=uuid4().hex,
            user_id=user_id,
            name=name.strip(),
            is_system="true" if is_system else "false",
            created_at=datetime.utcnow(),
        )
        try:
            db.add(folder)
            await db.commit()
            await db.refresh(folder)
            return folder
        except Exception:
            await db.rollback()
            raise

    async def list_by_user(self, user_id: str, db: AsyncSession):
        result = await db.execute(
            select(models.Folder)
            .where(models.Folder.user_id == user_id)
            .order_by(models.Folder.created_at.asc())
        )
        return result.scalars().all()

    async def get_by_id(self, folder_id: str, db: AsyncSession) -> Optional[models.Folder]:
        result = await db.execute(select(models.Folder).where(models.Folder.folder_id == folder_id))
        return result.scalars().first()

    async def get_by_name_for_user(self, user_id: str, name: str, db: AsyncSession) -> Optional[models.Folder]:
        result = await db.execute(
            select(models.Folder).where(
                models.Folder.user_id == user_id,
                models.Folder.name == name.strip(),
            )
        )
        return result.scalars().first()

    async def get_or_create_system_folder(self, *, user_id: str, name: str, db: AsyncSession) -> models.Folder:
        existing = await self.get_by_name_for_user(user_id, name, db)
        if existing:
            return existing
        return await self.create(user_id=user_id, name=name, is_system=True, db=db)
