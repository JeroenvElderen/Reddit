const { useState, useEffect, useRef } = React;
const sb = (typeof SUPABASE_URL !== 'undefined' && typeof SUPABASE_ANON_KEY !== 'undefined')
  ? supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;


function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [category, setCategory] = useState('unofficial');

  useEffect(() => {
    if (typeof MAPBOX_TOKEN === 'undefined' || !MAPBOX_TOKEN) {
      alert('MAPBOX_TOKEN missing in config.js');
      return;
    }
    // Warn if an older version of Mapbox GL JS is loaded
    const major = parseInt(mapboxgl.version.replace(/^v/, '').split('.')[0], 10);
    if (Number.isNaN(major) || major < 2) {
      alert('Mapbox GL JS v2 or higher is required for this style.');
      return;
    }
    mapboxgl.accessToken = MAPBOX_TOKEN;
    mapRef.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [0,0],
      zoom: 1.5,
      projection: 'globe'
    });

    mapRef.current.on('click', async (e) => {
      const coords = [e.lngLat.lng, e.lngLat.lat];
      const nameInput = prompt('Location name?');
      if (nameInput === null) return; // cancelled
      const countryInput = prompt('Country?');
      if (countryInput === null) return; // cancelled
      const category = prompt('Category (allowed/restricted/unofficial/illegal)?') || 'unofficial';
      const name = nameInput.trim() || 'Unnamed';
      const country = countryInput.trim();
      if (!country) return; // need country for law lookup
      await addMarker({ name, country, category, coordinates: coords });
    });
    if (sb) {
        (async () => {
        const { data, error } = await sb.from('map_markers').select('*');
        if (!error && data) {
          data.forEach(renderMarker);
        } else {
          console.error('Error loading markers', error);
        }
      })();
    }
  }, []);

  const categoryColor = (cat) => ({
    allowed: 'green',
    restricted: 'yellow',
    unofficial: 'blue',
    illegal: 'red'
  })[cat.toLowerCase()] || 'gray';

  const geocode = async(name, country) => {
    const q = encodeURIComponent(`${name} ${country}`);
    const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${q}.json?access_token=${MAPBOX_TOKEN}`;
    const res = await fetch(url);
    const data = await res.json();
    return data.features[0].center;
  };

  const searchPlaces = async (q) => {
    if (!q) {
      setSuggestions([]);
      return;
    }
    const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(q)}.json?autocomplete=true&limit=5&access_token=${MAPBOX_TOKEN}`;
    const res = await fetch(url);
    const data = await res.json();
    setSuggestions(data.features || []);
  };

  const fetchLaw = async (country) => {
    try {
      const res = await fetch(`https://restcountries.com/v3.1/name/${encodeURIComponent(country)}?fields=region`);
      const data = await res.json();
      return data[0] ? `Region: ${data[0].region}` : 'No data';
    } catch (e) {
      return 'Law data unavailable';
    }
  };

  const logDiscord = (msg) => {
    if (typeof DISCORD_WEBHOOK_URL === 'string' && DISCORD_WEBHOOK_URL) {
      fetch(DISCORD_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: msg })
      });
    }
  };

  const renderMarker = ({ name, country, category, coordinates, law }) => {
    const marker = new mapboxgl.Marker({ color: categoryColor(category) })
      .setLngLat(coordinates)
      .setPopup(
        new mapboxgl.Popup().setHTML(
          `<h3>${name}</h3><p>${country}</p><p>${category}</p><p>${law}</p>`
        )
      );

    // Prevent map click handler from firing when a marker is clicked
    marker.getElement().addEventListener('click', (e) => {
      e.stopPropagation();
    });

    marker.addTo(mapRef.current);
  };

  const addMarker = async ({ name = 'Unnamed', country, category, coordinates }) => {
    try {
      const coords = coordinates || await geocode(name, country);
      const law = country ? await fetchLaw(country) : 'No data';
      renderMarker({ name, country, category, coordinates: coords, law });
      logDiscord(`New marker: ${name}, ${country}, ${category}`);
      if (sb) {
        const { error } = await sb.from('map_markers').insert({ name, country, category, coordinates: coords, law });
        if (error) {
          console.error('Supabase insert error', error);
        }
      }
    } catch (err) {
      console.error('Error adding marker', err);
    }
  };

  const handleSuggestionClick = async (feature) => {
    setQuery('');
    setSuggestions([]);
    const countryFeature = feature.context?.find(c => c.id.startsWith('country'));
    const country = countryFeature ? countryFeature.text : '';
    await addMarker({ name: feature.text, country, category, coordinates: feature.center });
  };

  return (
    <>
      <div id="map" ref={mapContainer}></div>
      <div id="overlay">
        <h1>Legal Map</h1>
         <input
          value={query}
          onChange={e => { setQuery(e.target.value); searchPlaces(e.target.value); }}
          placeholder="Search for a place"
        />
        <select value={category} onChange={e => setCategory(e.target.value)}>
          <option value="allowed">allowed</option>
          <option value="restricted">restricted</option>
          <option value="unofficial">unofficial</option>
          <option value="illegal">illegal</option>
        </select>
        {suggestions.length > 0 && (
          <ul id="suggestions">
            {suggestions.map(f => (
              <li key={f.id} onClick={() => handleSuggestionClick(f)}>{f.place_name}</li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);