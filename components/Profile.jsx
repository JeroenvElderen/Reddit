function Profile() {
  const [user, setUser] = React.useState();
  const [newUsername, setNewUsername] = React.useState('');
  const [newPassword, setNewPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const [firstName, setFirstName] = React.useState('');
  const [lastName, setLastName] = React.useState('');
  const [address, setAddress] = React.useState('');
  const [city, setCity] = React.useState('');
  const [country, setCountry] = React.useState('');
  const [postalCode, setPostalCode] = React.useState('');
  const [aboutMe, setAboutMe] = React.useState('');
  const [birthdate, setBirthdate] = React.useState('');
  const [editing, setEditing] = React.useState(false);
  const [avatarPath, setAvatarPath] = React.useState('');
  const [avatarUrl, setAvatarUrl] = React.useState('');
  const [coverPath, setCoverPath] = React.useState('');
  const [coverUrl, setCoverUrl] = React.useState('');
  const DEFAULT_AVATAR =
    'https://demos.creativetim.com/argon-dashboard/assets-old/img/theme/team-4.jpg';
  const DEFAULT_COVER =
    'https://raw.githubusercontent.com/creativetimofficial/argon-dashboard/gh-pages/assets-old/img/theme/profile-cover.jpg';
  const STORAGE_BUCKET = 'profile-images';

  React.useEffect(() => {
    async function loadUser() {
      const {
        data: { user },
        error,
      } = await supabaseClient.auth.getUser();
      if (error) {
        console.error(error);
      }
      setUser(user);
      setNewUsername(user?.user_metadata?.username || '');
      setFirstName(user?.user_metadata?.first_name || '');
      setLastName(user?.user_metadata?.last_name || '');
      setAddress(user?.user_metadata?.address || '');
      setCity(user?.user_metadata?.city || '');
      setCountry(user?.user_metadata?.country || '');
      setPostalCode(user?.user_metadata?.postal_code || '');
      setAboutMe(user?.user_metadata?.about_me || '');
      setBirthdate(user?.user_metadata?.birthdate || '');
      if (user) {
        const { data: profile, error: profileError } = await supabaseClient
          .from('profiles')
          .select('avatar_url, cover_url')
          .eq('id', user.id)
          .single();
        if (!profileError && profile) {
          if (profile.avatar_url) {
            setAvatarPath(profile.avatar_url);
            const { data: aUrl } = supabaseClient.storage
              .from(STORAGE_BUCKET)
              .getPublicUrl(profile.avatar_url);
            if (aUrl?.publicUrl) {
              setAvatarUrl(aUrl.publicUrl);
            }
          }
          if (profile.cover_url) {
            setCoverPath(profile.cover_url);
            const { data: cUrl } = supabaseClient.storage
              .from(STORAGE_BUCKET)
              .getPublicUrl(profile.cover_url);
            if (cUrl?.publicUrl) {
              setCoverUrl(cUrl.publicUrl);
            }
          }
        }
      }
    }
    loadUser();
  }, []);

  const calculateAge = (dob) => {
    if (!dob) return '';
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  const calculateNaturistDays = (createdAt) => {
    if (!createdAt) return 0;
    const createdDate = new Date(createdAt);
    const today = new Date();
    const diffTime = today - createdDate;
    return Math.floor(diffTime / (1000 * 60 * 60 * 24));
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !user) return;
    const fileExt = file.name.split('.').pop();
    const filePath = `${user.id}/avatar-${Date.now()}.${fileExt}`;
    if (avatarPath) {
      await supabaseClient.storage
        .from(STORAGE_BUCKET)
        .remove([avatarPath]);
    }
    const { error: uploadError } = await supabaseClient.storage
      .from(STORAGE_BUCKET)
      .upload(filePath, file);
    if (uploadError) {
      alert(uploadError.message);
      return;
    }
    const { data: urlData } = supabaseClient.storage
      .from(STORAGE_BUCKET)
      .getPublicUrl(filePath);
    await supabaseClient
      .from('profiles')
      .update({ avatar_url: filePath })
      .eq('id', user.id);
    setAvatarPath(filePath);
    if (urlData?.publicUrl) {
      setAvatarUrl(urlData.publicUrl);
    }
  };

  const handleCoverUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !user) return;
    const fileExt = file.name.split('.').pop();
    const filePath = `${user.id}/cover-${Date.now()}.${fileExt}`;
    if (coverPath) {
      await supabaseClient.storage
        .from(STORAGE_BUCKET)
        .remove([coverPath]);
    }
    const { error: uploadError } = await supabaseClient.storage
      .from(STORAGE_BUCKET)
      .upload(filePath, file);
    if (uploadError) {
      alert(uploadError.message);
      return;
    }
    const { data: urlData } = supabaseClient.storage
      .from(STORAGE_BUCKET)
      .getPublicUrl(filePath);
    await supabaseClient
      .from('profiles')
      .update({ cover_url: filePath })
      .eq('id', user.id);
    setCoverPath(filePath);
    if (urlData?.publicUrl) {
      setCoverUrl(urlData.publicUrl);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const updates = {
      data: {
        username: newUsername,
        first_name: firstName,
        last_name: lastName,
        address,
        city,
        country,
        postal_code: postalCode,
        about_me: aboutMe,
        birthdate,
      },
    };
    if (newPassword) {
      updates.password = newPassword;
    }
    const { data, error } = await supabaseClient.auth.updateUser(updates);
    setLoading(false);
    if (error) {
      alert(error.message);
    } else {
      alert('Profile updated');
      setUser(data.user);
      setNewPassword('');
      setFirstName(data.user.user_metadata?.first_name || '');
      setLastName(data.user.user_metadata?.last_name || '');
      setAddress(data.user.user_metadata?.address || '');
      setCity(data.user.user_metadata?.city || '');
      setCountry(data.user.user_metadata?.country || '');
      setPostalCode(data.user.user_metadata?.postal_code || '');
      setAboutMe(data.user.user_metadata?.about_me || '');
      setBirthdate(data.user.user_metadata?.birthdate || '');
    }
  };

  if (user === undefined) {
    return (
      <div className="main-content">
        <p>Loading...</p>
      </div>
    );
  }

  if (user === null) {
    return (
      <div className="main-content">
          <p>
            You are not logged in. <a href="login.html">Login</a>
          </p>
      </div>
    );
  }

  return (
    <div className="main-content">
      <nav className="navbar navbar-top navbar-expand-md navbar-dark" id="navbar-main">
        <div className="container-fluid">
          <a className="h4 mb-0 text-white text-uppercase d-none d-lg-inline-block" href="#">
            User profile
          </a>
        </div>
      </nav>
      <div
        className="header pb-8 pt-5 pt-lg-8 d-flex align-items-center"
        style={{
          minHeight: '600px',
          backgroundImage: `url(${coverUrl || DEFAULT_COVER})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center top',
          position: 'relative',
        }}
      >
        {editing && (
          <>
            <label htmlFor="cover-upload" className="edit-overlay">
              <i className="fa-solid fa-plus-circle"></i>
            </label>
            <input
              type="file"
              id="cover-upload"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={handleCoverUpload}
            />
          </>
        )}
        <span className="mask bg-gradient-default opacity-8" />
        <div className="container-fluid d-flex align-items-center">
          <div className="row">
            <div className="col-lg-7 col-md-10">
              <h1 className="display-2 text-white">
                Hello {user?.user_metadata?.username || 'User'}
              </h1>
              <p className="text-white mt-0 mb-5">
                This is your profile page. You can see the progress you've made
                with your work and manage your projects or assigned tasks
              </p>
              <button
                className="btn btn-info"
                onClick={() => setEditing(!editing)}
                type="button"
              >
                {editing ? 'Done' : 'Settings'}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="container-fluid mt--7">
        <div className="row">
          <div className="col-xl-4 order-xl-2 mb-5 mb-lg-0">
            <div className="card card-profile shadow">
              <div className="row justify-content-center">
                <div className="col-lg-3 order-lg-2">
                  <div className="card-profile-image">
                    {editing ? (
                      <label htmlFor="avatar-upload" className="image-edit">
                        <img
                          src={avatarUrl || DEFAULT_AVATAR}
                          className="rounded-circle"
                        />
                        <span className="edit-overlay">
                          <i className="fa-solid fa-plus-circle"></i>
                        </span>
                      </label>
                    ) : (
                      <img
                        src={avatarUrl || DEFAULT_AVATAR}
                        className="rounded-circle"
                      />
                      )}
                    {editing && (
                      <input
                        type="file"
                        id="avatar-upload"
                        accept="image/*"
                        style={{ display: 'none' }}
                        onChange={handleAvatarUpload}
                      />
                    )}
                  </div>
                </div>
              </div>
              <div className="card-header text-center border-0 pt-8 pt-md-4 pb-0 pb-md-4">
                <div className="d-flex justify-content-between">
                  <a href="#" className="btn btn-sm btn-info mr-4">
                    Connect
                  </a>
                  <a href="#" className="btn btn-sm btn-default float-right">
                    Message
                  </a>
                </div>
              </div>
              <div className="card-body pt-0 pt-md-4">
                <div className="row">
                    <div className="col">
                      <div className="card-profile-stats d-flex justify-content-center mt-md-5">
                        <div>
                          <span className="heading">{user.user_metadata?.markers_created || 0}</span>
                          <span className="description">Markers</span>
                        </div>
                        <div>
                          <span className="heading">{calculateNaturistDays(user?.created_at)}</span>
                          <span className="description">Days as Naturist</span>
                        </div>
                        <div>
                          <span className="heading">{user.user_metadata?.comments || 0}</span>
                          <span className="description">Comments</span>
                        </div>
                      </div>
                    </div>
                  </div>
                <div className="text-center">
                  <h3>
                      {user.user_metadata?.username || 'Username'}
                      {birthdate && (
                        <span className="font-weight-light">, {calculateAge(birthdate)}</span>
                      )}
                    </h3>
                  <div className="h5 font-weight-300">
                    <i className="fa fa-location-dot mr-2" />
                    Bucharest, Romania
                  </div>
                  <hr className="my-4" />
                    <p>{aboutMe}</p>
                    <a href="#">Show more</a>
                  </div>
                </div>
              </div>
          </div>
          <div className="col-xl-8 order-xl-1">
            <div className="card bg-secondary shadow">
              <div className="card-header bg-white border-0">
                <div className="row align-items-center">
                  <div className="col-8">
                    <h3 className="mb-0">My account</h3>
                  </div>
                  <div className="col-4 text-right"></div>
                </div>
              </div>
              <div className="card-body">
                <form onSubmit={handleSubmit}>
                  <fieldset disabled={!editing} style={{ border: 'none' }}>
                  <h6 className="heading-small text-muted mb-4">
                    User information
                  </h6>
                  <div className="pl-lg-4">
                    <div className="row">
                      <div className="col-lg-6">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-username"
                          >
                            Username
                          </label>
                          <input
                            type="text"
                            id="input-username"
                            className="form-control form-control-alternative"
                            value={newUsername}
                            onChange={(e) => setNewUsername(e.target.value)}
                          />
                        </div>
                      </div>
                      <div className="col-lg-6">
                        <div className="form-group">
                          <label
                            className="form-control-label"
                            htmlFor="input-email"
                          >
                            Email address
                          </label>
                          <input
                            type="email"
                            id="input-email"
                            className="form-control form-control-alternative"
                            value={user.email}
                            disabled
                          />
                        </div>
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-lg-6">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-first-name"
                          >
                            First Name
                          </label>
                          <input
                            type="text"
                            id="input-first-name"
                            className="form-control form-control-alternative"
                            value={firstName}
                            onChange={(e) => setFirstName(e.target.value)}
                            placeholder="First Name"
                          />
                        </div>
                      </div>
                      <div className="col-lg-6">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-last-name"
                          >
                            Last Name
                          </label>
                          <input
                            type="text"
                            id="input-last-name"
                            className="form-control form-control-alternative"
                            value={lastName}
                            onChange={(e) => setLastName(e.target.value)}
                            placeholder="Last Name"
                          />
                        </div>
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-lg-6">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-password"
                          >
                            New Password
                          </label>
                          <input
                            type="password"
                            id="input-password"
                            className="form-control form-control-alternative"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            placeholder="New Password"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  <hr className="my-4" />
                  <h6 className="heading-small text-muted mb-4">
                    Contact information
                  </h6>
                  <div className="pl-lg-4">
                    <div className="row">
                      <div className="col-md-12">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-address"
                          >
                            Address
                          </label>
                          <input
                            id="input-address"
                            className="form-control form-control-alternative"
                            value={address}
                            onChange={(e) => setAddress(e.target.value)}
                            placeholder="Address"
                            type="text"
                          />
                        </div>
                      </div>
                    </div>
                    <div className="row">
                      <div className="col-lg-4">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-city"
                          >
                            City
                          </label>
                          <input
                            type="text"
                            id="input-city"
                            className="form-control form-control-alternative"
                            value={city}
                            onChange={(e) => setCity(e.target.value)}
                            placeholder="City"
                          />
                        </div>
                      </div>
                      <div className="col-lg-4">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-country"
                          >
                            Country
                          </label>
                          <input
                            type="text"
                            id="input-country"
                            className="form-control form-control-alternative"
                            value={country}
                            onChange={(e) => setCountry(e.target.value)}
                            placeholder="Country"
                          />
                        </div>
                      </div>
                      <div className="col-lg-4">
                        <div className="form-group focused">
                          <label
                            className="form-control-label"
                            htmlFor="input-postal-code"
                          >
                            Postal code
                          </label>
                          <input
                            type="number"
                            id="input-postal-code"
                            className="form-control form-control-alternative"
                            value={postalCode}
                            onChange={(e) => setPostalCode(e.target.value)}
                            placeholder="Postal code"
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  <hr className="my-4" />
                  <h6 className="heading-small text-muted mb-4">About me</h6>
                  <div className="pl-lg-4">
                    <div className="form-group focused">
                      <label
                        className="form-control-label"
                        htmlFor="input-birthdate"
                      >
                        Birthdate
                      </label>
                      <input
                        type="date"
                        id="input-birthdate"
                        className="form-control form-control-alternative"
                        value={birthdate}
                        onChange={(e) => setBirthdate(e.target.value)}
                      />
                    </div>
                    <div className="form-group focused">
                      <label
                        className="form-control-label"
                        htmlFor="input-about-me"
                      >
                        About Me
                      </label>
                      <textarea
                        rows="4"
                        className="form-control form-control-alternative"
                        id="input-about-me"
                        value={aboutMe}
                        onChange={(e) => setAboutMe(e.target.value)}
                        placeholder="A few words about you ..."
                      />
                    </div>
                  </div>
                  <div className="pl-lg-4">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                    >
                      {loading ? 'Updating...' : 'Update Profile'}
                    </button>
                  </div>
                  </fieldset>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Profile />);
