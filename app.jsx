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
  const tempMarkerRef = useRef(null);

  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [category, setCategory] = useState('unofficial');
  const [showForm, setShowForm] = useState(false);
  const showFormRef = useRef(false);
  const [formData, setFormData] = useState({ name: '', country: '', description: '' });
  const [username, setUsername] = useState('');
  const usernameRef = useRef('');
  const [pendingCoords, setPendingCoords] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [filter, setFilter] = useState({
    official: true,
    restricted: true,
    unofficial: true,
    illegal: true,
    secluded: true
  });
  const [countryFilter, setCountryFilter] = useState('All');
  const [countries, setCountries] = useState([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [legendOpen, setLegendOpen] = useState(window.innerWidth >= 768);

  useEffect(() => {
    showFormRef.current = showForm;
  }, [showForm]);

  // ---- zIndex helpers (ADVANCED MARKERS sit above IWs otherwise) ----
  const pushMarkersBehind = () => {
    markersRef.current.forEach(m => {
      if (m?.marker) m.marker.zIndex = -1000; // push pins behind IW layer
    });
  };
  const restoreMarkersZ = () => {
    markersRef.current.forEach(m => {
      if (m?.marker) m.marker.zIndex = 0; // normal
    });
  };

  const clearTempMarker = () => {
    if (tempMarkerRef.current) {
      tempMarkerRef.current.map = null;
      tempMarkerRef.current = null;
    }
  };

  const showTempMarker = ([lng, lat]) => {
    clearTempMarker();
    const exists = markersRef.current.some(({ marker }) => {
      const pos = marker.position;
      const pLat = typeof pos.lat === 'function' ? pos.lat() : pos.lat;
      const pLng = typeof pos.lng === 'function' ? pos.lng() : pos.lng;
      return Math.abs(pLat - lat) < 1e-5 && Math.abs(pLng - lng) < 1e-5;
    });
    if (exists || !mapRef.current || !window.google) return;
    const pin = new google.maps.marker.PinElement({
      background: '#9d5aff',
      borderColor: 'white',
      glyph: '?',
      glyphColor: 'black',
    });
    tempMarkerRef.current = new google.maps.marker.AdvancedMarkerElement({
      map: mapRef.current,
      position: { lat, lng },
      content: pin.element,
      zIndex: 1000,
    });
  };

  useEffect(() => {
    const onResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  useEffect(() => {
    setLegendOpen(!isMobile);
  }, [isMobile]);

  useEffect(() => {
    if (!showForm) clearTempMarker();
  }, [showForm]);

  const closeOpenInfo = () => {
    if (openInfoRef.current) {
      openInfoRef.current.close();
      openInfoRef.current = null;
    }
    clearTempMarker();
    // make sure pins come back to normal whenever we close an IW
    restoreMarkersZ();
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
        center: { lat: 50, lng: 10 },
        zoom: 4,
        minZoom: 4,
        mapId: MAP_ID,
        mapTypeControl: false,
        streetViewControl: false,
        rotateControl: false,
        tilt: 67.5,
        restriction: {
          latLngBounds: { north: 85, south: -85, west: -180, east: 180 },
          strictBounds: true
        }
      });

      geocoderRef.current = new google.maps.Geocoder();
      autocompleteRef.current = new google.maps.places.AutocompleteService();

      mapRef.current.addListener('dragstart', () => {
        closeOpenInfo();
        if (showFormRef.current) {
          setShowForm(false);
          setEditingId(null);
        }
      });
      mapRef.current.addListener('zoom_changed', () => {
        closeOpenInfo();
        if (showFormRef.current) {
          setShowForm(false);
          setEditingId(null);
        }
      });
      mapRef.current.addListener('click', (e) => {
        if (openInfoRef.current) {
          closeOpenInfo();
          return;
        }
        if (showFormRef.current) {
          setShowForm(false);
          setEditingId(null);
          return;
        }
        const coords = [e.latLng.lng(), e.latLng.lat()];
        setPendingCoords(coords);
        showTempMarker(coords);
        setEditingId(null);
        if (geocoderRef.current) {
          geocoderRef.current.geocode({ location: e.latLng }, (results, status) => {
            if (status === 'OK' && results[0]) {
              const res = results[0];
              const countryComp = res.address_components.find(c => c.types.includes('country'));
              const country = countryComp ? countryComp.long_name : '';
              const poiComp = res.address_components.find(c => c.types.includes('point_of_interest'))
                || res.address_components.find(c => c.types.includes('establishment'));
              const rawName = poiComp ? poiComp.long_name : res.formatted_address;
              const name = stripCountry(rawName, country);
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
    official: '#2eea9d',
    restricted: '#ffd84d',
    unofficial: '#5a81ff',
    illegal: '#fe6c9b',
    secluded: '#9d5aff'
  })[(cat || '').toLowerCase().trim()] || '#888';

  const icons = { official: '✓', restricted: '!', unofficial: 'i', illegal: '✖', secluded: 'N' };
  const categoryClassMap = { official: 'green', restricted: 'yellow', unofficial: 'blue', illegal: 'red', secluded: 'purple' };

  const toggleFilter = (cat) => {
    setFilter(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  const refreshCountries = () => {
    const list = Array.from(new Set(markersRef.current.map(m => m.country))).sort();
    setCountries(list);
    if (countryFilter !== 'All' && !list.includes(countryFilter)) {
      setCountryFilter('All');
    }
  };

  useEffect(() => {
    markersRef.current.forEach(({ marker, category, country }) => {
      const matchCat = filter[category];
      const matchCountry = countryFilter === 'All' || country === countryFilter;
      marker.map = (matchCat && matchCountry) ? mapRef.current : null;
    });
  }, [filter, countryFilter]);

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

  const handleQueryChange = (val) => {
    setQuery(val);
    searchPlaces(val);
  };

  const handleUsernameChange = (val) => {
    setUsername(val);
    usernameRef.current = val;
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

  const stripCountry = (name, country) => {
    if (!name) return name;
    // Only keep the portion before the first comma
    const idx = name.indexOf(',');
    return idx === -1 ? name.trim() : name.slice(0, idx).trim();
  };

  const renderMarker = ({ id, name, country, category, coordinates, description, law }) => {
    const pos = Array.isArray(coordinates)
      ? { lat: coordinates[1], lng: coordinates[0] }
      : coordinates;
    const coordsArr = Array.isArray(coordinates) ? coordinates : [coordinates.lng, coordinates.lat];
    const markerId = id ?? Date.now() + Math.random();

    const cat = (category || '').toLowerCase().trim();
    const pin = new google.maps.marker.PinElement({
      background: categoryColor(cat),
      borderColor: 'white',
      glyph: icons[cat] || '',
      glyphColor: 'black',
    });
    const marker = new google.maps.marker.AdvancedMarkerElement({
      position: pos,
      map: mapRef.current,
      content: pin.element,
    });
    marker.zIndex = 0; // baseline so we can move it behind when IW opens

    markersRef.current.push({ marker, category: cat, id: markerId, country });
    refreshCountries();
    const visible = filter[cat] && (countryFilter === 'All' || country === countryFilter);
    marker.map = visible ? mapRef.current : null;

    const text = description || law || '';
    const colorClass = categoryClassMap[cat] || 'blue';

    const content = document.createElement('div');
    content.className = `card popup ${colorClass}`;
    content.innerHTML = `
      <div class="card-body">
        <div>
          <h3>${name}</h3>
          <p>${country}</p>
          <p>${category}</p>
          <p class="card-text">${text}</p>
          <button class="edit-marker">Edit Marker</button>
          <button class="delete-marker">Delete Marker</button>
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
      if (mapRef.current) {
        mapRef.current.panTo(marker.position);
        if (isMobile) {
          const mapHeight = mapRef.current.getDiv().offsetHeight;
          const offset = mapHeight / 2 - 50; // align marker/card near bottom on mobile
          mapRef.current.panBy(0, -offset);
        } else {
          const h = content.offsetHeight || 0;
          mapRef.current.panBy(0, -h / 2);
        }
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

    const deleteBtn = content.querySelector('.delete-marker');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        closeOpenInfo();
        if (!usernameRef.current.trim()) {
          alert('Please enter your Reddit username before deleting')
          return;
        }
        if (confirm('Delete this marker?')) {
          await deleteMarker(markerId, { name, country, category: cat, username: usernameRef.current.trim() });
        }
      });
    }

    info.addListener('closeclick', () => {
      if (openInfoRef.current === info) openInfoRef.current = null;
      restoreMarkersZ(); // IMPORTANT: bring pins back
    });

    marker.addListener('click', () => {
      closeOpenInfo();
      pushMarkersBehind(); // IMPORTANT: push pins behind before opening IW
      info.open({ map: mapRef.current, anchor: marker });
      openInfoRef.current = info;
    });
  };

  const removeMarker = (id) => {
    const idx = markersRef.current.findIndex(m => m.id === id);
    if (idx !== -1) {
      const { marker } = markersRef.current[idx];
      marker.map = null;
      markersRef.current.splice(idx, 1);
      refreshCountries();
    }
  };

  useEffect(() => {
    if (!sb) return;
    const channel = sb
      .channel('map_markers_changes')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'map_markers' },
        payload => { renderMarker(payload.new); }
      )
      .on(
        'postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'map_markers' },
        payload => {
          removeMarker(payload.new.id);
          renderMarker(payload.new);
        }
      )
      .on(
        'postgres_changes',
        { event: 'DELETE', schema: 'public', table: 'map_markers' },
        payload => { removeMarker(payload.old.id); }
      )
      .subscribe();

    return () => { sb.removeChannel(channel); };
  }, []);

  const addMarker = async ({
    name = 'Unnamed', country, category, coordinates, description = '', username
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
      logDiscord(`New marker by: ${username}, ${name}, ${country}, ${category}`);
    } catch (err) {
      console.error('Error adding marker', err);
    }
  };

  const updateMarker = async (id, { name, country, category, coordinates, description = '', username }) => {
    try {
      const coords = coordinates || await geocode(name, country);
      if (sb) {
        await sb
          .from('pending_marker_actions')
          .insert({
            action: 'edit',
            marker_id: id,
            name,
            country,
            category,
            coordinates: coords,
            description,
            username
          });
      }
      alert('Edit request submitted for approval');
    } catch (err) {
      console.error('Error requesting marker update', err);
    }
  };

  const deleteMarker = async (id, { name, country, category, username }) => {
    try {
      if (sb) {
        await sb
          .from('pending_marker_actions')
          .insert({ action: 'delete', marker_id: id, name, country, category, username });
      }
      alert('Deletion request submitted for approval');
    } catch (err) {
      console.error('Error requesting marker deletion', err);
    }
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!pendingCoords) return;
    const { name, country, description } = formData;
    if (!country.trim() || !username.trim()) return;
    if (!sb) {
      alert('Supabase not configured');
      return;
    }
    const { data: userRow, error: userErr } = await sb
      .from('user_karma')
      .select('username')
      .eq('username', username.trim())
      .single();
    if (userErr || !userRow) {
      alert('Username not found in database');
      return;
    }
    if (editingId) {
      await updateMarker(editingId, {
        name: name.trim() || 'Unnamed',
        country: country.trim(),
        category,
        description,
        coordinates: pendingCoords,
        username: username.trim()
      });
      setEditingId(null);
    } else {
      await addMarker({
        name: name.trim() || 'Unnamed',
        country: country.trim(),
        category,
        description,
        coordinates: pendingCoords,
        username: username.trim()
      });
    }
    setShowForm(false);
  };

  const handleSuggestionClick = (prediction) => {
    closeOpenInfo();
    setQuery('');
    setSuggestions([]);
    if (!geocoderRef.current) return;
    geocoderRef.current.geocode({ placeId: prediction.place_id }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        if (mapRef.current) {
          mapRef.current.panTo(loc);
          if (mapRef.current.getZoom() < 14) mapRef.current.setZoom(14);
        }
        const countryComp = results[0].address_components.find(c => c.types.includes('country'));
        const country = countryComp ? countryComp.long_name : '';
        const coords = [loc.lng(), loc.lat()];
        setPendingCoords(coords);
        showTempMarker(coords);
        const name = stripCountry(prediction.description, country);
        setFormData({ name, country, description: '' });
        setEditingId(null);
        setShowForm(true);
        if (mapRef.current && window.google) {
          google.maps.event.addListenerOnce(mapRef.current, 'idle', () => {
            const form = document.getElementById('form-container');
            if (form && mapRef.current) {
              mapRef.current.panBy(0, -(form.offsetHeight * 0.7));
            }
          });
        }
      }
    });
  };

  const handleSearchSubmit = () => {
    closeOpenInfo();
    if (!query || !geocoderRef.current) return;
    geocoderRef.current.geocode({ address: query }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const loc = results[0].geometry.location;
        if (mapRef.current) {
          mapRef.current.panTo(loc);
          if (mapRef.current.getZoom() < 14) mapRef.current.setZoom(14);
        }
        const countryComp = results[0].address_components.find(c => c.types.includes('country'));
        const country = countryComp ? countryComp.long_name : '';
        const name = stripCountry(results[0].formatted_address, country);
        const coords = [loc.lng(), loc.lat()];
        setPendingCoords(coords)
        showTempMarker(coords);
        setFormData({ name, country, description: '' });
        setEditingId(null);
        setShowForm(true);
        setQuery('');
        setSuggestions([]);
        if (mapRef.current && window.google) {
          google.maps.event.addListenerOnce(mapRef.current, 'idle', () => {
            const form = document.getElementById('form-container');
            if (form && mapRef.current) {
              mapRef.current.panBy(0, -(form.offsetHeight * 0.7));
            }
          });
        }
      }
    });
  };

  return (
    <>
      <div id="map" ref={mapContainer}></div>
      <div id="overlay">
        <h1>Legal Map</h1>
        <SearchBar
          query={query}
          onQueryChange={handleQueryChange}
          closeOpenInfo={closeOpenInfo}
          handleSearchSubmit={handleSearchSubmit}
          username={username}
          setUsername={handleUsernameChange}
          suggestions={suggestions}
          handleSuggestionClick={handleSuggestionClick}
        />
      </div>
      <Legend
        legendOpen={legendOpen}
        filter={filter}
        toggleFilter={toggleFilter}
        icons={icons}
        countries={countries}
        countryFilter={countryFilter}
        setCountryFilter={setCountryFilter}
      />
      {isMobile && (
        <button id="legend-toggle" onClick={() => setLegendOpen(o => !o)}>
          {legendOpen
            ? <i className="fa-solid fa-xmark"></i>
            : <i className="fa-solid fa-circle-info"></i>}
        </button>
      )}
      <MarkerForm
        showForm={showForm}
        formData={formData}
        setFormData={setFormData}
        category={category}
        setCategory={setCategory}
        categoryClassMap={categoryClassMap}
        handleFormSubmit={handleFormSubmit}
        editingId={editingId}
        onCancel={() => { setShowForm(false); setEditingId(null); }}
      />
    </>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
