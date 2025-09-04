import React, { useState } from 'react';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const submit = () => alert(`Searching for ${query}`);

  const overlayStyle = {
    position: 'absolute',
    top: 10,
    left: '50%',
    transform: 'translateX(-50%)',
    width: 'calc(100% - 20px)',
    maxWidth: 400,
    zIndex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
    pointerEvents: 'none',
  };

  const searchBarStyle = {
    width: '100%',
    display: 'flex',
    gap: '0.5rem',
    pointerEvents: 'auto',
  };

  const inputStyle = {
    flex: 1,
    padding: '0.6rem 1rem',
    border: 'none',
    borderRadius: '1rem',
    boxShadow: '0.063em 0.75em 1.563em rgb(0 0 0 / 78%)',
    background: 'radial-gradient(ellipse at right top,#00458f8f 0%,#151419 45%,#151419 100%)',
    color: '#fff',
    fontFamily: '"Poppins", sans-serif',
  };

  const buttonStyle = {
    padding: '0.6rem 1rem',
    border: 'none',
    borderRadius: '1rem',
    boxShadow: '0.063em 0.75em 1.563em rgb(0 0 0 / 78%)',
    background: '#2eea9d',
    color: '#111',
    cursor: 'pointer',
    fontFamily: '"Poppins", sans-serif',
    pointerEvents: 'auto',
  };

  return (
    <div style={overlayStyle}>
      <div style={searchBarStyle}>
        <input
          style={inputStyle}
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search..."
        />
        <button onClick={submit} style={buttonStyle}>Go</button>
      </div>
    </div>
  );
}