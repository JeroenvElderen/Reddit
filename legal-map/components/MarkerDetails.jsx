const { useEffect, useState } = React;

function MarkerDetails() {
  const [marker, setMarker] = useState(null);
  const [currentPhoto, setCurrentPhoto] = useState(0);
    const handleShare = async () => {
        try {
            await navigator.clipboard.writeText(window.location.href);
            alert('Link copied to clipboard!');
        } catch (err) {
            console.error('Failed to copy: ', err);
        }
    };

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

  if (!marker) {
    return (
        <div class="page-content">
            <p>Loading...</p>
        </div>
    );
    }

  let lat, lng;
  const coords = marker.coordinates;
  if (Array.isArray(coords)) {
    [lng, lat] = coords;
  } else if (coords && typeof coords === 'object') {
    ({ lat, lng } = coords);
  } else if (typeof coords === 'string') {
    const parts = coords.split(',').map(parseFloat);
    [lng, lat] = parts;
  }

  const photos = marker.photos || [];

  return (
    <div className="marker-page">
      <header className="marker-header">
        <div className="marker-header-left">
          <h1>{marker.name}</h1>
          <div className="marker-meta">
            <i className="fa-solid fa-star"></i>
            <span>{marker.rating ?? '5.0'}</span>
            <span className="marker-reviews">• {marker.review_count ?? 0} reviews</span>
          </div>
        </div>
        <div className="marker-actions">
          {lat && lng && (
            <a
              className="marker-action"
              href={`https://www.google.com/maps?q=${lat},${lng}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <i className="fa-solid fa-map"></i> View on map
            </a>
          )}
          <button className="marker-action" onClick={handleShare}>
            <i className="fa-solid fa-share-nodes"></i> Share location
          </button>
          <a className="marker-action" href="register.html">
            <i className="fa-solid fa-user-plus"></i> Join
          </a>
        </div>
      </header>
      <div className="marker-content">
        <nav className="marker-nav">
          <ul>
            <li><a href="#photos">Photos</a></li>
            <li><a href="#features">Features</a></li>
            <li><a href="#description">Description</a></li>
            {lat != null && lng != null && (
              <li>
                <a
                  href={`https://www.google.com/maps?q=${lat},${lng}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  View on map
                </a>
              </li>
            )}
          </ul>
        </nav>
        <section className="marker-main">
          <div id="photos">
            {photos.length > 0 && (
              <div className="photo-gallery">
                <img
                  className="main-photo"
                  src={photos[currentPhoto]}
                  alt={marker.name}
                />
                <div className="thumbnails">
                  {photos.map((url, idx) => (
                    <img
                      key={idx}
                      src={url}
                      className={idx === currentPhoto ? 'active' : ''}
                      onClick={() => setCurrentPhoto(idx)}
                      alt=""
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
          <div id="features">
            <h2>Features</h2>
            <p>{marker.category}</p>
          </div>
          <div id="description">
            <h2>Description</h2>
            <p>{marker.description}</p>
          </div>
        </section>
      </div>
    </div>
  );
}

ReactDOM.render(<MarkerDetails />, document.getElementById('root'));