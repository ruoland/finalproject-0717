from typing import Optional, List
import time
from typing import  Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from database_tables import Schedule
from datetime import datetime, date
from functools import wraps
import logging as logger
from sqlalchemy.exc import SQLAlchemyError
from database_tables import User
from icalendar import Calendar, Event
import pytz
class ScheduleRepository:
    def __init__(self, session: Session, user: User):
        self.session = session
        self.user = user

    def schedule_create(self, subtitle:str, date:datetime, start_time:Optional[datetime] = None, end_time: Optional[datetime] = None, content: Optional[str] = '내용없음', is_alarm=False, tags='', is_loop=False) -> Optional[Schedule]:
        """
        새로운 일정을 생성합니다.

        Args:
            subtitle (str): 일정의 제목
            date (datetime): 일정 날짜
            start_time (Optional[datetime]): 시작 시간
            end_time (Optional[datetime]): 종료 시간
            content (Optional[str]): 일정 내용
            is_alarm (bool): 알람 설정 여부
            tags (str): 태그
            is_loop (bool): 반복 여부

        Returns:
            Schedule: 생성된 일정 객체
        """
        try:
            new_schedule = Schedule(user_id=self.user.id, date=date.date(), is_loop=is_loop, subtitle=subtitle, content=content, alarm_time=None, start_time=start_time, end_time=end_time, is_alarm=is_alarm)
            self.session.add(new_schedule)
            self.session.commit()
            logger.info(f'스케줄 {subtitle}이(가) 추가되었습니다. 날짜: {date}, 시작 시간: {start_time}, 종료 시간: {end_time}')
            return new_schedule
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'스케줄 생성 중 오류 발생: {str(e)}')
            raise

    def schedule_update(self, schedule_id: int, **kwargs) -> bool:
        """
        기존 일정을 업데이트합니다.

        Args:
            schedule_id (int): 업데이트할 일정의 ID
            **kwargs: 업데이트할 필드와 값들
            

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            schedule = self.session.query(Schedule).filter(Schedule.user_id == self.user.id, Schedule.id == schedule_id).first()
            if schedule:
                for key, value in kwargs.items():
                    setattr(schedule, key, value)
                self.session.commit()
                logger.info(f'스케줄 {schedule_id}이(가) 업데이트되었습니다.')
                return True
            logger.warning(f'스케줄 {schedule_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'스케줄 업데이트 중 오류 발생: {str(e)}')
            raise
    
    def schedule_delete(self, schedule_id: int) -> bool:
        """
        일정을 삭제합니다.

        Args:
            schedule_id (int): 삭제할 일정의 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            schedule = self.session.query(Schedule).filter(Schedule.user_id == self.user.id, Schedule.id == schedule_id).first()
            if schedule:
                self.session.delete(schedule)
                self.session.commit()
                logger.info(f'스케줄 {schedule.subtitle}이(가) 삭제되었습니다.')
                return True
            logger.warning(f'스케줄 {schedule_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'스케줄 삭제 중 오류 발생: {str(e)}')
            raise
    
    def get_schedules_with_days(self, date: datetime) -> Optional[List[Schedule]]:
        """
        특정 날짜의 모든 일정을 가져옵니다.

        Args:
            date (datetime): 조회할 날짜

        Returns:
            List[Schedule]: 해당 날짜의 일정 리스트
        """
        try:
            schedules = self.session.query(Schedule).filter(Schedule.user_id == self.user.id, Schedule.date == date).all()
            logger.info(f'{date} 날짜의 일정 {len(schedules)}개를 조회했습니다.')
            return schedules
        except SQLAlchemyError as e:
            logger.error(f'일정 조회 중 오류 발생: {str(e)}')
            raise
    
    def get_schedules_all(self) -> Optional[List[Schedule]]:
        """
        사용자의 모든 일정을 가져옵니다.

        Returns:
            List[Schedule]: 사용자의 모든 일정 리스트
        """
        try:
            schedules = self.session.query(Schedule).filter(Schedule.user_id == self.user.id).all()
            logger.info(f'사용자의 모든 일정 {len(schedules)}개를 조회했습니다.')
            return schedules
        except SQLAlchemyError as e:
            logger.error(f'모든 일정 조회 중 오류 발생: {str(e)}')
            raise
    
    def get_schedule_with_id(self, schedule_id: int) -> Optional[Schedule]:
        """
        특정 ID의 일정을 가져옵니다.

        Args:
            schedule_id (int): 조회할 일정의 ID

        Returns:
            Optional[Schedule]: 조회된 일정 객체 또는 None
        """
        try:
            schedule = self.session.query(Schedule).filter(Schedule.user_id == self.user.id, Schedule.id == schedule_id).first()
            if schedule:
                logger.info(f'일정 ID {schedule_id}을(를) 조회했습니다.')
            else:
                logger.warning(f'일정 ID {schedule_id}을(를) 찾을 수 없습니다.')
            return schedule
        except SQLAlchemyError as e:
            logger.error(f'일정 조회 중 오류 발생: {str(e)}')
            raise

    def get_schedules_by_date_range(self, start_date: datetime, end_date: datetime) -> Optional[List[Schedule]]:
        """        특정 기간 내의 모든 일정을 가져옵니다.

        Args:
            start_date (datetime): 시작 날짜
            end_date (datetime): 종료 날짜

        Returns:
            List[Schedule]: 해당 기간 내의 일정 리스트
        """
        try:
            schedules = self.session.query(Schedule).filter(
                Schedule.user_id == self.user.id,
                Schedule.date.between(start_date, end_date)
            ).all()
            logger.info(f'{start_date}부터 {end_date}까지의 일정 {len(schedules)}개를 조회했습니다.')
            return schedules
        except SQLAlchemyError as e:
            logger.error(f'일정 기간 조회 중 오류 발생: {str(e)}')
            raise
    def _ensure_datetime(self, dt_or_date):
        if isinstance(dt_or_date, date) and not isinstance(dt_or_date, datetime):
            return datetime.combine(dt_or_date, datetime.min.time()).replace(tzinfo=pytz.UTC)
        elif isinstance(dt_or_date, datetime) and dt_or_date.tzinfo is None:
            return dt_or_date.replace(tzinfo=pytz.UTC)
        return dt_or_date

    def import_ics(self, ics_content: str) -> Optional[List[Schedule]]:
        try:
            cal = Calendar.from_ical(ics_content)
            imported_schedules = []

            for component in cal.walk():
                if component.name == "VEVENT":
                    start = self._ensure_datetime(component.get('dtstart').dt)
                    end = self._ensure_datetime(component.get('dtend').dt) if component.get('dtend') else None

                    schedule = Schedule(
                        user_id=self.user.id,
                        date=start,
                        subtitle=str(component.get('summary', '')),
                        content=str(component.get('description', '')),
                        start_time=start,
                        end_time=end,
                        location=str(component.get('location', '')),
                        is_alarm=False,  # 기본값 설정
                        is_loop=False    # 기본값 설정
                    )
                    self.session.add(schedule)
                    imported_schedules.append(schedule)

            self.session.commit()
            logger.info(f'{len(imported_schedules)}개의 일정을 ICS 파일에서 가져왔습니다.')
            return imported_schedules
        except Exception as e:
            self.session.rollback()
            logger.error(f'ICS 파일 가져오기 중 오류 발생: {str(e)}')
            raise  
    def __init__(self, session: Session, user: User):
        self.session = session
        self.user = user


    def export_to_ics(self, schedules: List[Schedule]) -> str:
        """
        주어진 일정 리스트를 ICS 형식으로 변환합니다.

        Args:
            schedules (List[Schedule]): 변환할 일정 리스트

        Returns:
            str: ICS 형식의 문자열
        """
        try:
            cal = Calendar()
            for schedule in schedules:
                event = Event()
                event.add('summary', schedule.subtitle)
                event.add('description', schedule.content)

                # 날짜와 시간 처리
                if schedule.start_time:
                    event.add('dtstart', schedule.start_time)
                    event.add('dtend', schedule.end_time or schedule.start_time)
                else:
                    event.add('dtstart', schedule.date)

                cal.add_component(event)

            logger.info(f'{len(schedules)}개의 일정을 ICS 형식으로 변환했습니다.')
            return cal.to_ical().decode('utf-8')
        except Exception as e:
            logger.error(f'ICS 파일 생성 중 오류 발생: {str(e)}')
            raise