import React, { useEffect, useState } from 'react';
import './TeacherPage.css'; // Import the CSS file

const TeacherPage = () => {
  const [studentActivity, setStudentActivity] = useState([]);
  const [questionStats, setQuestionStats] = useState({});
  const [studentAnswers, setStudentAnswers] = useState({});
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const socket = new WebSocket(`ws://${process.env.REACT_APP_HOST}/ws/teacher`);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'student_activity') {
        setStudentActivity(data.active_students);
      } else if (data.type === 'stats') {
        setQuestionStats(data.all_stats);
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
      setQuestionStats({});
  
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

  return (
    <div className="teacher-container">
      <h2>Панель преподавателя</h2>
  
      <button onClick={handleStartQuiz} className="start-quiz-button">Начать квиз</button>
      <button onClick={handleNextQuestion} className="next-question-button">Следующий вопрос</button>
  
      <div className="quiz-stats">
        <h3>Статистика ответов</h3>
        {Object.keys(questionStats).length > 0 ? (
            <table className="stats-table">
            <thead>
                <tr>
                <th>ID вопроса</th>
                <th>Кол-во правильных ответов</th>
                <th>Кол-во неправильных ответов</th>
                </tr>
            </thead>
            <tbody>
                {Object.entries(questionStats).map(([questionId, { correct, incorrect }]) => (
                <tr key={questionId}>
                    <td>{questionId}</td>
                    <td className="correct-cell">{correct}</td>
                    <td className="incorrect-cell">{incorrect}</td>
                </tr>
                ))}
            </tbody>
            </table>
        ) : (
            <p>No statistics available yet. Start the quiz to see the data.</p>
        )}
      </div>


    </div>
  );
  
};

export default TeacherPage;
