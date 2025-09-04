import React, { useEffect, useRef, useState } from 'react';
import SearchBar from './components/SearchBar';
import Legend from './components/Legend';
import MarkerForm from './components/MarkerForm';
import Login from './components/Login';
import Register from './components/Register';
import { createClient } from '@supabase/supabase-js';
import { GOOGLE_MAPS_KEY, SUPABASE_URL, SUPABASE_KEY } from './config';

const supabase = SUPABASE_URL && SUPABASE_KEY ? createClient(SUPABASE_URL, SUPABASE_KEY) : null;

function loadGoogleMaps(key) {
  return new Promise((resolve, reject) => {
    if (window.google) {
      resolve();
      return;
    }
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${key}&libraries=places`;
    script.async = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

function MapView({ onLogin, onRegister }) {
  const mapRef = useRef(null);

  useEffect(() => {
    loadGoogleMaps(GOOGLE_MAPS_KEY).then(() => {
      new window.google.maps.Map(mapRef.current, {
        center: { lat: 0, lng: 0 },
        zoom: 2,
      });
    });
  }, []);

  return (
    <div style={{ height: '100vh', width: '100%' }}>
      <div id="map" ref={mapRef} style={{ height: '100%', width: '100%' }} />
      <SearchBar />
      <Legend />
      <MarkerForm />
      <div style={{ position: 'absolute', top: 10, left: 10 }}>
        <button onClick={onLogin}>Login</button>
        <button onClick={onRegister} style={{ marginLeft: '0.5rem' }}>Register</button>
      </div>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState('map');
  if (view === 'login') {
    return <Login onBack={() => setView('map')} onRegister={() => setView('register')} supabase={supabase} />;
  }
  if (view === 'register') {
    return <Register onBack={() => setView('map')} onLogin={() => setView('login')} supabase={supabase} />;
  }
  return <MapView onLogin={() => setView('login')} onRegister={() => setView('register')} />;
}