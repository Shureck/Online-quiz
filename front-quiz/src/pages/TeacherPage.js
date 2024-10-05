import React, { useEffect, useState } from 'react';
import './TeacherPage.css'; // Import the CSS file
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const TeacherPage = () => {
  const [studentActivity, setStudentActivity] = useState([]);
  const [questionStats, setQuestionStats] = useState({});
  const [questionText, setQuestionText] = useState({});
  const [studentAnswers, setStudentAnswers] = useState({});
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const socket = new WebSocket(`ws://${process.env.REACT_APP_HOST}/ws/teacher`);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'student_activity') {
        setStudentActivity(data.active_students);
      } else if (data.type === 'stats') {
        setQuestionStats(data.stats);
        setQuestionText(data.question);
      } else if (data.type === 'student_answer') {
        const { student_id, answer_text, question_id } = data;
        setStudentAnswers((prev) => ({
          ...prev,
          [student_id]: {
            answer_text,
            question_id,
          },
        }));
      }
    };

    setSocket(socket);

    return () => {
      socket.close();
    };
  }, []);

  const handleStartQuiz = async () => {
    try {
      const response = await fetch(`http://${process.env.REACT_APP_HOST}/start_quiz`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
  
      if (!response.ok) {
        throw new Error('Failed to start quiz');
      }
  
      const result = await response.json();
      console.log(result.message);
  
      // Reset the questionStats to an empty object when the quiz starts
      // setQuestionStats({});
  
    } catch (error) {
      console.error(error);
    }
  };
  

  const handleNextQuestion = async () => {
    try {
      const response = await fetch(`http://${process.env.REACT_APP_HOST}/next_question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to send next question');
      }

      const result = await response.json();
      console.log(result.message);
    } catch (error) {
      console.error(error);
    }
  };

  const labels = Object.keys(questionStats);  // Варианты ответов
  const data = Object.values(questionStats);  // Количество ответов
  
  // Данные для диаграммы
  const chartData = {
    labels: labels,
    datasets: [
      {
        label: 'Количество ответов',
        data: data,
        backgroundColor: ['rgba(75, 192, 192, 0.2)'],
        borderColor: ['rgba(75, 192, 192, 1)'],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Статистика ответов',
      },
    },
  };

  return (
    <div className="teacher-container">
      <h2>Панель преподавателя</h2>

      <button onClick={handleStartQuiz} className="start-quiz-button">Начать квиз</button>
      <button onClick={handleNextQuestion} className="next-question-button">Следующий вопрос</button>

      <div className="quiz-stats">
        {typeof questionText === 'string' && questionText.length > 0 ? (
          <>
            <h3>{questionText}</h3>
            {Object.keys(questionStats).length > 0 ? (
              <Bar data={chartData} options={options} />
            ) : (
              <p>No statistics available yet. Start the quiz to see the data.</p>
            )}
          </>
        ) : (
          <p>Вопрос ещё не загружен. Пожалуйста, подождите.</p>
        )}
      </div>
    </div>
  );
  
};

export default TeacherPage;
