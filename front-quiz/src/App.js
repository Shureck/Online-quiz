import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import RegisterPage from './pages/RegisterPage';
import LoginPage from './pages/LoginPage';
import SurveyPage from './pages/StudentQuizPage';
import TeacherPage from './pages/TeacherPage';
import StudentQuizPage from './pages/StudentQuizPage';

function App() {
  return (
      <Routes>
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/234765964237/teacher" element={<TeacherPage />} />
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="/student/:student_id" element={<StudentQuizPage />} />
      </Routes>
  );
}

export default App;
