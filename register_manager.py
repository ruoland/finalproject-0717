
from typing import Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database_tables import User
import bcrypt
import logging
# 기본 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
class RegisterManager:
    def __init__(self, session: Session):
        self.session = session
        print()
    def register_user(self, username: str, email: str, password: str, phone_number: str) -> Optional[User]:
            try:
                if self.check_duplicate_user(username, phone_number, email):
                    hashed_password = self.hash_password(password) # 비밀번호 암호화
                    new_user = User(
                        username=username,
                        email=email,
                        password_hash=hashed_password,
                        phone_number=phone_number,
                        birth_day='없음'
                    )
                    self.session.add(new_user)
                    self.session.commit()
                    logger.info(f"사용자 {username} 등록 완료")
                    return new_user
                else:
                    logger.warning("사용자 등록 실패: 중복된 정보")
                    return None
            except SQLAlchemyError as e:
                self.session.rollback()
                logger.error(f"사용자 등록 중 오류 발생: {str(e)}")
                return None

    def check_duplicate_user(self, username: str, phone_number: str, email: str) -> bool:
            try:
                existing_user = self.session.query(User).filter(
                    (User.username == username) | 
                    (User.phone_number == phone_number) | 
                    (User.email == email)
                ).first()
                if existing_user:
                    if existing_user.username == username:
                        logger.info("이미 등록된 아이디입니다.")
                        return False
                    if existing_user.phone_number == phone_number:
                        logger.info("이미 등록된 전화번호입니다.")
                        return False
                    if existing_user.email == email:
                        logger.info("이미 등록된 이메일이 있습니다.")
                        return False
                return True
            except SQLAlchemyError as e:
                logger.error(f"중복 유저 검사하던 중, 그리고 데이터베이스 조회 중 오류 발생: {str(e)}")
                return False

    def hash_password(self, password: str) -> str:
            password_bytes = password.encode('utf-8') # 비밀번호를 bytes로 변환하기
            salt = bcrypt.gensalt() # 소금치기
            hashed = bcrypt.hashpw(password_bytes, salt) # 해시값으로 암호화 하기
            logger.debug('비밀번호를 암호화 했습니다.')
            return hashed.decode('utf-8') # 해싱된 비밀번호를 다시 복호화 하여 Str로 만들기

    def verify_password(self, plain_password: str, hashed_password: str) -> bool: 
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)

    def authenticate_user(self, username: str, password: str) -> Union[User, None]:
            try:
                user = self.session.query(User).filter(User.username == username).first()
                if user and self.verify_password(password, user.password_hash):
                    logger.info('로그인 완료 되었습니다.')
                    return user
                logger.warning('로그인에 실패하였습니다.')
                return None
            except SQLAlchemyError as e:
                logger.error(f"인증 중 오류 발생: {str(e)}")
                return None
