from datetime import datetime
from typing import Optional

from app.database.models.user import User


class UserRepository:
    async def get_by_id(self, user_id: str) -> Optional[User]:
        return await User.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await User.find_one(User.email == email)

    async def create(self, user: User) -> User:
        return await user.insert()

    async def update(self, user: User) -> User:
        user.updated_at = datetime.utcnow()
        return await user.save()

    async def delete(self, user_id: str) -> bool:
        user = await User.get(user_id)
        if user:
            await user.delete()
            return True
        return False

    async def list_users(
        self, skip: int = 0, limit: int = 50
    ) -> list[User]:
        return await User.find_all().skip(skip).limit(limit).to_list()

    async def count_users(self) -> int:
        return await User.count()

    async def count_active_users(self) -> int:
        return await User.find(User.is_active == True).count()
