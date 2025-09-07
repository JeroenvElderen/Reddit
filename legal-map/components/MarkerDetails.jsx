const { useEffect, useState } = React;

function MarkerDetails() {
    const [marker, setMarker] = useState(null);
    const [currentPhoto, setCurrentPhoto] = useState(0);
    const ratingFields = [
    { name: 'overall', label: 'Rating*' },
    { name: 'nudity', label: 'Blootvriendelijkheid' },
    { name: 'hygiene', label: 'Hygiëne' },
    { name: 'price', label: 'Prijs / kwaliteit' },
    { name: 'facilities', label: 'Faciliteiten' },
    { name: 'swimming', label: 'Zwemmen' },
    { name: 'sanitary', label: 'Staat van het sanitair' },
    { name: 'food', label: 'Eten & drinken' },
    { name: 'location', label: 'Ligging' },
    { name: 'child', label: 'Kindvriendelijkheid' },
    { name: 'disabled', label: 'Geschikt voor mindervaliden' }
  ];
  const extraRatingLabel = 'Ook interessant (telt niet mee in de score)';
  const [ratings, setRatings] = useState(
    Object.fromEntries(ratingFields.map(f => [f.name, 0]))
  );
  const [reviewCount, setReviewCount] = useState(0);
  const [avgRatings, setAvgRatings] = useState({});
  const formatRating = value => {
    const num = Number(value);
    if (Number.isNaN(num)) return '0';
    return num.toFixed(1).replace(/\.0$/, '');
  };

  const handleRatingChange = (field, value) => {
    setRatings(prev => ({ ...prev, [field]: value }));
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert('Link copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!marker) return;
    const formData = new FormData(e.target);
    const cleanRatings = Object.fromEntries(
      Object.entries(ratings).map(([key, value]) => [key, value > 0 ? value : null])
    );
    const payload = {
      marker_id: marker.id,
      name: formData.get('name'),
      email: formData.get('email'),
      visited: formData.get('visited'),
      title: formData.get('title'),
      text: formData.get('text'),
      ...cleanRatings,
    };
    try {
      const { error } = await window.supabaseClient
        .from('marker_reviews')
        .insert(payload);
      if (error) throw error;
      alert('Review submitted!');
      e.target.reset();
      setRatings(Object.fromEntries(ratingFields.map(f => [f.name, 0])));
      setReviewCount(c => c + 1);
      setMarker(prev => ({ ...prev, review_count: (prev?.review_count ?? 0) + 1 }));
    } catch (err) {
      console.error('Error saving review', err);
      alert('Error saving review');
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (!id) return;
    const fetchData = async () => {
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
      const { data: reviews, error: reviewError } = await window.supabaseClient
        .from('marker_reviews')
        .select(ratingFields.map(f => f.name).join(','))
        .eq('marker_id', id);
      if (reviewError) {
        console.error('Error fetching reviews', reviewError);
      } else if (reviews) {
        setReviewCount(reviews.length);
        const averages = {};
        ratingFields.forEach(field => {
          const values = reviews
            .map(r => r[field.name])
            .filter(v => typeof v === 'number' && v > 0);
          const avg = values.length
            ? values.reduce((a, b) => a + b, 0) / values.length
            : 0;
          averages[field.name] = Number(avg.toFixed(1));
        });
        setAvgRatings(averages);
        setMarker(prev => ({
          ...prev,
          rating: averages.overall ?? prev?.rating,
          review_count: reviews.length,
        }));
      }
    };
    fetchData();
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
    [lat, lng] = coords;
  } else if (coords && typeof coords === 'object') {
    ({ lat, lng } = coords);
  } else if (typeof coords === 'string') {
    const parts = coords.split(',').map(parseFloat);
    [lat, lng] = parts;
  }

  const photos = marker.photos || [];
  const PLACEHOLDER_IMAGE = 'https://placehol.com/600x400?text=No+Image+Available';
    const primaryFields = ratingFields.filter(f => !['overall','location','child','disabled'].includes(f.name));
    const secondaryFields = ratingFields.filter(f => ['location','child','disabled'].includes(f.name));

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
              href={`https://www.google.com/maps?q=${lng},${lat}`}
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
            <li><a href="#reviews">Reviews</a></li>
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
          <div id="photos" className="marker-section">
            <div className="photo-gallery">
              <img
                className="main-photo"
                src={photos.length > 0 ? photos[currentPhoto] : PLACEHOLDER_IMAGE}
                alt={photos.length > 0 ? marker.name : 'No image available'}
              />
              {photos.length > 1 && (
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
              )}
              {photos.length === 0 && (
                <p>No image available</p>
              )}
            </div>
          </div>
          <div id="features" className="marker-section">
            <h2>Features</h2>
            <div className="feature-group">
              <h3>General</h3>
              <ul>
                {marker.features && marker.features.length > 0 ? (
                  marker.features.map((feat, idx) => <li key={idx}>{feat}</li>)
                ) : (
                  <li>{marker.category}</li>
                )}
              </ul>
            </div>
          </div>
          <div id="description" className="marker-section">
            <h2>Description</h2>
            <p>{marker.description}</p>
          </div>
          <div id="address" className="marker-section">
            <h2>Address Details</h2>
            <div className="address-info">
              <div className="address-block">
                <h3>Address</h3>
                {marker.address ? (
                  marker.address.split(',').map((line, idx) => (
                    <p key={idx}>{line.trim()}</p>
                  ))
                ) : (
                  <p>No address available</p>
                )}
              </div>
              {lat != null && lng != null && (
                <div className="address-block">
                  <h3>Navigation Address</h3>
                  <p>Google coordinates</p>
                  <p>
                    {lat}, {lng}
                  </p>
                  <a
                    className="marker-action"
                    href={`https://www.google.com/maps?q=${lng},${lat}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <i className="fa-solid fa-map"></i> Open map
                  </a>
                </div>
              )}
            </div>
          </div>
          <div id="reviews" className="marker-section">
            <h2>Plaats een review</h2>
            <form className="review-form" onSubmit={handleReviewSubmit} method="post">
              <div className="form-row">
                <label htmlFor="review-name">Naam*</label>
                <input id="review-name" name="name" type="text" required />
              </div>
              <div className="form-row">
                <label htmlFor="review-email">E-mail*</label>
                <input id="review-email" name="email" type="email" required />
              </div>
              <div className="form-row">
                <label htmlFor="review-visited">Met wie bezocht je de locatie</label>
                <select id="review-visited" name="visited">
                  <option>Alleen</option>
                  <option>Partner</option>
                  <option>Gezin</option>
                  <option>Vrienden</option>
                </select>
              </div>
              <p className="rating-note">
                LET OP: Beoordeel alléén de onderdelen die op deze locatie aanwezig zijn. Is er bijvoorbeeld geen zwemgelegenheid, geef dan geen beoordeling voor het onderdeel 'zwemmen'. Anders trekt deze beoordeling onterecht het gemiddelde cijfer omlaag.
              </p>
                <div className="rating-field">
                  <span>{ratingFields.find(f => f.name === 'overall').label}</span>
                  <div className="rating">
                    {[5,4,3,2,1].map(n => (
                      <React.Fragment key={n}>
                        <input
                          type="radio"
                          id={`overall-${n}`}
                          name="overall"
                          value={n}
                          onChange={() => handleRatingChange('overall', n)}
                        />
                        <label htmlFor={`overall-${n}`}></label>
                      </React.Fragment>
                    ))}
                  </div>
                </div>
                {primaryFields.map(field => (
                  <div className="rating-field" key={field.name}>
                    <span>{field.label}</span>
                    <div className="rating">
                      {[5,4,3,2,1].map(n => (
                        <React.Fragment key={n}>
                          <input
                            type="radio"
                            id={`${field.name}-${n}`}
                            name={field.name}
                            value={n}
                            onChange={() => handleRatingChange(field.name, n)}
                          />
                          <label htmlFor={`${field.name}-${n}`}></label>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
                <p className="rating-note">{extraRatingLabel}</p>
                {secondaryFields.map(field => (
                  <div className="rating-field" key={field.name}>
                    <span>{field.label}</span>
                    <div className="rating">
                      {[5,4,3,2,1].map(n => (
                        <React.Fragment key={n}>
                          <input
                            type="radio"
                            id={`${field.name}-${n}`}
                            name={field.name}
                            value={n}
                            onChange={() => handleRatingChange(field.name, n)}
                          />
                          <label htmlFor={`${field.name}-${n}`}></label>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                ))}
              <div className="form-row">
                <label htmlFor="review-title">Geef je beoordeling een titel</label>
                <input id="review-title" name="title" type="text" />
              </div>
              <div className="form-row">
                <label htmlFor="review-text">Schrijf hier je review (max. 300 woorden)</label>
                <textarea id="review-text" name="text" maxLength="300"></textarea>
              </div>
              <div className="form-row terms">
                <label>
                  <input type="checkbox" required /> Ik ga akkoord met de <a href="#">Spelregels</a> en <a href="#">Privacy Policy</a>
                </label>
              </div>
              <button type="submit">Review plaatsen</button>
            </form>
            <h2>Reviews over deze locatie</h2>
            <div className="review-summary">
              <div className="review-count">{reviewCount}</div>
              <div className="review-lists">
                <ul>
                  {primaryFields.map(field => (
                    <li key={field.name}>
                      <span>{field.label}</span>
                      <span>{formatRating(avgRatings[field.name] ?? 0)}</span>
                    </li>
                  ))}
                </ul>
                  {secondaryFields.length > 0 && (
                    <>
                      <h3>{extraRatingLabel}</h3>
                      <ul>
                        {secondaryFields.map(field => (
                        <li key={field.name}>
                          <span>{field.label}</span>
                          <span>{formatRating(avgRatings[field.name] ?? 0)}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

ReactDOM.render(<MarkerDetails />, document.getElementById('root'));
