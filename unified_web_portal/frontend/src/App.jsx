import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import AdminDashboard from './components/AdminDashboard';
import StudentDashboard from './components/StudentDashboard';

const API_BASE_URL = typeof window !== 'undefined' ? window.location.origin : '';

function App() {
  const [token, setToken] = useState(localStorage.getItem('access_token') || '');
  const [role, setRole] = useState(localStorage.getItem('user_role') || '');
  const [name, setName] = useState(localStorage.getItem('user_name') || '');
  const [studentRegNum, setStudentRegNum] = useState(localStorage.getItem('student_reg_number') || '');

  useEffect(() => {
    if (token) {
      localStorage.setItem('access_token', token);
      localStorage.setItem('user_role', role);
      localStorage.setItem('user_name', name);
      localStorage.setItem('student_reg_number', studentRegNum);
    } else {
      localStorage.clear();
    }
  }, [token, role, name, studentRegNum]);

  const handleLogout = () => {
    setToken('');
    setRole('');
    setName('');
    setStudentRegNum('');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Sleek Top Navigation Bar */}
      {token && (
        <header style={{
          borderBottom: '1px solid var(--border-glass)',
          background: 'rgba(9, 13, 22, 0.8)',
          backdropFilter: 'blur(10px)',
          padding: '16px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          position: 'sticky',
          top: 0,
          zIndex: 100
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              color: '#fff',
              fontSize: '18px'
            }}>P</div>
            <div>
              <h1 style={{ fontSize: '18px', fontWeight: '700', letterSpacing: '-0.025em' }}>PROXIMITY ATTENDANCE</h1>
              <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Enterprise Automaton Platform</p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <div style={{ textAlign: 'right' }}>
              <p style={{ fontSize: '14px', fontWeight: '600' }}>{name}</p>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                {role === 'admin' ? 'Campus Admin' : `Student (${studentRegNum})`}
              </p>
            </div>
            <button className="btn-secondary" onClick={handleLogout} style={{ padding: '8px 16px', fontSize: '13px' }}>
              Sign Out
            </button>
          </div>
        </header>
      )}

      {/* Main Workspace Frame */}
      <main style={{ flex: 1, padding: token ? '32px' : '0' }}>
        {!token ? (
          <Login setToken={setToken} setRole={setRole} setName={setName} setStudentRegNum={setStudentRegNum} API_BASE_URL={API_BASE_URL} />
        ) : role === 'admin' ? (
          <AdminDashboard token={token} API_BASE_URL={API_BASE_URL} />
        ) : (
          <StudentDashboard token={token} API_BASE_URL={API_BASE_URL} />
        )}
      </main>
    </div>
  );
}

export default App;
