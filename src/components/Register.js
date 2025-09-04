import React, { useState } from 'react';

export default function Register({ onBack, onLogin, supabase }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async e => {
    e.preventDefault();
    if (supabase) {
      await supabase.auth.signUp({ email, password });
    }
    onBack();
  };

  return (
    <div id="auth-container">
      <div className="auth-card">
        <h2>Register</h2>
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>
          <div className="input-group">
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>
          <button type="submit">Create</button>
          <button type="button" onClick={onBack}>Back</button>
          <div className="switch">
            <button type="button" onClick={onLogin}>Login</button>
          </div>
        </form>
      </div>
    </div>
  );
}