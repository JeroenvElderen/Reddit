function SearchBar({
  query,
  onQueryChange,
  closeOpenInfo,
  handleSearchSubmit,
  username,
  setUsername,
  suggestions,
  handleSuggestionClick,
}) {
  return (
    <>
      <div id="search-bar">
        <input
          value={query}
          onChange={e => onQueryChange(e.target.value)}
          onFocus={closeOpenInfo}
          onKeyDown={e => { if (e.key === 'Enter') handleSearchSubmit(); }}
          placeholder="Search for a place"
          className="search-input"
        />
        <input
          value={username}
          onChange={e => setUsername(e.target.value)}
          placeholder="Reddit username"
          className="username-input"
        />
      </div>
      {suggestions.length > 0 && (
        <ul id="suggestions">
          {suggestions.map(p => (
            <li key={p.place_id} onClick={() => handleSuggestionClick(p)}>{p.description}</li>
          ))}
        </ul>
      )}
    </>
  );
}