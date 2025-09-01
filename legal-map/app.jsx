const { useState, useEffect, useRef } = React;
const sb = (typeof SUPABASE_URL !== 'undefined' && typeof SUPABASE_ANON_KEY !== 'undefined')
  ? supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;


function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const geocoderRef = useRef(null);
  const autocompleteRef = useRef(null);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [category, setCategory] = useState('unofficial');

  useEffect(() => {
    if (typeof GOOGLE_MAPS_API_KEY === 'undefined' || !GOOGLE_MAPS_API_KEY) {
      alert('GOOGLE_MAPS_API_KEY missing in config.js');
      return;
    }
    
    const init = () => {
      mapRef.current = new google.maps.Map(mapContainer.current, {
        center: { lat: 0, lng: 0 },
        zoom: 2,
      });

      geocoderRef.current = new google.maps.Geocoder();
      autocompleteRef.current = new google.maps.places.AutocompleteService();

      mapRef.current.addListener('click', async (e) => {
        const coords = [e.latLng.lng(), e.latLng.lat()];
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
    };

    if (window.google && window.google.maps) {
      init();
    } else {
      const script = document.createElement('script');
      script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places`;
      script.onload = init;
      document.head.appendChild(script);
    }
  }, []);

  const categoryColor = (cat) => ({
    allowed: 'green',
    restricted: 'yellow',
    unofficial: 'blue',
    illegal: 'red'
  })[cat.toLowerCase()] || 'gray';

  const geocode = (name, country) => new Promise((resolve, reject) => {
    if (!geocoderRef.current) return reject('Geocoder not loaded');
    geocoderRef.current.geocode({ address: `${name} ${country}` }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        resolve([loc.lng(), loc.lat()]);
      } else {
        reject(status);
      }
    });
  });

  const searchPlaces = (q) => {
    if (!q || !autocompleteRef.current) {
      setSuggestions([]);
      return;
    }
    autocompleteRef.current.getPlacePredictions({ input: q }, (preds) => {
      setSuggestions(preds || []);
    });
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
    const pos = Array.isArray(coordinates)
      ? { lat: coordinates[1], lng: coordinates[0] }
      : coordinates;
    const marker = new google.maps.Marker({
      position: pos,
      map: mapRef.current,
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        fillColor: categoryColor(category),
        fillOpacity: 1,
        strokeWeight: 0,
        scale: 6,
      }
    });

    const info = new google.maps.InfoWindow({
      content: `<h3>${name}</h3><p>${country}</p><p>${category}</p><p>${law}</p>`
    });
    marker.addListener('click', () => info.open(mapRef.current, marker));
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

  const handleSuggestionClick = async (prediction) => {
    setQuery('');
    setSuggestions([]);
    if (!geocoderRef.current) return;
    geocoderRef.current.geocode({ placeId: prediction.place_id }, async (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        const countryComp = results[0].address_components.find(c => c.types.includes('country'));
        const country = countryComp ? countryComp.long_name : '';
        await addMarker({
          name: prediction.description,
          country,
          category,
          coordinates: [loc.lng(), loc.lat()]
        });
      }
    });
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
            {suggestions.map(p => (
                <li key={p.place_id} onClick={() => handleSuggestionClick(p)}>{p.description}</li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);