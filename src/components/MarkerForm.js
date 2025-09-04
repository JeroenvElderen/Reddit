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

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} style={{ position: 'fixed', right: 20, bottom: 20 }}>Add Marker</button>
    );
  }

  return (
    <div id="form-container">
      <form id="marker-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Name"
          value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })}
        />
        <textarea
          placeholder="Description"
          value={form.description}
          onChange={e => setForm({ ...form, description: e.target.value })}
        />
        <button type="submit">Save</button>
        <button type="button" onClick={() => setOpen(false)}>Cancel</button>
      </form>
    </div>
  );
}