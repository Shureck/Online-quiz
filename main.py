import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
import random
from sqlalchemy.orm import Session
from models import Student, Answer, Question
from database import get_db, engine
from models import Base

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Глобальные переменные
quiz_data = []
current_question_index = -1
students_connected = []
teachers_connected = []

# Загрузка вопросов из JSON файла
def load_questions(db: Session):
    global quiz_data
    with open("questions.json", "r") as f:
        quiz_data = json.load(f)
    
    # Добавляем вопросы в базу данных, если их там нет
    for question in quiz_data:
        existing_question = db.query(Question).filter(Question.id == question["id"]).first()
        if not existing_question:
            new_question = Question(
                id=question["id"],
                text=question["text"],
                options=json.dumps(question["options"]),
                correct_answer=question["correct_answer"]
            )
            db.add(new_question)
    db.commit()

# Функция для генерации уникального 4-значного кода
def generate_unique_code(db: Session):
    while True:
        unique_id = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        existing_student = db.query(Student).filter(Student.unique_id == unique_id).first()
        if not existing_student:
            return unique_id

# Маршрут для отображения страницы регистрации студента
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Маршрут для обработки данных регистрации студента
@app.post("/register_student")
async def register_student(name: str = Form(...), db: Session = Depends(get_db)):
    # Генерация уникального ID
    unique_id = generate_unique_code(db)

    # Сохранение студента в БД
    student = Student(name=name, unique_id=unique_id)
    db.add(student)
    db.commit()

    # Редирект на страницу с квизом
    return RedirectResponse(f"/student/{unique_id}", status_code=303)

# Маршрут для страницы преподавателя
@app.get("/", response_class=HTMLResponse)
async def teacher_page(request: Request):
    return templates.TemplateResponse("teacher.html", {"request": request})

# Маршрут для страницы студента
@app.get("/student/{student_id}", response_class=HTMLResponse)
async def student_page(request: Request, student_id: str):
    return templates.TemplateResponse("student_quiz.html", {"request": request, "student_id": student_id})

# WebSocket для преподавателя
@app.websocket("/ws/teacher")
async def teacher_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    teachers_connected.append(websocket)

    # Отправка текущего вопроса преподавателю при подключении
    if current_question_index >= 0:
        await send_current_question_to_teacher(websocket, db)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        teachers_connected.remove(websocket)

# Отправка текущего вопроса студентам
async def send_question_to_students():
    global current_question_index
    question = quiz_data[current_question_index]
    for student in students_connected:
        await student.send_json({"question": question})

# Отправка текущего вопроса преподавателю
async def send_current_question_to_teacher(websocket: WebSocket, db: Session):
    question = quiz_data[current_question_index]
    await websocket.send_json({
        "question": question,
        "stats": await get_answer_stats(current_question_index, db)
    })

# Отправка текущего вопроса студенту
async def send_current_question_to_student(websocket: WebSocket):
    question = quiz_data[current_question_index]
    await websocket.send_json({"question": question})

# Отправка статистики по ответам преподавателю
async def send_statistics_to_teacher(db: Session):
    # Получаем все ответы
    answers = db.query(Answer).all()

    # Собираем статистику ответов
    stats = {}
    for answer in answers:
        if answer.answer_text in stats:
            stats[answer.answer_text] += 1
        else:
            stats[answer.answer_text] = 1

    # Отправляем статистику учителю
    for teacher_socket in teachers_connected:  # teachers_connected — это список сокетов учителей
        await teacher_socket.send_json({"stats": stats})


# Получение статистики ответов по текущему вопросу
async def get_answer_stats(question_id: int, db: Session):
    answers = db.query(Answer).filter(Answer.question_id == question_id).all()
    stats = {}
    for answer in answers:
        if answer.answer_text in stats:
            stats[answer.answer_text] += 1
        else:
            stats[answer.answer_text] = 1
    return stats

# Запуск квиза
@app.post("/start_quiz")
async def start_quiz(db: Session = Depends(get_db)):
    global current_question_index
    load_questions(db)
    current_question_index = 0
    await send_question_to_students()
    return {"message": "Quiz started"}

# Следующий вопрос
@app.post("/next_question")
async def next_question():
    global current_question_index
    current_question_index += 1
    await send_question_to_students()
    return {"message": "Next question sent"}

@ app.websocket("/ws/student/{student_id}")
async def student_websocket(websocket: WebSocket, student_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    students_connected.append(websocket)
    
    # Отправляем текущий вопрос студенту при подключении, если квиз идет
    if current_question_index >= 0:
        await send_current_question_to_student(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            question_id = data.get("question_id")
            answer_text = data.get("answer_text")

            # Сохранение ответа студента в БД
            student = db.query(Student).filter(Student.unique_id == student_id).first()
            answer = Answer(student_id=student.id, question_id=question_id, answer_text=answer_text)
            db.add(answer)
            db.commit()

            # Отправка обновленной статистики преподавателю
            await send_statistics_to_teacher(db)
    except WebSocketDisconnect:
        students_connected.remove(websocket)

