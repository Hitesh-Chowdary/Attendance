import sys
import os
from datetime import datetime, date, time, timedelta
from passlib.context import CryptContext

# Adjust sys.path to run directly from the workspace root or directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_layer.connection import engine, Base, SessionLocal
from database_layer.models import (
    Branch, Section, Classroom, Student, Teacher, Subject, 
    TimetableSchedule, AttendanceLog, AttendanceStatus
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_database():
    print("Initialising database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if database is already seeded
        if db.query(Branch).first() is not None:
            print("Database already seeded. Skipping...")
            return

        print("Seeding branches...")
        branches_data = [
            {"name": "Computer Science & Engineering", "code": "CSE"},
            {"name": "Electronics & Communication Engineering", "code": "ECE"},
            {"name": "Information Technology", "code": "IT"},
            {"name": "Mechanical Engineering", "code": "ME"},
            {"name": "Civil Engineering", "code": "CE"},
            {"name": "Electrical & Electronics Engineering", "code": "EEE"},
            {"name": "Aeronautical Engineering", "code": "AE"},
            {"name": "Chemical Engineering", "code": "CHE"}
        ]
        branches = []
        for b in branches_data:
            branch = Branch(name=b["name"], code=b["code"])
            db.add(branch)
            branches.append(branch)
        db.commit()

        print("Seeding sections (Year 1 to 4)...")
        sections = []
        for branch in branches:
            for year in [1, 2, 3, 4]:
                for sec_letter in ["A", "B"]:
                    section = Section(
                        branch_id=branch.branch_id, 
                        year=year, 
                        section_name=f"{branch.code}-{year}{sec_letter}"
                    )
                    db.add(section)
                    sections.append(section)
        db.commit()

        print("Seeding classrooms...")
        classrooms_data = [
            {"room_number": "LH-301", "esp32_hardware_uid": "ESP32_UID_ROOM301"},
            {"room_number": "LH-302", "esp32_hardware_uid": "ESP32_DEV_ROOM302"},  # Matches developer target
            {"room_number": "LH-303", "esp32_hardware_uid": "ESP32_UID_ROOM303"},
            {"room_number": "Lab-201", "esp32_hardware_uid": "ESP32_UID_LAB201"},
            {"room_number": "Lab-202", "esp32_hardware_uid": "ESP32_UID_LAB202"}
        ]
        classrooms = []
        for c in classrooms_data:
            classroom = Classroom(room_number=c["room_number"], esp32_hardware_uid=c["esp32_hardware_uid"])
            db.add(classroom)
            classrooms.append(classroom)
        db.commit()

        print("Seeding teachers...")
        teachers_data = [
            {"name": "Dr. Sarah Jenkins", "email": "jenkins@college.edu", "password": "password123"},
            {"name": "Prof. David Miller", "email": "miller@college.edu", "password": "password123"},
            {"name": "Dr. Alice Vance", "email": "vance@college.edu", "password": "password123"}
        ]
        teachers = []
        for t in teachers_data:
            teacher = Teacher(
                name=t["name"], 
                email=t["email"], 
                password_hash=get_password_hash(t["password"])
            )
            db.add(teacher)
            teachers.append(teacher)
        db.commit()

        print("Seeding subjects...")
        subjects_data = [
            {"subject_name": "Software Engineering", "course_code": "CS-401"},
            {"subject_name": "Embedded Systems", "course_code": "EC-302"},
            {"subject_name": "Data Structures & Algorithms", "course_code": "CS-201"},
            {"subject_name": "Database Management Systems", "course_code": "IT-304"},
            {"subject_name": "Machine Learning", "course_code": "CS-405"}
        ]
        subjects = []
        for s in subjects_data:
            subject = Subject(subject_name=s["subject_name"], course_code=s["course_code"])
            db.add(subject)
            subjects.append(subject)
        db.commit()

        print("Seeding students (including developer profile)...")
        # Find CSE-1A (First Year CSE Section A) and CSE-3A (Third Year CSE Section A)
        cse_1a = next(s for s in sections if s.section_name == "CSE-1A")
        cse_3a = next(s for s in sections if s.section_name == "CSE-3A")
        ece_3a = next(s for s in sections if s.section_name == "ECE-3A")

        students_data = [
            # Main developer student profile
            {"reg_number": "23BCE040", "name": "Hitesh Kumar", "password": "password123", "section_id": cse_3a.section_id},
            {"reg_number": "23BCE041", "name": "Aman Verma", "password": "password123", "section_id": cse_3a.section_id},
            {"reg_number": "23BCE042", "name": "Rohan Sharma", "password": "password123", "section_id": cse_3a.section_id},
            {"reg_number": "23BCE043", "name": "Priya Patel", "password": "password123", "section_id": cse_3a.section_id},
            {"reg_number": "23BCE044", "name": "Sneha Reddy", "password": "password123", "section_id": cse_3a.section_id},
            
            # ECE student
            {"reg_number": "23BEC012", "name": "Karan Malhotra", "password": "password123", "section_id": ece_3a.section_id},
            
            # CSE 1st Year (Baseline stats check)
            {"reg_number": "25BCE001", "name": "Rahul Singh", "password": "password123", "section_id": cse_1a.section_id},
            {"reg_number": "25BCE002", "name": "Ananya Sen", "password": "password123", "section_id": cse_1a.section_id}
        ]
        students = []
        for s in students_data:
            student = Student(
                reg_number=s["reg_number"],
                name=s["name"],
                password_hash=get_password_hash(s["password"]),
                plain_password=s["password"],
                section_id=s["section_id"]
            )
            db.add(student)
            students.append(student)
        db.commit()

        print("Seeding timetable schedules...")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        # We need a schedule that matches "today" for easy testing
        today_name = datetime.utcnow().strftime("%A")
        
        schedules_data = [
            # Active schedule for testing in Room 302
            {
                "classroom_id": classrooms[1].classroom_id, # Room 302
                "teacher_id": teachers[0].teacher_id, # Sarah Jenkins
                "subject_id": subjects[0].subject_id, # Software Engineering
                "section_id": cse_3a.section_id, # CSE-3A
                "day_of_week": today_name,
                "start_time": time(8, 0),
                "end_time": time(20, 0) # Wide window for testing
            },
            # Active schedule for Monday in Room 301
            {
                "classroom_id": classrooms[0].classroom_id,
                "teacher_id": teachers[1].teacher_id,
                "subject_id": subjects[2].subject_id,
                "section_id": cse_1a.section_id,
                "day_of_week": "Monday",
                "start_time": time(9, 0),
                "end_time": time(10, 30)
            },
            # Active schedule for Tuesday in Room 303
            {
                "classroom_id": classrooms[2].classroom_id,
                "teacher_id": teachers[2].teacher_id,
                "subject_id": subjects[1].subject_id,
                "section_id": ece_3a.section_id,
                "day_of_week": "Tuesday",
                "start_time": time(11, 0),
                "end_time": time(12, 30)
            }
        ]
        
        schedules = []
        for s in schedules_data:
            schedule = TimetableSchedule(
                classroom_id=s["classroom_id"],
                teacher_id=s["teacher_id"],
                subject_id=s["subject_id"],
                section_id=s["section_id"],
                day_of_week=s["day_of_week"],
                start_time=s["start_time"],
                end_time=s["end_time"]
            )
            db.add(schedule)
            schedules.append(schedule)
        db.commit()

        print("Seeding past attendance logs for analytics...")
        # Create records for the last 3 weeks to generate charts
        today = date.today()
        hitesh = next(st for st in students if st.reg_number == "23BCE040")
        aman = next(st for st in students if st.reg_number == "23BCE041")
        
        # Test schedule
        test_sched = schedules[0]
        
        for i in range(1, 15):
            log_date = today - timedelta(days=i)
            # Skip weekends for realistic logs
            if log_date.weekday() >= 5:
                continue
            
            # Hitesh: 80% attendance
            hitesh_status = AttendanceStatus.PRESENT if (i % 5 != 0) else AttendanceStatus.ABSENT
            db.add(AttendanceLog(
                student_id=hitesh.student_id,
                schedule_id=test_sched.schedule_id,
                date=log_date,
                timestamp=datetime.combine(log_date, time(9, 5)),
                status=hitesh_status
            ))
            
            # Aman: 60% attendance (below 65% critical indicator test)
            aman_status = AttendanceStatus.PRESENT if (i % 3 == 0) else AttendanceStatus.ABSENT
            db.add(AttendanceLog(
                student_id=aman.student_id,
                schedule_id=test_sched.schedule_id,
                date=log_date,
                timestamp=datetime.combine(log_date, time(9, 8)),
                status=aman_status
            ))

        db.commit()
        print("Database successfully seeded with mock data!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
