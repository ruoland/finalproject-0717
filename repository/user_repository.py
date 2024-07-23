
from typing import TypeVar
from sqlalchemy.orm import Session
from database_tables import User
from database_tables import Holiday
import logging
from .check_repository import CheckListRepository
from .diary_repository import DiaryRepository
from .hobby_repository import HobbyRepository
from .holiday_repository import HolidayRepository
from .schedule_repository import ScheduleRepository
from sqlalchemy.orm import Session

# 기본 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

T = TypeVar('T')

    
class UserRepository():
    def __init__(self, session: Session, user :User):
        self.diary_repo = DiaryRepository(user=user, session=session)
        self.schedule_repo = ScheduleRepository(user=user, session=session)
        self.checklist_repo = CheckListRepository(user=user, session=session)
        self.hobby_repo = HobbyRepository(user=user, session=session)
        self.holiday_repo = HobbyRepository(user=user, session=session)
        
