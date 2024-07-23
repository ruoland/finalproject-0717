
from typing import Optional
from sqlalchemy.orm import Session
from database_tables import Holiday
from datetime import datetime, timedelta

class HolidayRepository:
    def add_holiday(self, session: Session, date, name, is_public_holiday=True) -> Optional[Holiday]:
        holiday = Holiday(date=date, name=name, is_public_holiday= is_public_holiday)
        session.add(holiday)
        session.commit()
        return holiday
        
    def get_holidays_for_month(self, session: Session, year, month) -> Optional[list[Holiday]]:
        start_date = datetime(year, month, 1)
        end_date = start_date + timedelta(days=32)
        end_date = end_date.replace(day=1) - timedelta(days=1)
        
        return session.query(Holiday).filter(
            Holiday.date.between(start_date, end_date)
        ).all()