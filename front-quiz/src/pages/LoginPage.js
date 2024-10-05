import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './LoginPage.css'; // Подключаем файл стилей

const LoginPage = () => {
  const [studentID, setStudentID] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      // Проверка, существует ли студент по уникальному ID
      const response = await axios.get(`http://${process.env.REACT_APP_HOST}/student/${studentID}`);
      
      if (response.status === 200) {
        // Перенаправление студента на страницу опроса или профиля
        navigate(`/student/${studentID}`);
      }
    } catch (error) {
      setError('Неправильный ID студента. Попробуйте еще раз.');
    }
  };

  return (
    <div className="login-container">
      <h2>Вход</h2>
      <form onSubmit={handleLogin} className="login-form">
        <div className="form-group">
          <label htmlFor="studentID">Введите ваш ID студента:</label>
          <input
            type="text"
            id="studentID"
            value={studentID}
            onChange={(e) => setStudentID(e.target.value)}
            required
            className="input-field"
          />
        </div>
        {error && <p className="error-message">{error}</p>}
        <button type="submit" className="login-button">Войти</button>
        <button className="switch-button" onClick={() => navigate('/register')}>
          Нет аккаунта? Зарегистрируйтесь
        </button>
      </form>
    </div>
  );
};

export default LoginPage;
