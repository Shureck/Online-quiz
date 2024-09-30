from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

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
