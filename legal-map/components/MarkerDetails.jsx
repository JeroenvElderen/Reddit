const { useEffect, useState } = React;

function MarkerDetails() {
  const [marker, setMarker] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (!id) return;
    const fetchMarker = async () => {
      const { data, error } = await window.supabaseClient
        .from('map_markers')
        .select()
        .eq('id', id)
        .single();
      if (error) {
        console.error('Error fetching marker', error);
      } else {
        setMarker(data);
      }
    };
    fetchMarker();
  }, []);

  if (!marker) return (<div class="page-content"><p>Loading...</p></div>);

  const coords = typeof marker.coordinates === 'string'
    ? marker.coordinates.split(',').map(parseFloat)
    : marker.coordinates || [];
  const [lat, lng] = coords;

  return (
    <div class="page-content">
      <h1>{marker.name}</h1>
      <p>{marker.country}</p>
      <p>{marker.category}</p>
      <p>{marker.description}</p>
      {lat && lng && (
        <p>
          <a href={`https://www.google.com/maps?q=${lat},${lng}`} target="_blank" rel="noopener noreferrer">
            View on Google Maps
          </a>
        </p>
      )}
    </div>
  );
}

ReactDOM.render(<MarkerDetails />, document.getElementById('root'));