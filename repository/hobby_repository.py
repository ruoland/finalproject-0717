from typing import Optional, List
import time
from sqlalchemy import func
from sqlalchemy.orm import Session
from database_tables import User,Hobby
from datetime import datetime, time
from functools import wraps
import logging as logger
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database_tables import Base, User
from datetime import time, datetime
from typing import Union
class HobbyRepository():
    def __init__(self, session: Session, user: User):
        self.session = session
        self.user = user

    def hobby_create(self, name:str, time_start: Optional[time] = None, time_end: Optional[time] = None, count: Optional[int] = 0, play_time: Optional[float] = 0, last_done_date: Optional[datetime] = None) -> Union[time, None]:
        """
        새로운 취미를 생성합니다.

        Args:
            name (str): 취미 이름
            time_start (float): 선호 시작 시간
            time_end (float): 선호 종료 시간
            count (Optional[int]): 실행 횟수
            play_time (Optional[float]): 총 실행 시간
            last_done_date (Optional[datetime]): 마지막 실행 날짜

        Returns:
            Hobby: 생성된 취미 객체
        """
        
        if time_start and time_end:
            if time_start > time_end:
                logger.error('취미 선호 시작 시간이 끝나는 시간보다 빠릅니다!')
                return None
        try:
            new_hobby = Hobby(user_id=self.user.id, name=name, preferred_time_start=time_start, preferred_time_end=time_end, last_done_date=last_done_date, play_time=play_time, count=count)
            self.session.add(new_hobby)
            self.session.commit()
            logger.info(f'새로운 취미 "{name}"이(가) 생성되었습니다.')
            return new_hobby
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'취미 생성 중 오류 발생: {str(e)}')
            raise
        
    def get_user_hobbies(self) -> Optional[List[Hobby]]:
        """
        사용자의 모든 취미를 가져옵니다.

        Returns:
            List[Hobby]: 사용자의 모든 취미 리스트
        """
        try:
            hobbies = self.session.query(Hobby).filter_by(user_id=self.user.id).all()
            logger.info(f'사용자의 모든 취미 {len(hobbies)}개를 조회했습니다.')
            return hobbies
        except SQLAlchemyError as e:
            logger.error(f'취미 조회 중 오류 발생: {str(e)}')
            raise

    def hobby_update(self, hobby_id: int, **kwargs) -> bool:
        """
        취미 정보를 업데이트합니다.

        Args:
            hobby_id (int): 업데이트할 취미의 ID
            **kwargs: 업데이트할 필드와 값들

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            hobby = self.session.query(Hobby).filter(Hobby.user_id == self.user.id, Hobby.id == hobby_id).first()
            if hobby:
                for key, value in kwargs.items():
                    setattr(hobby, key, value)
                self.session.commit()
                logger.info(f'취미 ID {hobby_id}의 정보가 업데이트되었습니다.')
                return True
            logger.warning(f'취미 ID {hobby_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'취미 업데이트 중 오류 발생: {str(e)}')
            raise

    def hobby_delete(self, hobby_id: int) -> bool: 
        """
        취미를 삭제합니다.

        Args:
            hobby_id (int): 삭제할 취미의 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            hobby = self.session.query(Hobby).filter(Hobby.user_id == self.user.id, Hobby.id == hobby_id).first()
            if hobby:
                self.session.delete(hobby)
                self.session.commit()
                logger.info(f'취미 "{hobby.name}"(ID: {hobby_id})이(가) 삭제되었습니다.')
                return True
            logger.warning(f'취미 ID {hobby_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'취미 삭제 중 오류 발생: {str(e)}')
            raise

    def get_hobby_with_id(self, hobby_id: int) -> Optional[Hobby]:
        """
        특정 ID의 취미를 가져옵니다.

        Args:
            hobby_id (int): 조회할 취미의 ID

        Returns:
            Optional[Hobby]: 조회된 취미 객체 또는 None
        """
        try:
            hobby = self.session.query(Hobby).filter(Hobby.user_id == self.user.id, Hobby.id == hobby_id).first()
            if hobby:
                logger.info(f'취미 ID {hobby_id}을(를) 조회했습니다.')
            else:
                logger.warning(f'취미 ID {hobby_id}을(를) 찾을 수 없습니다.')
            return hobby
        except SQLAlchemyError as e:
            logger.error(f'취미 조회 중 오류 발생: {str(e)}')
            raise

    def get_hobbies_by_preferred_time(self, time: time) -> Optional[List[Hobby]]:
        """
        특정 시간에 선호되는 취미들을 가져옵니다.

        Args:
            time (float): 조회할 시간

        Returns:
            List[Hobby]: 해당 시간에 선호되는 취미 리스트
        """
        try:
            hobbies = self.session.query(Hobby).filter(
                Hobby.user_id == self.user.id,
                Hobby.preferred_time_start <= time,
                Hobby.preferred_time_end >= time
            ).all()
            logger.info(f'시간 {time}에 선호되는 취미 {len(hobbies)}개를 조회했습니다.')
            return hobbies
        except SQLAlchemyError as e:
            logger.error(f'선호 시간별 취미 조회 중 오류 발생: {str(e)}')
            raise

    def update_hobby_stats(self, hobby_id: int, play_time: float) -> bool:
        """
        취미 통계를 업데이트합니다.

        Args:
            hobby_id (int): 업데이트할 취미의 ID
            play_time (float): 추가할 실행 시간

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            hobby = self.session.query(Hobby).filter(Hobby.user_id == self.user.id, Hobby.id == hobby_id).first()
            if hobby:
                hobby.count += 1
                hobby.play_time += play_time
                hobby.last_done_date = datetime.now()
                self.session.commit()
                logger.info(f'취미 "{hobby.name}"의 통계가 업데이트되었습니다. 총 실행 횟수: {hobby.count}, 총 실행 시간: {hobby.play_time}')
                return True
            logger.warning(f'취미 ID {hobby_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'취미 통계 업데이트 중 오류 발생: {str(e)}')
            raise