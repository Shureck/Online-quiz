import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './RegisterPage.css'; // Подключаем файл стилей

const RegisterPage = () => {
    const [name, setName] = useState('');
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleRegister = async (e) => {
        e.preventDefault();
    
        try {
            const response = await axios.post(`http://${process.env.REACT_APP_HOST}/register_student`, 
                new URLSearchParams({
                    name: name
                }), 
                {
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }
                }
            ).then((response) => {
                console.log(response);
                const studentID = response.data; // Извлекаем ID студента из URL
                navigate(`/student/${studentID}`); // Перенаправление на страницу студента
              });
    
            // Проверка на 303 статус для редиректа
            if (response.status === 303) {
                const location = response.headers['location']; // Headers might be lowercase
                console.log(location);
                const studentID = location.split('/').pop(); // Извлекаем ID студента из URL
                navigate(`/student/${studentID}`); // Перенаправление на страницу студента
            } else {
                setError('Unexpected response status.');
            }
        } catch (error) {
            setError('Регистрация не удалась. Пожалуйста, попробуйте еще раз.');
            console.error("Registration error:", error); // Логирование ошибок для диагностики
        }
    };

    return (
        <div className="register-container">
            <h2>Регистрация</h2>
            <form onSubmit={handleRegister} className="register-form">
                <div className="form-group">
                    <label htmlFor="name">Полное имя:</label>
                    <input
                        type="text"
                        id="name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        className="input-field"
                    />
                </div>
                {error && <p className="error-message">{error}</p>}
                <button type="submit" className="register-button">Зарегистрироваться</button>
                <button className="switch-button" onClick={() => navigate('/login')}>
                    Уже есть аккаунт? Войдите
                </button>
            </form>
        </div>
    );
};

export default RegisterPage;
