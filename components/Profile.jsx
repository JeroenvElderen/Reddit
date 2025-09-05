function Profile() {
  const [user, setUser] = React.useState();
  const [newUsername, setNewUsername] = React.useState('');
  const [newPassword, setNewPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);

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
    }
    loadUser();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const updates = {};
    if (newUsername && newUsername !== user?.user_metadata?.username) {
      updates.data = { username: newUsername };
    }
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
          backgroundImage:
            'url(https://raw.githubusercontent.com/creativetimofficial/argon-dashboard/gh-pages/assets-old/img/theme/profile-cover.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center top',
        }}
      >
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
              <a href="#" className="btn btn-info">
                Edit profile
              </a>
            </div>
          </div>
        </div>
        </div>
      <div className="container-fluid mt--7">
        <div className="row">
          <div className="col-xl-4 order-xl-2 mb-5 mb-xl-0">
            <div className="card card-profile shadow">
              <div className="row justify-content-center">
                <div className="col-lg-3 order-lg-2">
                  <div className="card-profile-image">
                    <a href="#">
                      <img
                        src="https://demos.creative-tim.com/argon-dashboard/assets-old/img/theme/team-4.jpg"
                        className="rounded-circle"
                      />
                    </a>
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
                        <span className="heading">22</span>
                        <span className="description">Friends</span>
                      </div>
                      <div>
                        <span className="heading">10</span>
                        <span className="description">Photos</span>
                      </div>
                      <div>
                        <span className="heading">89</span>
                        <span className="description">Comments</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="text-center">
                  <h3>
                    {user.user_metadata?.username || 'Username'}
                    <span className="font-weight-light">, 27</span>
                  </h3>
                  <div className="h5 font-weight-300">
                    <i className="fa fa-location-dot mr-2" />
                    Bucharest, Romania
                  </div>
                  <div className="h5 mt-4">
                    <i className="fa fa-briefcase mr-2" />
                    Solution Manager - Creative Tim Officer
                  </div>
                  <div>
                    <i className="fa fa-graduation-cap mr-2" />
                    University of Computer Science
                  </div>
                  <hr className="my-4" />
                  <p>
                    Ryan — the name taken by Melbourne-raised, Brooklyn-based
                    Nick Murphy — writes, performs and records all of his own
                    music.
                  </p>
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
                  <div className="col-4 text-right">
                    <a href="#" className="btn btn-sm btn-primary">
                      Settings
                    </a>
                  </div>
                </div>
              </div>
              <div className="card-body">
                <form onSubmit={handleSubmit}>
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
                  <div className="pl-lg-4">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                    >
                      {loading ? 'Updating...' : 'Update Profile'}
                    </button>
                  </div>
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
