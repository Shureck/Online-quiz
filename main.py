import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import random
from sqlalchemy.orm import Session
from models import Student, Answer, Question
from database import get_db, engine
from models import Base

# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return student_id

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
    stats = {'correct': 0, 'incorrect': 0}
    
    # Assuming you have a way to determine the correct answer
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        correct_answer = question.correct_answer

        for answer in answers:
            if answer.is_correct == True:
                stats['correct'] += 1
            else:
                stats['incorrect'] += 1
    
    return stats

async def send_all_statistics_to_teacher(db: Session):
    all_stats = {}
    questions = db.query(Question).all()
    
    for question in questions:
        all_stats[question.id] = await get_answer_stats(question.id, db)
    
    print("Sending stats to teacher:", all_stats)  # Debugging line
    
    for teacher_socket in teachers_connected:
        await teacher_socket.send_json({"type": "stats", "all_stats": all_stats})

# Update this line in the student_websocket method where you call send_statistics_to_teacher


# Запуск квиза
# Start the quiz and reset stats
@app.post("/start_quiz")
async def start_quiz(db: Session = Depends(get_db)):
    global current_question_index

    # Reset the current question index and load questions again
    current_question_index = 0
    load_questions(db)

    # Clear previous answers from the database (optional if you want a fresh start)
    db.query(Answer).delete()
    db.commit()

    # Notify connected students about the start of a new quiz
    await send_question_to_students()

    # Notify connected teachers with empty stats
    await send_all_statistics_to_teacher(db)

    return {"message": "Quiz started"}


# Следующий вопрос
@app.post("/next_question")
async def next_question():
    global current_question_index
    current_question_index += 1
    await send_question_to_students()
    return {"message": "Next question sent"}

@app.websocket("/ws/student/{student_id}")
async def student_websocket(websocket: WebSocket, student_id: str, db: Session = Depends(get_db)):
    await websocket.accept()
    students_connected.append(websocket)

    if current_question_index >= 0:
        await send_current_question_to_student(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            question_id = data.get("question_id")
            answer_text = data.get("answer_text")

            student = db.query(Student).filter(Student.unique_id == student_id).first()
            if student:
                tr = quiz_data[question_id-1]['correct_answer'] == answer_text
                print(question_id-1, quiz_data[question_id-1]['correct_answer'], answer_text,quiz_data[question_id-1]['correct_answer'] == answer_text)
                answer = Answer(student_id=student.id, question_id=question_id, answer_text=answer_text, is_correct=quiz_data[question_id-1]['correct_answer'] == answer_text)
                db.add(answer)
                db.commit()

                # Send updated stats after each answer
                await send_all_statistics_to_teacher(db)
            else:
                print(f"Student with ID {student_id} not found.")

    except WebSocketDisconnect:
        print(f"Student {student_id} disconnected.")
        students_connected.remove(websocket)
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()

    except WebSocketDisconnect:
        print(f"Student {student_id} disconnected.")
        students_connected.remove(websocket)
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()




