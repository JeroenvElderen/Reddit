import React, { useState } from 'react';

export default function MarkerForm() {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });

  const handleSubmit = e => {
    e.preventDefault();
    alert(`Marker submitted: ${form.name}`);
    setForm({ name: '', description: '' });
    setOpen(false);
  };

  const formContainerStyle = {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    zIndex: 3,
  };

  const formStyle = {
    width: '400px',
    maxWidth: '90vw',
    padding: '12px',
    boxSizing: 'border-box',
  };

  const fieldStyle = {
    display: 'block',
    width: '100%',
    boxSizing: 'border-box',
    margin: '8px 0',
    padding: '1rem 1rem',
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
    boxSizing: 'border-box',
  };

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} style={{ position: 'fixed', right: 20, bottom: 20 }}>Add Marker</button>
    );
  }

  return (
    <div style={formContainerStyle}>
      <form style={formStyle} onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Name"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
          style={fieldStyle}
        />
        <textarea
          placeholder="Description"
          value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })}
          style={fieldStyle}
        />
        <button type="submit" style={buttonStyle}>Save</button>
        <button type="button" onClick={() => setOpen(false)} style={buttonStyle}>Cancel</button>
      </form>
    </div>
  );
}