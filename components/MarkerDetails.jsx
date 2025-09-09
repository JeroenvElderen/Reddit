const { useEffect, useState } = React;

function MarkerDetails() {
  const [marker, setMarker] = useState(null);
  const [currentPhoto, setCurrentPhoto] = useState(0);

  // ✅ Use Supabase column names
  const ratingFields = [
    { name: "rating_overall", label: "Rating*" },
    { name: "rating_nudity", label: "Blootvriendelijkheid" },
    { name: "rating_hygiene", label: "Hygiëne" },
    { name: "rating_price_quality", label: "Prijs / kwaliteit" },
    { name: "rating_facilities", label: "Faciliteiten" },
    { name: "rating_swimming", label: "Zwemmen" },
    { name: "rating_sanitary", label: "Staat van het sanitair" },
    { name: "rating_food_drink", label: "Eten & drinken" },
    { name: "rating_location", label: "Ligging" },
    { name: "rating_child_friendly", label: "Kindvriendelijkheid" },
    { name: "rating_disabled_friendly", label: "Geschikt voor mindervaliden" },
  ];

  const extraRatingLabel = "Ook interessant (telt niet mee in de score)";
  const [ratings, setRatings] = useState(
    Object.fromEntries(ratingFields.map((f) => [f.name, 0]))
  );
  const [reviewCount, setReviewCount] = useState(0);
  const [avgRatings, setAvgRatings] = useState({});
  const [reviews, setReviews] = useState([]);
  const [currentPage, setCurrentPage] = useState(0);
  const reviewsPerPage = 3;

  const formatRating = (value) => {
    const num = Number(value);
    if (Number.isNaN(num)) return "0.0";
    return num.toFixed(1); // always keep one decimal, e.g. 4.0, 4.9
  };

  const handleRatingChange = (field, value) => {
    setRatings((prev) => ({ ...prev, [field]: value }));
  };

  const handleShare = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      alert("Link copied to clipboard!");
    } catch (err) {
      console.error("Failed to copy: ", err);
    }
  };

  const handleReviewSubmit = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!marker) return;

    const formData = new FormData(e.target);

    const cleanRatings = Object.fromEntries(
      Object.entries(ratings).map(([key, value]) => [
        key,
        value > 0 ? value : null,
      ])
    );

    const payload = {
      marker_id: marker.id,
      name: formData.get("name"),
      email: formData.get("email"),
      visited_with: formData.get("visited_with"),
      title: formData.get("title"),
      review: formData.get("review"),
      ...cleanRatings,
    };

    try {
      const { error } = await window.supabaseClient
        .from("marker_reviews")
        .insert(payload);
      if (error) throw error;
      alert("Review submitted!");
      e.target.reset();
      setRatings(Object.fromEntries(ratingFields.map((f) => [f.name, 0])));
      setReviewCount((c) => c + 1);
      setMarker((prev) => ({
        ...prev,
        review_count: (prev?.review_count ?? 0) + 1,
      }));
    } catch (err) {
      console.error("Error saving review", err);
      alert("Error saving review");
    }
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (!id) return;

    const fetchData = async () => {
      const { data, error } = await window.supabaseClient
        .from("map_markers")
        .select()
        .eq("id", id)
        .single();
      if (error) {
        console.error("Error fetching marker", error);
      } else {
        setMarker(data);
      }

      const { data: reviewData, error: reviewError } =
        await window.supabaseClient
          .from("marker_reviews")
          .select(
            `id, name, visited_with, title, review, created_at, ${ratingFields
              .map((f) => f.name)
              .join(",")}`
          )
          .eq("marker_id", id)
          .order("created_at", { ascending: false });

      if (reviewError) {
        console.error("Error fetching reviews", reviewError);
      } else if (reviewData) {
        setReviews(reviewData);
        setReviewCount(reviewData.length);

        const averages = {};
        ratingFields.forEach((field) => {
          const values = reviewData
            .map((r) => r[field.name])
            .filter((v) => typeof v === "number" && v > 0);
          const avg = values.length
            ? values.reduce((a, b) => a + b, 0) / values.length
            : 0;
          averages[field.name] = Number(avg.toFixed(1));
        });

        setAvgRatings(averages);
        setMarker((prev) => ({
          ...prev,
          rating: averages.rating_overall ?? prev?.rating,
          review_count: reviewData.length,
        }));
      }
    };
    fetchData();
  }, []);

  if (!marker) {
    return (
      <div className="page-content">
        <p>Loading...</p>
      </div>
    );
  }

  let lat, lng;
  const coords = marker.coordinates;
  if (Array.isArray(coords)) {
    [lat, lng] = coords;
  } else if (coords && typeof coords === "object") {
    ({ lat, lng } = coords);
  } else if (typeof coords === "string") {
    const parts = coords.split(",").map(parseFloat);
    [lat, lng] = parts;
  }

  const photos = marker.photos || [];
  const PLACEHOLDER_IMAGE =
    "https://placehol.co/600x400?text=No+Image+Available";

  const primaryFields = ratingFields.filter(
    (f) =>
      ![
        "rating_overall",
        "rating_location",
        "rating_child_friendly",
        "rating_disabled_friendly",
      ].includes(f.name)
  );
  const secondaryFields = ratingFields.filter((f) =>
    [
      "rating_location",
      "rating_child_friendly",
      "rating_disabled_friendly",
    ].includes(f.name)
  );

  // Average of only the primary ratings that were actually filled in (>0).
  const getReviewAverage = (rev) => {
    const vals = primaryFields
      .map((f) => Number(rev[f.name]))
      .filter((v) => Number.isFinite(v) && v > 0);

    if (vals.length > 0) {
      const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
      return Number(avg.toFixed(1));
    }

    // Fallback: use the author's overall rating if no primary fields were rated
    const overall = Number(rev.rating_overall);
    return Number.isFinite(overall) ? Number(overall.toFixed(1)) : 0.0;
  };

  const totalPages = Math.ceil(reviews.length / reviewsPerPage);
  const start = currentPage * reviewsPerPage;
  const displayedReviews = reviews.slice(start, start + reviewsPerPage);

  const formatDate = (dateStr) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString("nl-NL", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  return (
    <div className="marker-page">
      {/* NEW: left rail (nav) + right rail (all sections). Visuals unchanged */}
      <div className="page-rail">
        {/* Move nav here; same markup/styles */}
        <nav className="marker-nav">
          <ul>
            <li>
              <a href="#section-hero">Foto's</a>
            </li>
            <li>
              <a href="#features">Kenmerken</a>
            </li>
            <li>
              <a href="#description">Beschrijving</a>
            </li>
            <li>
              <a href="#address">Adresgegevens</a>
            </li>
            <li>
              <a href="#section-reviews">Plaats een review</a>
            </li>
            <li>
              <a href="#section-reviews">Lees reviews</a>
            </li>
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

        {/* Right column: ALL your existing sections, unchanged inside */}
        <div className="rail-content">
          {/* SECTION 1 — header + photos */}
          <section
            id="section-hero"
            className="page-section page-section--muted"
          >
            <div className="section-inner">
              <header className="marker-header" id="section-header">
                <div className="marker-header-left">
                  <h1>{marker.name}</h1>
                  <div className="marker-meta">
                    <i className="fa-solid fa-star"></i>
                    <span>{formatRating(marker.rating ?? "5.0")}</span>
                    <span className="marker-reviews">
                      • {marker.review_count ?? 0} reviews
                    </span>
                  </div>
                </div>
                <div className="marker-actions">
                  {lat != null && lng != null && (
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

              <div id="photos" className="photo-gallery">
                <img
                  className="main-photo"
                  src={
                    photos.length > 0 ? photos[currentPhoto] : PLACEHOLDER_IMAGE
                  }
                  alt={photos.length > 0 ? marker.name : "No image available"}
                />

                {photos.length > 1 && (
                  <div className="thumbnails-grid">
                    {photos.slice(1, 5).map((url, idx) => {
                      const gridIndex = idx + 1; // because we sliced from 1
                      const isVideo = /youtube\.com|youtu\.be|vimeo\.com/.test(
                        url
                      );
                      return (
                        <button
                          key={url}
                          type="button"
                          className={`thumb ${
                            gridIndex === currentPhoto ? "active" : ""
                          } ${isVideo ? "is-video" : ""}`}
                          onClick={() => setCurrentPhoto(gridIndex)}
                          aria-label={`Open image ${gridIndex + 1}`}
                        >
                          <img src={url} alt="" />
                        </button>
                      );
                    })}
                  </div>
                )}

                {photos.length > 5 && (
                  <button
                    type="button"
                    className="gallery-more"
                    onClick={() => setCurrentPhoto(0)} // hook up to your lightbox if you add one
                  >
                    Meer foto&apos;s ({photos.length - 1})
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* SECTION 2 — features + description + address */}
          <section
            id="section-info"
            className="page-section page-section--white"
          >
            <div className="section-inner">
              <div id="features" className="marker-section">
                <h2>Features</h2>
                <div className="feature-group">
                  <h3>General</h3>
                  <ul>
                    {marker.features && marker.features.length > 0 ? (
                      marker.features.map((feat, idx) => (
                        <li key={idx}>{feat}</li>
                      ))
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
                      marker.address
                        .split(",")
                        .map((line, idx) => <p key={idx}>{line.trim()}</p>)
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
                        href={`https://www.google.com/maps?q=${lat},${lng}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <i className="fa-solid fa-map"></i> Open map
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* SECTION 3 — reviews */}
          <section
            id="section-reviews"
            className="page-section page-section--light"
          >
            <div className="section-inner">
              <div id="reviews" className="marker-section">
                <h2>Plaats een review</h2>

                <form
                  className="review-form"
                  onSubmit={handleReviewSubmit}
                  method="post"
                >
                  <div className="form-row">
                    <label htmlFor="review-name">Naam*</label>
                    <input id="review-name" name="name" type="text" required />
                  </div>
                  <div className="form-row">
                    <label htmlFor="review-email">E-mail*</label>
                    <input
                      id="review-email"
                      name="email"
                      type="email"
                      required
                    />
                  </div>
                  <div className="form-row">
                    <label htmlFor="review-visited">
                      Met wie bezocht je de locatie
                    </label>
                    <select id="review-visited" name="visited_with">
                      <option>Alleen</option>
                      <option>Partner</option>
                      <option>Gezin</option>
                      <option>Vrienden</option>
                    </select>
                  </div>

                  <p className="rating-note">
                    LET OP: Beoordeel alléén de onderdelen die op deze locatie
                    aanwezig zijn…
                  </p>

                  <div className="rating-field">
                    <span>
                      {
                        ratingFields.find((f) => f.name === "rating_overall")
                          .label
                      }
                    </span>
                    <div className="rating">
                      {[5, 4, 3, 2, 1].map((n) => (
                        <React.Fragment key={n}>
                          <input
                            type="radio"
                            id={`rating_overall-${n}`}
                            name="rating_overall"
                            value={n}
                            onChange={() =>
                              handleRatingChange("rating_overall", n)
                            }
                          />
                          <label htmlFor={`rating_overall-${n}`}></label>
                        </React.Fragment>
                      ))}
                    </div>
                  </div>

                  {primaryFields.map((field) => (
                    <div className="rating-field" key={field.name}>
                      <span>{field.label}</span>
                      <div className="rating">
                        {[5, 4, 3, 2, 1].map((n) => (
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

                  <p className="rating-note">
                    Ook interessant (telt niet mee in de score)
                  </p>

                  {secondaryFields.map((field) => (
                    <div className="rating-field" key={field.name}>
                      <span>{field.label}</span>
                      <div className="rating">
                        {[5, 4, 3, 2, 1].map((n) => (
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
                    <label htmlFor="review-title">
                      Geef je beoordeling een titel
                    </label>
                    <input id="review-title" name="title" type="text" />
                  </div>
                  <div className="form-row">
                    <label htmlFor="review-text">
                      Schrijf hier je review (max. 300 woorden)
                    </label>
                    <textarea
                      id="review-text"
                      name="review"
                      maxLength="300"
                    ></textarea>
                  </div>
                  <div className="form-row terms">
                    <label>
                      <input type="checkbox" required /> Ik ga akkoord met de{" "}
                      <a href="#">Spelregels</a> en{" "}
                      <a href="#">Privacy Policy</a>
                    </label>
                  </div>
                  <button type="submit">Review plaatsen</button>
                </form>

                <h2>Reviews over deze locatie</h2>
                <div className="review-summary">
                  <div className="review-count">{reviewCount}</div>
                  <div className="review-lists">
                    <ul>
                      {primaryFields.map((field) => (
                        <li key={field.name}>
                          <span>{field.label}</span>
                          <span>
                            {formatRating(avgRatings[field.name] ?? 0)}
                          </span>
                        </li>
                      ))}
                    </ul>

                    {secondaryFields.length > 0 && (
                      <>
                        <h3>Ook interessant (telt niet mee in de score)</h3>
                        <ul>
                          {secondaryFields.map((field) => (
                            <li key={field.name}>
                              <span>{field.label}</span>
                              <span>
                                {formatRating(avgRatings[field.name] ?? 0)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                </div>

                {displayedReviews.map((rev) => (
                  <article className="review" key={rev.id}>
                    <div className="review-header">
                      <span className="review-score">
                        {formatRating(getReviewAverage(rev))}
                      </span>
                      <div className="review-headings">
                        <h3 className="review-title">
                          {rev.title || "Review"}
                        </h3>
                        <p className="review-meta">
                          {formatDate(rev.created_at)}
                          {rev.name ? ` • ${rev.name}` : ""}
                          {rev.visited_with
                            ? ` • Bezocht: ${rev.visited_with}`
                            : ""}
                        </p>
                      </div>
                    </div>

                    {rev.review && <p className="review-text">{rev.review}</p>}

                    <div className="review-lists">
                      <ul>
                        {primaryFields.map((field) =>
                          rev[field.name] ? (
                            <li key={field.name}>
                              <span>{field.label}</span>
                              <span>{formatRating(rev[field.name])}</span>
                            </li>
                          ) : null
                        )}
                      </ul>

                      {secondaryFields.some((f) => rev[f.name]) && (
                        <>
                          <h4 className="review-extra-heading">
                            Ook interessant
                          </h4>
                          <ul>
                            {secondaryFields.map((field) =>
                              rev[field.name] ? (
                                <li key={field.name}>
                                  <span>{field.label}</span>
                                  <span>{formatRating(rev[field.name])}</span>
                                </li>
                              ) : null
                            )}
                          </ul>
                        </>
                      )}
                    </div>
                  </article>
                ))}

                {reviews.length > reviewsPerPage && (
                  <div className="review-pagination">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(p - 1, 0))}
                      disabled={currentPage === 0}
                    >
                      Vorige
                    </button>
                    <span className="review-page">
                      {currentPage + 1} / {totalPages}
                    </span>
                    <button
                      onClick={() =>
                        setCurrentPage((p) => Math.min(p + 1, totalPages - 1))
                      }
                      disabled={currentPage === totalPages - 1}
                    >
                      Volgende
                    </button>
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

ReactDOM.render(<MarkerDetails />, document.getElementById("root"));
