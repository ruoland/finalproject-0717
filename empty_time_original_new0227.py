import logging
from datetime import datetime, time, date, timedelta
from collections import defaultdict
import random
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from database_tables import Base, User, Diary, Checklist, Hobby, Schedule, Holiday
from marshmallow import Schema, fields, ValidationError
from config import DATABASE_URL, LOG_LEVEL, LOG_FORMAT, DEFAULT_SLEEP_START, DEFAULT_SLEEP_END

# 로깅 설정
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# 데이터베이스 연결 설정
engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()

# 데이터 유효성 검사를 위한 스키마
class HobbySchema(Schema):
    name = fields.Str(required=True)
    preferred_time_start = fields.Time(required=True)
    preferred_time_end = fields.Time(required=True)
    count = fields.Int(allow_none=True)
    play_time = fields.Float(required=True)
    last_done_date = fields.DateTime(allow_none=True)

class CalendarRecommendation:
    def __init__(self, user_id):
        self.user_id = user_id
        self.calendar = {}
        self.hobbies = []
        self.tasks = []
        self.activity_stats = defaultdict(lambda: defaultdict(int))
        self.vectorizer = TfidfVectorizer()
        self.index = None
        self.activity_vectors = []
        self.activity_types = []
        self.restricted_times = {}
        self.default_sleep_time = (time.fromisoformat(DEFAULT_SLEEP_START), time.fromisoformat(DEFAULT_SLEEP_END))
        self.load_user_data()

    def load_user_data(self):
        with session_scope() as session:
            try:
                # 사용자의 일정 로드
                schedules = session.query(Schedule).filter(Schedule.user_id == self.user_id).all()
                for schedule in schedules:
                    self.add_event(schedule.date.date(), schedule.start_time, schedule.end_time, schedule.subtitle)

                # 사용자의 할 일 목록 로드
                checklists = session.query(Checklist).filter(Checklist.user_id == self.user_id, Checklist.is_complete == False).all()
                for checklist in checklists:
                    self.add_task(checklist.content, checklist.deadline, checklist.divisible, checklist.category)

                # 사용자의 취미 로드
                hobbies = session.query(Hobby).filter(Hobby.user_id == self.user_id).all()
                for hobby in hobbies:
                    self.add_hobby(hobby.name, hobby.preferred_time_start, hobby.preferred_time_end, hobby.count, hobby.play_time, hobby.last_done_date)
            except Exception as e:
                logger.error(f"Error loading user data: {str(e)}")
                raise

    def add_hobby(self, name, preferred_time_start, preferred_time_end, count, play_time, last_done_date):
        hobby_data = {
            "name": name,
            "preferred_time_start": preferred_time_start,
            "preferred_time_end": preferred_time_end,
            "count": count,
            "play_time": play_time,
            "last_done_date": last_done_date
        }
        
        # 데이터 유효성 검사
        try:
            HobbySchema().load(hobby_data)
        except ValidationError as err:
            logger.error(f"Invalid hobby data: {err.messages}")
            return

        self.hobbies.append(hobby_data)
        self.activity_vectors.append(name)
        self.activity_types.append('hobby')
        logger.info(f"Added hobby: {name}")
    def set_restricted_time(self, date, start_time, end_time, reason=""):
        if date not in self.restricted_times:
            self.restricted_times[date] = []
        self.restricted_times[date].append((start_time, end_time, reason))

    def set_default_sleep_time(self, sleep_start, sleep_end):
        self.default_sleep_time = (sleep_start, sleep_end)

    def add_event(self, date, start_time, end_time, event_type):
        if date not in self.calendar:
            self.calendar[date] = []
        self.calendar[date].append((start_time, end_time, event_type))
        hour = start_time.hour
        self.activity_stats[event_type][hour] += 1
        self.activity_vectors.append(event_type)
        self.activity_types.append('event')

    def add_hobby(self, name, preferred_time_start, preferred_time_end, count, play_time, last_done_date):
        self.hobbies.append({
            "name": name,
            "preferred_time_start": preferred_time_start,
            "preferred_time_end": preferred_time_end,
            "count": count,
            "play_time": play_time,
            "last_done_date": last_done_date
        })
        self.activity_vectors.append(name)
        self.activity_types.append('hobby')
    def add_task(self, content, deadline, divisible, category):
        self.tasks.append({
            "content": content,
            "deadline": deadline,
            "divisible": divisible,
            "category": category,
            "completed": False,
            "completion_date": None
        })
        self.activity_vectors.append(content)
        self.activity_types.append('task')
    def is_time_restricted(self, date, time):
        if date in self.restricted_times:
            for start, end, _ in self.restricted_times[date]:
                if start <= time < end:
                    return True
        sleep_start, sleep_end = self.default_sleep_time
        if sleep_start <= time or time < sleep_end:
            return True
        return False

    def find_free_time(self, date):
        all_events = sorted(self.calendar.get(date, []) + self.restricted_times.get(date, []))
        free_times = []
        last_end = time(0, 0)

        for start, end, _ in all_events:
            if start > last_end and not self.is_time_restricted(date, last_end):
                free_times.append((last_end, start))
            last_end = max(last_end, end)

        if last_end < time(23, 59) and not self.is_time_restricted(date, last_end):
            free_times.append((last_end, time(23, 59)))

        return free_times
    def recommend_activities(self, date):
        free_times = self.find_free_time(date)
        if not free_times:
            return []

        recommendations = []
        used_activities = set()

        # 현재 날짜와 시간
        current_datetime = datetime.now()
        
        # 해당 날짜의 태스크만 선택하고, 기한이 지나지 않은 것만 선택
        sorted_tasks = sorted([
            t for t in self.tasks 
            if not t['completed'] and t['deadline'].date() >= date
        ], key=lambda x: x['deadline'])

        for start, end in free_times:
            current_time = datetime.combine(date, start)
            end_time = datetime.combine(date, end)
            
            while current_time < end_time:
                duration = (end_time - current_time).total_seconds() / 3600
                
                if duration < 0.5:  # 최소 30분 이상의 빈 시간이 있을 때만 활동 추천
                    break

                # 2시간마다 30분 휴식 시간 추가
                if len(recommendations) > 0 and (current_time - datetime.combine(date, recommendations[-1][1])).total_seconds() / 3600 >= 2:
                    rest_end_time = current_time + timedelta(minutes=30)
                    if not self.is_time_restricted(date, rest_end_time.time()):
                        recommendations.append((current_time.time(), rest_end_time.time(), "휴식 시간"))
                        current_time = rest_end_time
                        continue

                # 할 일 추천
                task_recommended = False
                for task in sorted_tasks:
                    if task['content'] not in used_activities:
                        # 작업 시간을 1시간으로 가정 (또는 다른 적절한 방법으로 추정)
                        task_duration = min(1, duration)  
                        task_end_time = current_time + timedelta(hours=task_duration)

                        if not self.is_time_restricted(date, task_end_time.time()):
                            recommendations.append((current_time.time(), task_end_time.time(), f"할 일: {task['content']} (카테고리: {task['category']})"))
                            used_activities.add(task['content'])
                            current_time = task_end_time
                            task_recommended = True
                            break

                # 취미 추천 (할 일이 추천되지 않은 경우)
                if not task_recommended:
                    for hobby in sorted(self.hobbies, key=lambda x: x['last_done_date'] or date.min):
                        if (hobby['name'] not in used_activities and
                            
                            hobby['preferred_time_start'] <= current_time.time() < hobby['preferred_time_end']):
                            if 'play_time' not in hobby:
                                print('넘어갑니다', hobby)
                                continue  # 'play_time' 키가 없는 경우 해당 취미 건너뛰기
                            
                            hobby_duration = min(hobby['play_time'], duration)
                            hobby_end_time = current_time + timedelta(hours=hobby_duration)
                            if not self.is_time_restricted(date, hobby_end_time.time()):
                                recommendations.append((current_time.time(), hobby_end_time.time(), f"취미: {hobby['name']}"))
                                used_activities.add(hobby['name'])
                                current_time = hobby_end_time
                                break
                    else:
                        # 추천할 활동이 없으면 다음 시간대로 이동
                        current_time += timedelta(hours=1)

        # 시간 순서대로 정렬
        recommendations.sort(key=lambda x: x[0])
        return recommendations

    def print_recommendations(self, date):
        recommendations = self.recommend_activities(date)
        if not recommendations:
            print(f"{date}에는 추천할 만한 충분한 여유 시간이 없습니다.")
        else:
            print(f"{date}의 추천 활동:")
            for start, end, activity in recommendations:
                duration = (datetime.combine(date, end) - datetime.combine(date, start)).total_seconds() / 3600
                print(f"  {start.strftime('%H:%M')} - {end.strftime('%H:%M')} ({duration:.1f}시간): {activity}")

if __name__ == "__main__":
    user_id = 1  # 예시 사용자 ID
    cr = CalendarRecommendation(user_id)
    
    # 기본 수면 시간 설정 (수정된 부분)
    cr.set_default_sleep_time(time(23, 0), time(7, 0))
    
    # 특정 날짜에 제한 시간 설정
    today = date.today()
    cr.set_restricted_time(today, time(12, 0), time(13, 0), "점심 시간")
    cr.set_restricted_time(today, time(18, 0), time(19, 0), "저녁 식사")
    
    # 추천 출력
    cr.print_recommendations(today)
    