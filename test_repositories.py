import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_tables import Base, Schedule, User
from datetime import time, datetime
from repository import ScheduleRepository, CheckListRepository, HobbyRepository
from repository.diary_repository import DiaryRepository

class TestRepositories(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_user = 'admin'
        db_password = '5642'
        db_host = 'localhost'
        db_port = 5432
        db_database = 'test_db'
        dsn = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_database}"
        cls.engine = create_engine(dsn)
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        # Create a test user only once
        session = cls.Session()
        #
        cls.user = session.query(User).filter(User.username == '홍길동').first()
        session.add(cls.user)
        session.commit()
        cls.user_id = cls.user.id
        session.close()

    def setUp(self):
        self.session = self.__class__.Session()
        self.user:User = self.session.query(User).get(self.__class__.user_id)
        print('INFO:root:',self.user.username, '라는 이름으로 테스트를 진행합니다...')
        # Initialize repositories
        self.diary_repo = DiaryRepository(self.session, self.user)
        self.schedule_repo = ScheduleRepository(self.session, self.user)
        self.checklist_repo = CheckListRepository(self.session, self.user)
        self.hobby_repo = HobbyRepository(self.session, self.user)

    def tearDown(self):
        self.session.close()

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_diary_repository(self):
        # Test diary_create
        diary = self.diary_repo.diary_create(
            write_date=datetime.now(),
            subtitle="Test Diary",
            content="This is a test diary entry",
            keyword="test",
            emotion_data="happy",
            weather="sunny"
        )
        self.assertIsNotNone(diary)

        # Test diary_update
        updated = self.diary_repo.diary_update(
            diary.id,
            subtitle="다이어리 수정 테스트",
            content="This is an updated test diary entry"
        )
        self.assertTrue(updated)
        # Test get_diary_with_id
        retrieved_diary = self.diary_repo.get_diary_with_id(diary.id)
        self.assertEqual(retrieved_diary.subtitle, "다이어리 수정 테스트")
        # Test get_diaries_by_date_range
        diaries = self.diary_repo.get_diaries_by_date_range(
            datetime.now() - timedelta(days=1),
            datetime.now() + timedelta(days=1)
        )
        self.assertEqual(len(diaries), 1)
        # Test diary_delete
        self.diary_repo.delete_diary(diary.id)
        deleted_diary = self.diary_repo.get_diary_with_id(diary.id)
        self.assertIsNone(deleted_diary)
        print('\n')
    def test_schedule_repository(self):
        # Test schedule_create
        schedule = self.schedule_repo.schedule_create(
            subtitle="Test Schedule",
            date=datetime.now(),
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1),
            content="This is a test schedule",
            is_alarm=True
        )
        self.assertIsNotNone(schedule)

        # Test schedule_update
        updated = self.schedule_repo.schedule_update(
            schedule.id,
            subtitle="일정 업데이트",
            content="This is an updated test schedule"
        )
        self.assertTrue(updated)

        # Test get_schedule_with_id
        retrieved_schedule:Schedule = self.schedule_repo.get_schedule_with_id(schedule.id)
        self.assertEqual(retrieved_schedule.subtitle, "일정 업데이트")

        # Test get_schedules_by_date_range
        schedules = self.schedule_repo.get_schedules_by_date_range(
            datetime.now() - timedelta(days=1),
            datetime.now() + timedelta(days=1)
        )
        self.assertEqual(len(schedules), 1)

        # Test schedule_delete
        deleted = self.schedule_repo.schedule_delete(schedule.id)
        self.assertTrue(deleted)
        print('\n')
    def test_checklist_repository(self):
        # Test checklist_create
        checklist = self.checklist_repo.checklist_create(
            content="할일 테스트",
            deadline=datetime.now() + timedelta(days=1)
        )
        self.assertIsNotNone(checklist)

        # Test checklist_update
        updated = self.checklist_repo.checklist_update(
            checklist.id,
            content="할 일 수정 테스트"
        )
        self.assertTrue(updated)

        # Test checklist_complete_done
        completed = self.checklist_repo.checklist_complete_done(checklist.id, True)
        self.assertTrue(completed)

        # Test get_checklist_with_id
        retrieved_checklist = self.checklist_repo.get_checklist_with_id(checklist.id)
        self.assertEqual(retrieved_checklist.content, "할 일 수정 테스트")
        self.assertTrue(retrieved_checklist.is_complete)

        # Test get_checklist_done and get_checklist_not_done
        done_checklists = self.checklist_repo.get_checklist_done()
        not_done_checklists = self.checklist_repo.get_checklist_not_done()
        self.assertEqual(len(done_checklists), 1)
        self.assertEqual(len(not_done_checklists), 0)

        # Test checklist_delete
        deleted = self.checklist_repo.checklist_delete(checklist.id)
        self.assertTrue(deleted)
        print('\n')
    def test_hobby_repository(self):
        # Test hobby_create
        hobby = self.hobby_repo.hobby_create(
            name="취미 테스트",
            time_start=time(10,10),
            time_end=time(10,10),
            count=0,
            play_time=0
        )
        self.assertIsNotNone(hobby)

        # Test hobby_update
        updated = self.hobby_repo.hobby_update(
            hobby.id,
            name="취미 수정 테스트",
            play_time=1.5
        )
        self.assertTrue(updated)

        # Test get_hobby_with_id
        retrieved_hobby = self.hobby_repo.get_hobby_with_id(hobby.id)
        self.assertEqual(retrieved_hobby.name, "취미 수정 테스트")

        # Test get_hobbies_by_preferred_time
        hobbies = self.hobby_repo.get_hobbies_by_preferred_time(time(10,10))
        self.assertEqual(len(hobbies), 1)
        print(' 플레이타임',hobbies[0].play_time)
        # Test update_hobby_stats
        stats_updated = self.hobby_repo.update_hobby_stats(hobby.id, 2.5)
        self.assertTrue(stats_updated)
        print(stats_updated)
        updated_hobby = self.hobby_repo.get_hobby_with_id(hobby.id)
        self.assertEqual(updated_hobby.count, 1)
        self.assertEqual(updated_hobby.play_time, 5.0)
        print('\n')
        # Test hobby_delete
        deleted = self.hobby_repo.hobby_delete(hobby.id)
        self.assertTrue(deleted)
        print('각 테이블에 대한 데이터 삽입, 수정, 데이터 조회, 삭제에 대한 테스트가 성공적으로 끝났습니다.')
if __name__ == '__main__':
    unittest.main()