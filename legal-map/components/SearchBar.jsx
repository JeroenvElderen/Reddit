function SearchBar({
  query,
  onQueryChange,
  closeOpenInfo,
  handleSearchSubmit,
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