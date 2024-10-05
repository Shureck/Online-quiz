import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import './StudentQuizPage.css';

const StudentQuizPage = () => {
  const { student_id } = useParams();
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [currentAnswer, setCurrentAnswer] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [socket, setSocket] = useState(null);
  const [hasSubmitted, setHasSubmitted] = useState(false); 

  useEffect(() => {
    console.log("Student ID from URL:", student_id);

    const ws = new WebSocket(`ws://${process.env.REACT_APP_HOST}/ws/student/${student_id}`);
    
    ws.onopen = () => {
      console.log('Connected to student WebSocket');
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.question) {
        setCurrentQuestion(data.question);
        setCurrentAnswer(data.answer); // Устанавливаем текущий ответ
        setHasSubmitted(!!data.answer); // Если ответ уже есть, блокируем отправку
        setSelectedAnswer(data.answer || null); // Если ответ уже есть, делаем его выбранным
      }
    };

    ws.onclose = () => {
      console.log('Disconnected from student WebSocket');
    };
    setSocket(ws);

    return () => {
      ws.close();
    };
  }, [student_id]);

  const handleAnswerSubmit = () => {
    if (selectedAnswer && socket && currentQuestion) {
      const answerData = {
        question_id: currentQuestion.id,
        answer_text: selectedAnswer,
        student_id: student_id
      };

      console.log("Submitting answer:", answerData);
      socket.send(JSON.stringify(answerData));
      setHasSubmitted(true); 
    } else {
      console.warn("Cannot submit answer. Missing data:", {
        selectedAnswer,
        socket,
        currentQuestion,
        student_id,
      });
    }
  };

  return (
    <div className="student-page-container">
      <h2>Квиз студента</h2>
      {currentQuestion ? (
        <div className="question-container">
          <p className="question-text">{currentQuestion.text}</p>
          <div className="options">
            {currentQuestion.options.map((option, index) => (
              <label key={index} className={`option-label ${hasSubmitted ? 'disabled' : ''}`}>
                <input
                  type="radio"
                  name={`question-${currentQuestion.id}`}
                  value={option}
                  checked={selectedAnswer === option} // Отмечаем, если совпадает с выбранным
                  onChange={() => setSelectedAnswer(option)}
                  disabled={hasSubmitted} // Делаем неактивным, если уже отправлено
                />
                {option}
              </label>
            ))}
          </div>
          <button
            onClick={handleAnswerSubmit}
            disabled={!selectedAnswer || hasSubmitted} // Делаем кнопку неактивной, если отправлено
            className="submit-button"
          >
            Отправить ответ
          </button>
        </div>
      ) : (
        <p className="waiting-text">Ожидание следующего вопроса...</p>
      )}
    </div>
  );
};

export default StudentQuizPage;

