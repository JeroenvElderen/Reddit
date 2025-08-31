const { useState, useEffect, useRef } = React;

function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const [input, setInput] = useState("");

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
      style: 'mapbox://styles/jeroenvanelderen/cmc958dgm006s01shdiu103uz',
      center: [0,0],
      zoom: 1.5,
      projection: 'globe'
    });

    mapRef.current.on('click', async (e) => {
      const name = prompt('Location name?');
      const country = prompt('Country?');
      const category = prompt('Category (allowed/restricted/unofficial/illegal)?');
      if (name && country && category) {
        await addMarker({ name, country, category, coordinates: [e.lngLat.lng, e.lngLat.lat] });
      }
    });

    fetch('markers.json')
      .then(res => res.json())
      .then(data => data.forEach(renderMarker))
      .catch(()=>{});
  }, []);

  const categoryColor = (cat) => ({
    allowed: 'green',
    restricted: 'yellow',
    unofficial: 'blue',
    illegal: 'red'
  })[cat.toLowerCase()] || 'gray';

  const geocode = async (name, country, coords) => {
    if (coords) return coords;
    const q = encodeURIComponent(`${name} ${country}`);
    const url = `https://api.mapbox.com/geocoding/v5/mapbox.places/${q}.json?access_token=${MAPBOX_TOKEN}`;
    const res = await fetch(url);
    const data = await res.json();
    return data.features[0].center;
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
    new mapboxgl.Marker({ color: categoryColor(category) })
      .setLngLat(coordinates)
      .setPopup(new mapboxgl.Popup().setHTML(`<h3>${name}</h3><p>${country}</p><p>${category}</p><p>${law}</p>`))
      .addTo(mapRef.current);
  };

  const addMarker = async ({ name, country, category, coordinates }) => {
    try {
      const coords = await geocode(name, country, coordinates);
      const law = await fetchLaw(country);
      renderMarker({ name, country, category, coordinates: coords, law });
      logDiscord(`New marker: ${name}, ${country}, ${category}`);
    } catch (err) {
      console.error('Error adding marker', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const [name, country, category='unofficial'] = input.split(',').map(s => s.trim());
    if (name && country) {
      await addMarker({ name, country, category, coordinates: null });
      setInput('');
    }
  };

  return (
    <div>
      <h1>Legal Map</h1>
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={e=>setInput(e.target.value)} placeholder="Name, Country, Category" />
        <button type="submit">Add via Bot</button>
      </form>
      <div id="map" ref={mapContainer}></div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);