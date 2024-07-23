import datetime
from collections import defaultdict
import random
import csv
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import faiss

class CalendarRecommendation:
    def __init__(self):
        self.calendar = {}
        self.hobbies = []
        self.tasks = []
        self.activity_stats = defaultdict(lambda: defaultdict(int))
        self.vectorizer = TfidfVectorizer()
        self.index = None
        self.activity_vectors = []
        self.activity_types = []

    def add_event(self, date, start_time, end_time, event_type):
        if date not in self.calendar:
            self.calendar[date] = []
        self.calendar[date].append((start_time, end_time, event_type))
        hour = start_time.hour
        self.activity_stats[event_type][hour] += 1
        self.activity_vectors.append(event_type)
        self.activity_types.append('event')

    def add_hobby(self, name, preferred_time_start, preferred_time_end, frequency_per_week, duration, last_done_date):
        self.hobbies.append({
            "name": name,
            "preferred_time_start": preferred_time_start,
            "preferred_time_end": preferred_time_end,
            "frequency_per_week": frequency_per_week,
            "duration": duration,
            "last_done_date": last_done_date
        })
        self.activity_vectors.append(name)
        self.activity_types.append('hobby')

    def add_task(self, name, deadline, estimated_time, divisible, completed, completion_date):
        self.tasks.append({
            "name": name,
            "deadline": deadline,
            "estimated_time": estimated_time,
            "divisible": divisible,
            "completed": completed,
            "completion_date": completion_date
        })
        self.activity_vectors.append(name)
        self.activity_types.append('task')

    def build_index(self):
        vectors = self.vectorizer.fit_transform(self.activity_vectors).toarray()
        self.index = faiss.IndexFlatL2(vectors.shape[1])
        self.index.add(vectors.astype(np.float32))

    def find_similar_activities(self, query, k=5):
        query_vector = self.vectorizer.transform([query]).toarray().astype(np.float32)
        _, indices = self.index.search(query_vector, k)
        return [(self.activity_vectors[i], self.activity_types[i]) for i in indices[0]]

    def find_free_time(self, date):
        if date not in self.calendar:
            return [(datetime.time(0, 0), datetime.time(23, 59))]

        events = sorted(self.calendar[date])
        free_times = []
        last_end = datetime.time(0, 0)

        for start, end, _ in events:
            if start > last_end:
                free_times.append((last_end, start))
            last_end = max(last_end, end)

        if last_end < datetime.time(23, 59):
            free_times.append((last_end, datetime.time(23, 59)))

        return free_times

    def get_best_activity_time(self, activity_type):
        if not self.activity_stats[activity_type]:
            return random.randint(9, 20)
        return max(self.activity_stats[activity_type], key=self.activity_stats[activity_type].get)

    def recommend_activities(self, date):
        free_times = self.find_free_time(date)
        if not free_times:
            return []

        recommendations = []
        used_activities = set()

        # 할 일 목록 정렬 (마감일 기준)
        sorted_tasks = sorted([t for t in self.tasks if not t['completed'] and t['deadline'] >= date],
                              key=lambda x: x['deadline'])

        for start, end in free_times:
            current_time = start
            while current_time < end:
                duration = (datetime.datetime.combine(date, end) - datetime.datetime.combine(date, current_time)).total_seconds() / 3600
                if duration < 0.5:  # 30분 미만의 시간은 무시
                    break

                # 할 일 추천
                task_recommended = False
                for task in sorted_tasks:
                    if task['name'] not in used_activities:
                        task_duration = min(task['estimated_time'], duration)
                        task_end_time = (datetime.datetime.combine(date, current_time) + datetime.timedelta(hours=task_duration)).time()

                        # 취미 선호 시간과 겹치는지 확인
                        hobby_conflict = False
                        for hobby in self.hobbies:
                            if (current_time.hour >= hobby['preferred_time_start'] and
                                current_time.hour < hobby['preferred_time_end']):
                                hobby_conflict = True
                                break

                        if hobby_conflict:
                            # 취미 선호 시간과 겹치면 할 일 추천을 미룸
                            break

                        recommendations.append((current_time, task_end_time, f"할 일: {task['name']}"))
                        used_activities.add(task['name'])
                        current_time = task_end_time
                        task_recommended = True
                        break

                # 취미 추천 (할 일이 추천되지 않은 경우)
                if not task_recommended:
                    for hobby in sorted(self.hobbies, key=lambda x: x['last_done_date'] or datetime.date.min):
                        if (hobby['name'] not in used_activities and
                            current_time.hour >= hobby['preferred_time_start'] and
                            current_time.hour < hobby['preferred_time_end']):
                            hobby_duration = min(hobby['duration'], duration)
                            hobby_end_time = (datetime.datetime.combine(date, current_time) + datetime.timedelta(hours=hobby_duration)).time()
                            recommendations.append((current_time, hobby_end_time, f"취미: {hobby['name']}"))
                            used_activities.add(hobby['name'])
                            current_time = hobby_end_time
                            break
                    else:
                        # 추천할 활동이 없으면 다음 시간대로 이동
                        current_time = (datetime.datetime.combine(date, current_time) + datetime.timedelta(hours=1)).time()

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
                duration = (datetime.datetime.combine(date, end) - datetime.datetime.combine(date, start)).total_seconds() / 3600
                print(f"  {start.strftime('%H:%M')} - {end.strftime('%H:%M')} ({duration:.1f}시간): {activity}")

    def load_from_file(self, filename):
        with open(filename, 'r', encoding='UTF-8') as file:
            reader = csv.reader(file)
            next(reader)  # 헤더 행 건너뛰기
            for row in reader:
                data_type = row[0]
                if data_type == 'event':
                    date = datetime.datetime.strptime(row[1], '%Y-%m-%d').date()
                    start_time = datetime.datetime.strptime(row[2], '%H:%M').time()
                    end_time = datetime.datetime.strptime(row[3], '%H:%M').time()
                    event_type = row[4]
                    self.add_event(date, start_time, end_time, event_type)
                elif data_type == 'hobby':
                    name = row[1]
                    preferred_start = int(row[2])
                    preferred_end = int(row[3])
                    frequency = int(row[4])
                    duration = float(row[5])
                    last_done_date = datetime.datetime.strptime(row[6], '%Y-%m-%d').date() if row[6] else None
                    self.add_hobby(name, preferred_start, preferred_end, frequency, duration, last_done_date)
                elif data_type == 'task':
                    name = row[1]
                    deadline = datetime.datetime.strptime(row[2], '%Y-%m-%d').date()
                    estimated_time = float(row[3])
                    divisible = row[4].lower() == 'true'
                    completed = row[5].lower() == 'true'
                    completion_date = datetime.datetime.strptime(row[6], '%Y-%m-%d').date() if row[6] else None
                    self.add_task(name, deadline, estimated_time, divisible, completed, completion_date)
        self.build_index()

# 사용 예시
if __name__ == "__main__":
    cr = CalendarRecommendation()
    cr.load_from_file('calendar_data.csv')
    today = datetime.date.today()
    cr.print_recommendations(today)