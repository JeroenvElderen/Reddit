import React, { useState } from 'react';

export default function SearchBar() {
  const [query, setQuery] = useState('');
  const submit = () => alert(`Searching for ${query}`);
  return (
    <div id="overlay">
      <div id="search-bar">
        <input
          className="search-input"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search..."
        />
        <button onClick={submit}>Go</button>
      </div>
    </div>
  );
}