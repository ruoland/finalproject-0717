import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from database_tables import Holiday
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = "3IpRs6A2neT5UHVp0qnHiQ379CHsWwiz5AQD9qaY4dNGS148Nkl29ABsPcNESnxACMlQornuCXqjLlLaGRp6fg=="
BASE_URL = "http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getHoliDeInfo"

def fetch_holidays(year: int):
    params = {
        'serviceKey': API_KEY,
        'solYear': str(year),
        'numOfRows': '100',
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()  # HTTP 오류 발생 시 예외를 발생시킵니다.

        root = ET.fromstring(response.content)
        items = root.findall('.//item')

        holidays = []
        for item in items:
            date_str = item.find('locdate').text
            name = item.find('dateName').text
            is_holiday = True  # API에서 가져온 모든 날짜를 공휴일로 간주

            date = datetime.strptime(date_str, '%Y%m%d')
            holidays.append(database_tables.Holiday(
                date=date,
                name=name,
                is_holiday=is_holiday
            ))

        return holidays
    except requests.RequestException as e:
        logging.error(f"API 요청 중 오류 발생: {e}")
        return []

def update_holidays_in_db(session: Session, year: int):
    holidays = fetch_holidays(year)
    
    try:
        for holiday in holidays:
            existing_holiday = session.query(Holiday).filter_by(date=holiday.date).first()
            
            if existing_holiday:
                existing_holiday.name = holiday.name
                existing_holiday.is_holiday = holiday.is_holiday
            else:
                session.add(holiday)

        session.commit()
        logging.info(f"{year}년 공휴일 정보가 성공적으로 업데이트되었습니다. 총 {len(holidays)}개의 항목 처리.")
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"데이터베이스 업데이트 중 오류 발생: {e}")


def update_holidays_for_range(start_year: int, end_year: int):
    session = sessionmaker()
    try:
        for year in range(start_year, end_year + 1):
            update_holidays_in_db(session, year)
    finally:
        session.close()