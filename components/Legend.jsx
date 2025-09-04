function Legend({
  legendOpen,
  filter,
  toggleFilter,
  icons,
  countries,
  countryFilter,
  setCountryFilter,
}) {
  return (
    <div id="legend" className={legendOpen ? '' : 'hidden'}>
      {['official','restricted','unofficial','illegal','secluded'].map(cat => (
        <label key={cat} className="legend-item">
          <input
            type="checkbox"
            checked={filter[cat]}
            onChange={() => toggleFilter(cat)}
          />
          <span className={`legend-marker ${cat}`}>{icons[cat]}</span>
          {cat}
        </label>
      ))}
      {countries.length > 0 && (
        <select
          className="country-select"
          value={countryFilter}
          onChange={e => setCountryFilter(e.target.value)}
        >
          <option value="All">All countries</option>
          {countries.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      )}
    </div>
  );
}
