import React, { useState } from 'react';

export default function Login({ onBack, onRegister, supabase }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async e => {
    e.preventDefault();
    if (supabase) {
      await supabase.auth.signInWithPassword({ email, password });
    }
    onBack();
  };

  const containerStyle = {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    zIndex: 3,
  };

  const cardStyle = {
    background: 'radial-gradient(ellipse at right top,#00458f8f 0%,#151419 45%,#151419 100%)',
    color: '#fff',
    padding: '1rem 1.5rem',
    borderRadius: '1rem',
    boxShadow: '0.063em 0.75em 1.563em rgb(0 0 0 / 78%)',
    fontFamily: '"Poppins", sans-serif',
  };

  const groupStyle = { margin: '0.5rem 0' };

  const inputStyle = {
    width: '100%',
    padding: '0.6rem 1rem',
    border: 'none',
    borderRadius: '1rem',
    background: 'rgba(34,33,39,0.5)',
    color: '#fff',
    fontFamily: '"Poppins", sans-serif',
  };

  const buttonStyle = {
    display: 'block',
    width: '100%',
    margin: '8px 0',
    padding: '0.6rem 1rem',
    border: 'none',
    borderRadius: '1rem',
    background: '#2eea9d',
    color: '#111',
    cursor: 'pointer',
    fontFamily: '"Poppins", sans-serif',
  };

  const switchStyle = {
    marginTop: '0.5rem',
    display: 'flex',
    justifyContent: 'space-between',
  };

  return (
    <div style ={containerStyle}>
      <div style={cardStyle}>
        <h2>Login</h2>
        <form onSubmit={handleSubmit}>
          <div style={groupStyle}>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={groupStyle}>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={inputStyle}
            />
          </div>
          <button type="submit" style={buttonStyle}>Login</button>
          <button type="button" onClick={onBack} style={buttonStyle}>Back</button>
          <div style={switchStyle}>
            <button type="button" onClick={onRegister} style={{ ...buttonStyle, width: 'auto', margin: 0 }}>Register</button>
          </div>
        </form>
      </div>
    </div>
  );
}