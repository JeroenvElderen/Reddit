const { useState, useEffect, useRef } = React;
const sb = (typeof SUPABASE_URL !== 'undefined' && typeof SUPABASE_ANON_KEY !== 'undefined')
  ? supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  : null;


function App() {
  const mapContainer = useRef(null);
  const mapRef = useRef(null);
  const geocoderRef = useRef(null);
  const autocompleteRef = useRef(null);
  const openInfoRef = useRef(null);
  const markersRef = useRef([]);
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [category, setCategory] = useState('unofficial');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', country: '', description: '' });
  const [pendingCoords, setPendingCoords] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [filter, setFilter] = useState({
    official: true,
    restricted: true,
    unofficial: true,
    illegal: true
  });
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [legendOpen, setLegendOpen] = useState(window.innerWidth >= 768);

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    setLegendOpen(!isMobile);
  }, [isMobile]);

  const closeOpenInfo = () => {
    if (openInfoRef.current) {
      openInfoRef.current.close();
      openInfoRef.current = null;
    }
  };

  useEffect(() => {
    window.addEventListener('scroll', closeOpenInfo);
    if (typeof GOOGLE_MAPS_API_KEY === 'undefined' || !GOOGLE_MAPS_API_KEY) {
      alert('GOOGLE_MAPS_API_KEY missing in config.js');
      return;
    }
    if (typeof MAP_ID === 'undefined' || !MAP_ID) {
      alert('MAP_ID missing in config.js');
      return;
    }
    
    const init = () => {
      mapRef.current = new google.maps.Map(mapContainer.current, {
        center: { lat: 0, lng: 0 },
        zoom: 2,
        minZoom: 4,
        mapId: MAP_ID,
        mapTypeControl: false,
        streetViewControl: false,
        rotateControl: false,
        tilt: 67.5,
        restriction: {
          latLngBounds: {
            north: 85,
            south: -85,
            west: -180,
            east: 180
          },
          strictBounds: true
        }
      });

      geocoderRef.current = new google.maps.Geocoder();
      autocompleteRef.current = new google.maps.places.AutocompleteService();

      mapRef.current.addListener('dragstart', closeOpenInfo);
      mapRef.current.addListener('zoom_changed', closeOpenInfo);

      mapRef.current.addListener('click', (e) => {
        closeOpenInfo();
        const coords = [e.latLng.lng(), e.latLng.lat()];
        setPendingCoords(coords);
        setEditingId(null);
        if (geocoderRef.current) {
          geocoderRef.current.geocode({ location: e.latLng }, (results, status) => {
            if (status === 'OK' && results[0]) {
              const res = results[0];
              const countryComp = res.address_components.find(c => c.types.includes('country'));
              const country = countryComp ? countryComp.long_name : '';
              const poiComp = res.address_components.find(c => c.types.includes('point_of_interest'))
                || res.address_components.find(c => c.types.includes('establishment'));
              const name = poiComp ? poiComp.long_name : res.formatted_address;
              setFormData({ name, country, description: '' });
            } else {
              setFormData({ name: '', country: '', description: '' });
            }
            setShowForm(true);
          });
        } else {
          setFormData({ name: '', country: '', description: '' });
          setShowForm(true);
        }
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
      script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places,marker`;
      script.onload = init;
      document.head.appendChild(script);
    }
    return () => {
      window.removeEventListener('scroll', closeOpenInfo);
    };
  }, []);

  const categoryColor = (cat) => ({
    official: '#2eea9d',   // green accent from .card.green
    restricted: '#ffd84d',// yellow accent from .card.yellow
    unofficial: '#5a81ff',// blue accent from .card.blue
    illegal: '#fe6c9b'    // red accent from .card.red
  })[cat.toLowerCase()] || '#888'; // fallback gray

  const icons = {
    official: '✓',
    restricted: '!',
    unofficial: 'i',
    illegal: '✖'
  };

  const toggleFilter = (cat) => {
    setFilter(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  useEffect(() => {
    markersRef.current.forEach(({ marker, category }) => {
      marker.map = filter[category] ? mapRef.current : null;
    });
  }, [filter]);


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

  const logDiscord = (msg) => {
    if (typeof DISCORD_WEBHOOK_URL === 'string' && DISCORD_WEBHOOK_URL) {
      fetch(DISCORD_WEBHOOK_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: msg })
      });
    }
  };

  const renderMarker = ({ id, name, country, category, coordinates, description, law }) => {
    const pos = Array.isArray(coordinates)
      ? { lat: coordinates[1], lng: coordinates[0] }
      : coordinates;
    const coordsArr = Array.isArray(coordinates)
      ? coordinates
      : [coordinates.lng, coordinates.lat];
    const markerId = id ?? Date.now() + Math.random();

    const cat = (category || '').toLowerCase();
    const pin = new google.maps.marker.PinElement({
      background: categoryColor(category),
      borderColor: 'white',
      glyph: icons[cat] || '',
      glyphColor: 'black',
    });
    const marker = new google.maps.marker.AdvancedMarkerElement({
      position: pos,
      map: mapRef.current,
      content: pin.element,
    });
    markersRef.current.push({ marker, category: cat, id: markerId});
    marker.map = filter[cat] ? mapRef.current : null;
      
    const text = description || law || '';

    const colorClass = {
      official: 'green',
      restricted: 'yellow',
      unofficial: 'blue',
      illegal: 'red'
    }[cat] || 'blue';
    const content = document.createElement('div');
    content.className = `card ${colorClass}`;
    content.innerHTML = `
        <div class="card-body">
          <div>
          <h3>${name}</h3>
          <p>${country}</p>
          <p>${category}</p>
          <p>${text}</p>
          <button class="edit-marker">Edit Marker</button>
          <button onclick="window.open('https://www.google.com/maps?q=${pos.lat},${pos.lng}', '_blank')">View on Google Maps</button>
        </div>
      </div>`;

    const info = new google.maps.InfoWindow({ content });
    info.addListener('domready', () => {
      const iw = document.querySelector('.gm-style-iw');
      if (iw) {
        iw.style.maxWidth = 'none';
        iw.style.width = 'auto';
      }
      const iwd = document.querySelector('.gm-style-iw-d');
      if (iwd) {
        iwd.style.overflow = 'visible';
        iwd.style.maxWidth = 'none';
        iwd.style.width = 'auto';
      }
    });
    content.addEventListener('click', closeOpenInfo);
    const closeBtn = content.querySelector('.close');
    if (closeBtn) closeBtn.addEventListener('click', closeOpenInfo);

    const editBtn = content.querySelector('.edit-marker');
    if (editBtn) {
      editBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        closeOpenInfo();
        setFormData({ name, country, description: description || '' });
        setCategory(cat);
        setPendingCoords(coordsArr);
        setEditingId(markerId);
        setShowForm(true);
      });
    }

    info.addListener('closeclick', () => {
      if (openInfoRef.current === info) openInfoRef.current = null;
    });

    marker.addListener('click', () => {
      closeOpenInfo();
      info.open({ map: mapRef.current, anchor: marker });
      openInfoRef.current = info;
    });
  };

  const addMarker = async ({
    name = 'Unnamed',
    country,
    category,
    coordinates,
    description = ''
  }) => {
    try {
      const coords = coordinates || await geocode(name, country);
      let id = null;
      if (sb) {
        const { data: inserted, error } = await sb
          .from('map_markers')
          .insert({ name, country, category, coordinates: coords, description })
          .select();
        if (error) {
          console.error('Supabase insert error', error);
        } else if (inserted && inserted[0]) {
          id = inserted[0].id;
        }
      }
      renderMarker({ id, name, country, category, coordinates: coords, description });
      logDiscord(`New marker: ${name}, ${country}, ${category}`);
    } catch (err) {
      console.error('Error adding marker', err);
    }
  };

  const updateMarker = async (id, {
    name,
    country,
    category,
    coordinates,
    description = ''
  }) => {
    try {
      const coords = coordinates || await geocode(name, country);
      markersRef.current = markersRef.current.filter(m => {
        if (m.id === id) {
          m.marker.map = null;
          return false;
        }
        return true;
      });
      if (sb) {
        const { error } = await sb
          .from('map_markers')
          .update({ name, country, category, coordinates: coords, description })
          .eq('id', id);
        if (error) {
          console.error('Supabase update error', error);
        }
      }
      renderMarker({ id, name, country, category, coordinates: coords, description });
      logDiscord(`Updated marker: ${name}, ${country}, ${category}`);
    } catch (err) {
      console.error('Error updating marker', err);
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!pendingCoords) return;
    const { name, country, description } = formData;
    if (!country.trim()) return;
    if (editingId) {
      await updateMarker(editingId, {
        name: name.trim() || 'Unnamed',
        country: country.trim(),
        category,
        description,
        coordinates: pendingCoords
      });
      setEditingId(null);
    } else {
      await addMarker({
        name: name.trim() || 'Unnamed',
        country: country.trim(),
        category,
        description,
        coordinates: pendingCoords
      });
    }
    setShowForm(false);
  };

  const handleSuggestionClick = (prediction) => {
    setQuery('');
    setSuggestions([]);
    if (!geocoderRef.current) return;
    geocoderRef.current.geocode({ placeId: prediction.place_id }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        const countryComp = results[0].address_components.find(c => c.types.includes('country'));
        const country = countryComp ? countryComp.long_name : '';
        setPendingCoords([loc.lng(), loc.lat()]);
        setFormData({ name: prediction.description, country, description: '' });
        setEditingId(null);
        setShowForm(true);
      }
    });
  };

  const handleSearchSubmit = () => {
    if (!query || !geocoderRef.current) return;
    geocoderRef.current.geocode({ address: query }, async (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        const countryComp = results[0].address_components.find(c => c.types.includes('country'));
        const country = countryComp ? countryComp.long_name : '';
        setEditingId(null);
        await addMarker({
          name: results[0].formatted_address,
          country,
          category,
          coordinates: [loc.lng(), loc.lat()]
        });
        setQuery('');
        setSuggestions([]);
      }
    });
  };

  return (
    <>
      <div id="map" ref={mapContainer}></div>
      <div id="legend" className={legendOpen ? '' : 'hidden'}>
        {['official','restricted','unofficial','illegal'].map(cat => (
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
      </div>
      {isMobile && (
        <button id="legend-toggle" onClick={() => setLegendOpen(o => !o)}>
          {legendOpen
            ? <i className="fa-solid fa-xmark"></i>
            : <i className="fa-solid fa-circle-info"></i>}
        </button>
      )}
      <div id="overlay">
        <h1>Legal Map</h1>
         <input
          value={query}
          onChange={e => { setQuery(e.target.value); searchPlaces(e.target.value); }}
          onKeyDown={e => { if (e.key === 'Enter') handleSearchSubmit(); }}
          placeholder="Search for a place"
        />
        {suggestions.length > 0 && (
          <ul id="suggestions">
            {suggestions.map(p => (
              <li key={p.place_id} onClick={() => handleSuggestionClick(p)}>{p.description}</li>
            ))}
          </ul>
        )}
      </div>
      {showForm && (
        <div id="form-container">
          <form id="marker-form" onSubmit={handleFormSubmit}>
            <input
              value={formData.name}
              onChange={e => setFormData({ ...formData, name: e.target.value })}
              placeholder="Location name"
              required
            />
            <input
              value={formData.country}
              onChange={e => setFormData({ ...formData, country: e.target.value })}
              placeholder="Country"
              required
            />
            <select value={category} onChange={e => setCategory(e.target.value)}>
              <option value="official">official</option>
              <option value="restricted">restricted</option>
              <option value="unofficial">unofficial</option>
              <option value="illegal">illegal</option>
            </select>
            <input
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              placeholder="Description"
            />
            <button type="submit">{editingId ? 'Save' : 'Add'}</button>
            <button type="button" onClick={() => { setShowForm(false); setEditingId(null); }}>Cancel</button>
          </form>
        </div>
      )}
      </>
    );
  }

ReactDOM.createRoot(document.getElementById('root')).render(<App />);