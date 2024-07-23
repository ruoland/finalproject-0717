from typing import Optional, List
from sqlalchemy.orm import Session
from database_tables import Image, User, Diary
from datetime import datetime
import logging as logger
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

class DiaryRepository:
    """
    DiaryRepository class handles all database operations related to diaries.
    """

    def __init__(self, session: Session, user: User):
        """
        일기 리포지토리를 초기화 합니다

        Args:
            session (Session): DB와 연결을 위한 세션
            user (User): 현재 이 다이어리를 갖고 있는 유저 객체
        """
        self.session = session
        self.user = user
    def diary_create(self, write_date: datetime, subtitle: str, content: str, 
                     keyword: Optional[str] = 'None', emotion_data: Optional[str] = 'None', 
                     weather: Optional[str] = None, image_files: Optional[list[dict]] = None, 
                     tags: Optional[str] = None) -> Optional[Diary]:
        """
        Create a new diary entry.

        Args:
            필수로 작성해야 하는 것
            write_date (datetime): 다이어리 작성 날짜
            subtitle (str): 다이어리의 제목
            content (str): 다이어리의 내용
            
            작성하지 않아도 괜찮은 것들
            keyword (Optional[str]): 다이어리의 키워드, 기본적으로 None 으로 설정 되어 있습니다. 나중에 자동으로 부여하게 할 거
            emotion_data (Optional[str]): 감정 데이터, 이것도 키워드처럼 나중에 자동으로 부여하게 할 거
            weather (Optional[str]): 날씨, 이 다이어리가 작성된 날의 날짜입니다, 이건 해도 되고 안 해도 되고
            image_files (Optional[list[dict]]): 다이어리에 추가한 이미지 파일들의 경로를 입력하는 곳인데 이것도 나중에
            tags (Optional[str]): 다이어리의 태그 태그

        Returns:
            Optional[Diary]: 만약 다이어리가 성공적으로 생성되면 다이어리 개체를 반환하고, 아닌 경우 None을 반환합니다
        """
        try:
            new_diary = Diary(user_id=self.user.id, write_date=write_date, subtitle=subtitle, 
                              content=content, weather=weather, emotion_data=emotion_data, 
                              tags=tags, keyword=keyword)
            self.session.add(new_diary)
            
            if image_files:
                for img in image_files:
                    new_image = Image(diary_id=new_diary.id, file_path=img['file_path'], file_name=img['file_name'])
                    new_diary.images.append(new_image)

            self.session.commit()
            logger.info(f"Diary created successfully: {subtitle}")
            return new_diary
        except IntegrityError:
            self.session.rollback()
            logger.error("Failed to create diary: Integrity Error")
            print("오류: 중복된 데이터 또는 필수 필드 누락으로 인해 일기를 생성할 수 없습니다.")
            return None
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create diary: {str(e)}")
            print("오류: 데이터베이스 오류로 인해 일기를 생성할 수 없습니다.")
            return None
    
    

    def diary_update(self, diary_id: int, subtitle: Optional[str] = None, 
                     content: Optional[str] = None, date: Optional[datetime] = None,
                     weather: Optional[str] = None, image: Optional[str] = None, 
                     tags: Optional[str] = None) -> bool:
        """
        Update an existing diary entry.

        Args:
            diary_id (int): 업데이트할 다이어리의 ID.
            
            수정할 것들만 선택하여 아래처럼 작성하기
            예시: diary_update(2, subtitle='새로운 제목', content='새로운 내용')
            
            subtitle (Optional[str]): New subtitle for the diary.
            content (Optional[str]): New content for the diary.
            date (Optional[datetime]): New date for the diary.
            weather (Optional[str]): New weather information.
            image (Optional[str]): New image information.
            tags (Optional[str]): New tags for the diary.

        Returns:
            bool: 업데이트가 잘 되면 True를, 어떤 이유로 안 된다면 False을 반홥합니다
        """
        try:
            diary = self.session.query(Diary).filter(Diary.user_id == self.user.id, Diary.id == diary_id).first()
            if diary:
                if subtitle is not None:
                    diary.subtitle = subtitle
                if content is not None:
                    diary.content = content
                if date is not None:
                    diary.edit_time = date
                if weather is not None:
                    diary.weather = weather
                if image is not None:
                    diary.image = image
                if tags is not None:
                    diary.tags = tags
                self.session.commit()
                logger.info(f"Diary updated successfully: {diary_id}")
                return True
            else:
                logger.warning(f"Diary not found: {diary_id}")
                print("경고: 업데이트할 일기를 찾을 수 없습니다.")
                return False
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to update diary: {str(e)}")
            print("오류: 데이터베이스 오류로 인해 일기를 업데이트할 수 없습니다.")
            return False
        
    def delete_diary(self, diary_id: int) -> bool:
        """
        Delete a diary entry.

        Args:
            diary_id (int): ID of the diary to delete.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        try:
            select_diary = self.session.query(Diary).filter(Diary.user_id == self.user.id, Diary.id == diary_id).one()
            self.session.delete(select_diary)
            self.session.commit()
            logger.info(f"Diary deleted successfully: {select_diary.subtitle}")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to delete diary: {str(e)}")
            print("오류: 데이터베이스 오류로 인해 일기를 삭제할 수 없습니다.")
            return False

    def get_user_diaries(self) -> Optional[List[Diary]]:
        """
        Retrieve all diaries for the current user.

        Returns:
            List[Diary]: A list of all diary objects for the user.
        """
        try:
            diaries = self.session.query(Diary).filter(Diary.user_id == self.user.id).all()
            logger.info(f"Retrieved {len(diaries)} diaries for user {self.user.id}")
            return diaries
        except SQLAlchemyError as e:
            logger.error(f"Failed to retrieve user diaries: {str(e)}")
            print("오류: 데이터베이스 오류로 인해 일기 목록을 가져올 수 없습니다.")
            return []
    
    def get_diary_with_id(self, diary_id: int) -> Optional[Diary]:
        """
        주어진 ID에 해당하는 일기를 조회합니다.

        Args:
            diary_id (int): 조회할 일기의 ID

        Returns:
            Optional[Diary]: 조회된 일기 객체. 없을 경우 None 반환

        Raises:
            SQLAlchemyError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            diary = self.session.query(Diary).filter(
                Diary.user_id == self.user.id, 
                Diary.id == diary_id
            ).first()
            
            if diary:
                logger.info(f"사용자 {self.user.id}의 일기 ID {diary_id}를 조회했습니다.")
            else:
                logger.info(f"사용자 {self.user.id}의 일기 ID {diary_id}를 찾을 수 없습니다.")
            
            return diary
        except SQLAlchemyError as e:
            logger.error(f"일기 {diary_id} 조회 중 데이터베이스 오류 발생: {str(e)}")
            self.session.rollback()
            raise

    def get_diaries_by_date_range(self, start_date: datetime, end_date: datetime) -> Optional[List[Diary]]:
        """
        주어진 날짜 범위 내의 모든 일기를 조회합니다.

        Args:
            start_date (datetime): 조회 시작 날짜
            end_date (datetime): 조회 종료 날짜

        Returns:
            List[Diary]: 조회된 일기 객체 리스트

        Raises:
            SQLAlchemyError: 데이터베이스 조회 중 오류 발생 시
        """
        try:
            diaries = self.session.query(Diary).filter(
                Diary.user_id == self.user.id,
                Diary.write_date.between(start_date, end_date)
            ).all()
            
            logger.info(f"사용자 {self.user.id}의 {start_date}부터 {end_date}까지의 일기 {len(diaries)}개를 조회했습니다.")
            return diaries
        except SQLAlchemyError as e:
            logger.error(f"일기 조회 중 데이터베이스 오류 발생: {str(e)}")
            self.session.rollback()
            raise