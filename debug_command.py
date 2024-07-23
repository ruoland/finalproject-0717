
from database_tables import  SessionFactory
from datetime import datetime, time
from database_tables import User
from register_manager import RegisterManager
from typing import List
from repository import UserRepository

time_now = datetime.now()

#나중에 세션 닫는 코드도 꼭 작성해야 함
#잊지말고
rm = RegisterManager(session=SessionFactory())

def get_user_with_id(self, user_id: int):
    return self.query(User).filter(User.id == user_id).one_or_none()

#가입 기능, 가입에 성공하면 가입한 유저 객체를 newuser라는 곳에 담아서 반환 하게 돼
newuser = rm.register_user(username='홍길동', email='홍길동@네이버닷컴', password='비밀번호', phone_number='000-00220-000')

#로그인 기능, 로그인 성공하면 loginUser 라는 변수에 유저 객체가 저장 돼
loginUser:User = rm.authenticate_user('홍길동', '비밀번호')

#user_repo, 유저의 데이터 공간 가져오기
user_repo = UserRepository(user=loginUser, session=SessionFactory())

#유저 체크리스트에 과제 A 추가하기
user_repo.checklist_repo.checklist_create('과제A', datetime(2024,7,20, 20,10))
#유저 체크리스트에 과제 A 추가하기
user_repo.checklist_repo.checklist_create('과제B', datetime(2024,7,25, 23,20))
#유저 체크리스트에 취미 A 추가하기
user_repo.hobby_repo.hobby_create('취미A', time_start=time(10,10), time_end=time(15,10), count=0, play_time=1)
#유저 체크리스트에 취미 B 추가하기
user_repo.hobby_repo.hobby_create('취미B', time_start=time(16,10), time_end=time(18,10), count=0, play_time=1)

user_repo.diary_repo.diary_create(write_date=datetime.now(), subtitle='다이어리 제목', content='다이어리 내용')
user_repo.schedule_repo.schedule_create(date=datetime(2024, 7, 23), subtitle='일정 제목', content='일정 내용')
# try:
   
#     # ICS 파일 읽기
#     with open('objectbow@gmail.com.ics', 'r', encoding='UTF-8') as file:
#         ics_content = file.read()

#     # ICS 파일 가져오기
#     imported_schedules = user_repo.schedule_repo.import_ics(ics_content)

#     # 가져온 일정 출력
#     for schedule in imported_schedules:
#         print(f"일정: {schedule.subtitle}")
#         print(f"날짜: {schedule.date}")
#         print(f"시작 시간: {schedule.start_time}")
#         print(f"종료 시간: {schedule.end_time}")
#         print(f"내용: {schedule.content}")
#         print("-" * 30)

# except Exception as e:
#     print(e)