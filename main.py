import json
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import random
#from models import Student, Answer, Question
import models
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
def load_questions():
    global quiz_data
    with open("questions.json", "r") as f:
        quiz_data = json.load(f)

    models.add_questions(quiz_data)
    return quiz_data[0]['id']


# Функция для генерации уникального 4-значного кода
def generate_unique_code():
    while True:
        unique_id = ''.join([str(random.randint(0, 9)) for _ in range(4)])
        existing_student = models.get_student(unique_id=unique_id)
        if not existing_student:
            return unique_id

# Маршрут для отображения страницы регистрации студента
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Маршрут для обработки данных регистрации студента
@app.post("/register_student")
async def register_student(name: str = Form(...)):
    # Генерация уникального ID
    unique_id = generate_unique_code()
    models.add_new_student(name=name, unique_id=unique_id)

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
async def teacher_websocket(websocket: WebSocket):
    await websocket.accept()
    teachers_connected.append(websocket)
    
    # Отправка текущего вопроса преподавателю при подключении
    if current_question_index >= 0:
        await send_current_question_to_teacher(websocket)
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
async def send_current_question_to_teacher(websocket: WebSocket):
    question = quiz_data[current_question_index]
    question, stats = await get_answer_stats(current_question_index)
    await websocket.send_json({
        "type": "stats",
        "stats": stats, 
        "question":question
    })

# Отправка текущего вопроса студенту
async def send_current_question_to_student(websocket: WebSocket, student_id:str):
    question = quiz_data[current_question_index]
    answer = models.get_answer(student_id=student_id, question_id=current_question_index)
    ans = None
    if answer != None:
        ans = answer.answer_text
    await websocket.send_json({"question": question, "answer": ans})

# Отправка статистики по ответам преподавателю
# async def send_statistics_to_teacher():
#     # Получаем все ответы
#     answers = models.get_all_answers()
#     stats = {}
#     for answer in answers:
#         if answer.answer_text in stats:
#             stats[answer.answer_text] += 1
#         else:
#             stats[answer.answer_text] = 1

#     # Отправляем статистику учителю
#     for teacher_socket in teachers_connected:  # teachers_connected — это список сокетов учителей
#         await teacher_socket.send_json({"stats": stats})

# Получение статистики ответов по текущему вопросу
async def get_answer_stats(question_id: int):
    answers = models.get_all_answers(question_id=question_id)
    stats = {}
    question = models.get_question(question_id=question_id)
    if question:
        for i in question.options:
            stats[i] = 0
        for answer in answers:
            stats[answer.answer_text] += 1
    
    return question.text, stats

async def send_all_statistics_to_teacher():
    all_stats = {}
    questions = models.get_all_questions()
    for question in questions:
        all_stats[question.id] = await get_answer_stats(question.id)

    print("Sending stats to teacher:", all_stats)  # Debugging line
    for teacher_socket in teachers_connected:
        await teacher_socket.send_json({"type": "stats", "all_stats": all_stats})

async def send_statistics_to_teacher():
    global current_question_index
    question, stats = await get_answer_stats(current_question_index)
    print("Sending stats to teacher:", stats)  # Debugging line
    for teacher_socket in teachers_connected:
        await teacher_socket.send_json({"type": "stats", "stats": stats, "question":question})

# Update this line in the student_websocket method where you call send_statistics_to_teacher


# Запуск квиза
# Start the quiz and reset stats
@app.post("/start_quiz")
async def start_quiz():
    global current_question_index

    # Reset the current question index and load questions again
    current_question_index = load_questions()
    # Notify connected students about the start of a new quiz
    await send_question_to_students()
    # Notify connected teachers with empty stats
    await send_statistics_to_teacher()

    return {"message": "Quiz started"}


# Следующий вопрос
@app.post("/next_question")
async def next_question():
    global current_question_index
    current_question_index += 1
    await send_question_to_students()
    await send_statistics_to_teacher()
    return {"message": "Next question sent"}

@app.websocket("/ws/student/{student_id}")
async def student_websocket(websocket: WebSocket, student_id: str):
    await websocket.accept()
    students_connected.append(websocket)

    if current_question_index >= 0:
        await send_current_question_to_student(websocket, student_id)

    try:
        while True:
            data = await websocket.receive_json()
            question_id = data.get("question_id")
            answer_text = data.get("answer_text")

            student = models.get_student(unique_id=student_id)
            if student:
                tr = quiz_data[question_id]['correct_answer'] == answer_text
                models.add_answer(student_id=student.id, question_id=question_id, answer_text=answer_text, is_correct=tr)
                # Send updated stats after each answer
                await send_statistics_to_teacher()
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




