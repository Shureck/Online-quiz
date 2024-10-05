from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5435/biji"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=30,            # Максимум 30 соединений
    max_overflow=10,          # Дополнительные 10 соединений, если 30 заняты
    pool_timeout=30,          # Тайм-аут ожидания соединения
)
# SessionLocal для контекстного управления сессиями
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Создание всех таблиц в базе данных

class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    unique_id = Column(String, unique=True, index=True)

class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String)
    options = Column(String)  # Варианты ответов в виде JSON строки
    correct_answer = Column(String)

class Answer(Base):
    __tablename__ = 'answers'
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    question_id = Column(Integer, ForeignKey('questions.id'))
    answer_text = Column(String)
    is_correct = Column(Boolean)

Base.metadata.create_all(engine)

def add_new_student(name: str, unique_id: str):
    with SessionLocal() as session:
        scene = Student(name=name, unique_id=unique_id)
        session.add(scene)
        session.commit()

def get_student(unique_id:str):
    with SessionLocal() as session:
        print(unique_id)
        user = session.query(Student).filter(Student.unique_id == unique_id).first()
        # if user is None:
        #     return ''
        print(user)
        return user

def add_questions(quiz_data:dict):
    with SessionLocal() as session:
        for question in quiz_data:
            existing_question = session.query(Question).filter(Question.id == question["id"]).first()
            if not existing_question:
                new_question = Question(
                    id=question["id"],
                    text=question["text"],
                    options=json.dumps(question["options"], ensure_ascii=False),
                    correct_answer=question["correct_answer"]
                )
                session.add(new_question)
        session.commit()

def get_all_questions():
    with SessionLocal() as session:
        questions = session.query(Question).all()
        return questions
    
def get_question(question_id):
    with SessionLocal() as session:
        question = session.query(Question).filter(Question.id == question_id).first()
        return question

def add_answer(student_id:str, question_id:str, answer_text:str, is_correct:bool):
    with SessionLocal() as session:
        answer = Answer(student_id=student_id, question_id=question_id, answer_text=answer_text, is_correct=is_correct)
        session.add(answer)
        session.commit()

def get_all_answers(question_id):
    with SessionLocal() as session:
        answers = session.query(Answer).filter(Answer.question_id == question_id).all()
        return answers