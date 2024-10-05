import React, { useEffect, useState } from 'react';
import './StudentQuiz.css'; // Import CSS for styling

const StudentQuiz = ({ studentId }) => {
    const [currentQuestion, setCurrentQuestion] = useState(null);
    const [currentQuestionId, setCurrentQuestionId] = useState(null);
    const [selectedAnswer, setSelectedAnswer] = useState('');

    useEffect(() => {
        const studentSocket = new WebSocket(`ws://62.109.26.235:80/ws/student/${studentId}`);

        studentSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.question) {
                setCurrentQuestion(data.question);
                setCurrentQuestionId(data.question.id);
                setSelectedAnswer('');
            }
        };

        return () => {
            studentSocket.close();
        };
    }, [studentId]);

    const handleAnswerChange = (event) => {
        setSelectedAnswer(event.target.value);
    };

    const handleSubmit = (event) => {
        event.preventDefault();

        if (currentQuestionId === null) {
            alert("No question available");
            return;
        }

        const studentSocket = new WebSocket(`ws://62.109.26.235:80/ws/student/${studentId}`);
        studentSocket.onopen = () => {
            studentSocket.send(JSON.stringify({
                question_id: currentQuestionId,
                answer_text: selectedAnswer
            }));
        };
    };

    return (
        <div className="quiz-container">
            <h1 className="quiz-title">Quiz in Progress</h1>
            {currentQuestion && (
                <div className="question-container">
                    <div className="question-text">{currentQuestion.text}</div>
                    <form id="answerForm" onSubmit={handleSubmit}>
                        <div className="options-container">
                            {currentQuestion.options.map((option, index) => (
                                <label key={index} className="option-label">
                                    <input
                                        type="radio"
                                        name="answer"
                                        value={option.text}
                                        checked={selectedAnswer === option.text}
                                        onChange={handleAnswerChange}
                                        className="option-input"
                                    />
                                    <div className="option-content">
                                        <img src={option.image} alt={option.text} className="option-image" />
                                        <span className="option-text">{option.text}</span>
                                    </div>
                                </label>
                            ))}
                        </div>
                        <button type="submit" className="submit-button">Submit Answer</button>
                    </form>
                </div>
            )}
        </div>
    );
};

export default StudentQuiz;
