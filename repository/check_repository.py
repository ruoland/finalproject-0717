
from sqlalchemy import create_engine
from database_tables import Base, User
from datetime import datetime
from typing import Optional, List
from sqlalchemy import func
from sqlalchemy.orm import Session
from database_tables import Checklist, User
from datetime import datetime
from functools import wraps
import logging as logger
from sqlalchemy.exc import SQLAlchemyError
class CheckListRepository:
    def __init__(self, session: Session, user: User):
        self.session = session
        self.user = user
        
    def checklist_create(self, content:str, deadline:datetime) -> Optional[Checklist]:
        """
        새로운 체크리스트 항목을 생성합니다.

        Args:
            content (str): 체크리스트 항목의 내용
            deadline (datetime): 마감 기한

        Returns:
            Checklist: 생성된 체크리스트 항목 객체
        """
        try:
            new_checklist = Checklist(user_id=self.user.id, content=content, deadline=deadline, write_date=func.now(), is_complete=False, divisible=False)
            self.session.add(new_checklist)
            self.session.commit()
            logger.info(f'새로운 체크리스트 항목이 생성되었습니다. 내용: {content}, 마감기한: {deadline}')
            return new_checklist
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'체크리스트 항목 생성 중 오류 발생: {str(e)}')
            raise

    def checklist_update(self, checklist_id: int, **kwargs) -> bool:
        """
        체크리스트 항목을 업데이트합니다.

        Args:
            checklist_id (int): 업데이트할 체크리스트 항목의 ID
            **kwargs: 업데이트할 필드와 값들

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            checklist = self.session.query(Checklist).filter(Checklist.user_id == self.user.id, Checklist.id == checklist_id).first()
            if checklist:
                for key, value in kwargs.items():
                    setattr(checklist, key, value)
                self.session.commit()
                logger.info(f'체크리스트 항목 {checklist_id}이(가) 업데이트되었습니다.')
                return True
            logger.warning(f'체크리스트 항목 {checklist_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'체크리스트 항목 업데이트 중 오류 발생: {str(e)}')
            raise
    def checklist_complete_done(self, checklist_id:int, is_complete:bool) -> bool:
        """
        체크리스트 항목의 완료 상태를 변경합니다.

        Args:
            checklist_id (int): 상태를 변경할 체크리스트 항목의 ID
            is_complete (bool): 완료 여부

        Returns:
            bool: 상태 변경 성공 여부
        """
        try:
            checklist = self.session.query(Checklist).filter(Checklist.user_id == self.user.id, Checklist.id == checklist_id).first()    
            if checklist:
                checklist.is_complete = is_complete
                self.session.commit()
                logger.info(f'체크리스트 항목 {checklist_id}의 완료 상태가 {is_complete}로 변경되었습니다.')
                return True
            logger.warning(f'체크리스트 항목 {checklist_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'체크리스트 항목 상태 변경 중 오류 발생: {str(e)}')
            raise
     
    def get_user_checklists(self) -> Optional[List[Checklist]]:
        """
        사용자의 모든 체크리스트 항목을 가져옵니다.

        Returns:
            List[Checklist]: 사용자의 모든 체크리스트 항목 리스트
        """
        try:
            checklists = self.session.query(Checklist).filter_by(user_id=self.user.id).all()
            logger.info(f'사용자의 모든 체크리스트 항목 {len(checklists)}개를 조회했습니다.')
            return checklists
        except SQLAlchemyError as e:
            logger.error(f'체크리스트 항목 조회 중 오류 발생: {str(e)}')
            raise
        
    def checklist_delete(self, checklist_id: int) -> bool:
        """
        체크리스트 항목을 삭제합니다.

        Args:
            checklist_id (int): 삭제할 체크리스트 항목의 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            checklist = self.session.query(Checklist).filter(Checklist.user_id == self.user.id, Checklist.id == checklist_id).first()
            if checklist:
                self.session.delete(checklist)
                self.session.commit()
                logger.info(f'체크리스트 항목 {checklist_id}이(가) 삭제되었습니다.')
                return True
            logger.warning(f'체크리스트 항목 {checklist_id}을(를) 찾을 수 없습니다.')
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f'체크리스트 항목 삭제 중 오류 발생: {str(e)}')
            raise

    def get_checklist_with_id(self, checklist_id: int) -> Optional[Checklist]:
        """
        특정 ID의 체크리스트 항목을 가져옵니다.

        Args:
            checklist_id (int): 조회할 체크리스트 항목의 ID

        Returns:
            Optional[Checklist]: 조회된 체크리스트 항목 객체 또는 None
        """
        try:
            checklist = self.session.query(Checklist).filter(Checklist.user_id == self.user.id, Checklist.id == checklist_id).one_or_none()
            if checklist:
                logger.info(f'체크리스트 항목 ID {checklist_id}을(를) 조회했습니다.')
            else:
                logger.warning(f'체크리스트 항목 ID {checklist_id}을(를) 찾을 수 없습니다.')
            return checklist
        except SQLAlchemyError as e:
            logger.error(f'체크리스트 항목 조회 중 오류 발생: {str(e)}')
            raise
    
    def get_checklist_not_done(self):
        """
        완료되지 않은 체크리스트 항목들을 가져옵니다.

        Returns:
            List[Checklist]: 완료되지 않은 체크리스트 항목 리스트
        """
        try:
            checklists = self.session.query(Checklist).filter(Checklist.user_id == self.user.id, Checklist.is_complete == False).all()
            logger.info(f'완료되지 않은 체크리스트 항목 {len(checklists)}개를 조회했습니다.')
            return checklists
        except SQLAlchemyError as e:
            logger.error(f'미완료 체크리스트 항목 조회 중 오류 발생: {str(e)}')
            raise
    
    def get_checklist_done(self) -> Optional[List[Checklist]]:
        """
        완료된 체크리스트 항목들을 가져옵니다.

        Returns:
            List[Checklist]: 완료된 체크리스트 항목 리스트
        """
        try:
            checklists = self.session.query(Checklist).filter(Checklist.user_id == self.user.id, Checklist.is_complete == True).all()
            logger.info(f'완료된 체크리스트 항목 {len(checklists)}개를 조회했습니다.')
            return checklists
        except SQLAlchemyError as e:
            logger.error(f'완료된 체크리스트 항목 조회 중 오류 발생: {str(e)}')
            raise
