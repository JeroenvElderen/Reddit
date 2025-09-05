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
      <div id="auth-container">
        <p>Loading...</p>
      </div>
    );
  }

  if (user === null) {
    return (
      <div id="auth-container">
        <div className="auth-card">
          <p>
            You are not logged in. <a href="login.html">Login</a>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div id="auth-container">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Your Profile</h2>
        <p>
          <strong>Email:</strong> {user.email}
        </p>
        <div className="input-group">
          <i className="fa fa-user" />
          <input
            type="text"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            placeholder="Username"
          />
        </div>
        <div className="input-group">
          <i className="fa fa-lock" />
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="New Password"
          />
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Updating...' : 'Update Profile'}
        </button>
      </form>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<Profile />);
