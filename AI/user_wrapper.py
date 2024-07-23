from sqlalchemy import func
from database_tables import User
from functools import wraps
from sqlalchemy.exc import NoResultFound
import logging as logger
logger.basicConfig(level=logger.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logger.getLogger(__name__)

def user_required(f):
    def get_user_with_id(self, user_id: int):
        return self.session.query(User).filter(User.id == user_id).one_or_none()
    @wraps(f)
    def wrapper(self, user:User, *args, **kwargs):
        try:
            print(user)
            user = get_user_with_id(self, user.id)
            return f(self, user, *args, **kwargs)
        except NoResultFound:
            logger.warning(f'존재하지 않는 유저입니다. (ID: {user.id})')
            return None
    return wrapper

