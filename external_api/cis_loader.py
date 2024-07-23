from icalendar import Calendar, Event
from datetime import datetime
import pytz

class ICSProcessor:
    def __init__(self):
        self.calendar = None

    def load_ics(self, file_path):
        """ICS 파일을 로드합니다."""
        try:
            with open(file_path, 'rb') as file:
                self.calendar = Calendar.from_ical(file.read())
            print("ICS 파일을 성공적으로 로드했습니다.")
        except FileNotFoundError:
            print(f"파일을 찾을 수 없습니다: {file_path}")
        except ValueError:
            print("ICS 파일 파싱 중 오류가 발생했습니다.")

    def get_events(self):
        """모든 이벤트를 반환합니다."""
        if self.calendar is None:
            print("캘린더가 로드되지 않았습니다. 먼저 load_ics 메서드를 호출하세요.")
            return []

        events = []
        for component in self.calendar.walk():
            if component.name == "VEVENT":
                event = {
                    'summary': component.get('summary'),
                    'description': component.get('description'),
                    'location': component.get('location'),
                    'start': component.get('dtstart').dt,
                    'end': component.get('dtend').dt if component.get('dtend') else None,
                }
                events.append(event)
        return events

    def add_event(self, summary, start_time, end_time, description=None, location=None):
        """새 이벤트를 추가합니다."""
        if self.calendar is None:
            self.calendar = Calendar()

        event = Event()
        event.add('summary', summary)
        event.add('dtstart', start_time)
        event.add('dtend', end_time)
        if description:
            event.add('description', description)
        if location:
            event.add('location', location)

        self.calendar.add_component(event)
        print(f"이벤트 '{summary}'가 추가되었습니다.")

    def save_ics(self, output_path):
        """처리된 캘린더를 새 ICS 파일로 저장합니다."""
        if self.calendar is None:
            print("캘린더가 로드되지 않았습니다. 먼저 load_ics 메서드를 호출하세요.")
            return

        with open(output_path, 'wb') as file:
            file.write(self.calendar.to_ical())
        print(f"처리된 캘린더를 {output_path}에 저장했습니다.")

# 사용 예시
if __name__ == "__main__":
    processor = ICSProcessor()
    processor.load_ics("input.ics")
    
    events = processor.get_events()
    print(f"총 {len(events)}개의 이벤트가 있습니다.")
    for event in events[:5]:  # 처음 5개 이벤트만 출력
        print(f"이벤트: {event['summary']}, 시작: {event['start']}")

    # 새 이벤트 추가
    processor.add_event(
        summary="팀 미팅",
        start_time=datetime(2023, 7, 20, 14, 0, tzinfo=pytz.UTC),
        end_time=datetime(2023, 7, 20, 15, 0, tzinfo=pytz.UTC),
        description="주간 팀 미팅",
        location="회의실 A"
    )

    processor.save_ics("output.ics")