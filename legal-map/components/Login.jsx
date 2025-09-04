function Login({ onBack, onSwitch }) {
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const { error } = await supabaseClient.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (error) {
      alert(error.message);
    } else {
      alert('Logged in!');
    }
  };

  return (
    <div id="auth-container">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h2>Login</h2>
        <div className="input-group">
          <i className="fa fa-envelope" />
          <input
            type="email"
            placeholder="Email ID"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="input-group">
          <i className="fa fa-lock" />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <div className="options">
          <label><input type="checkbox" /> Remember me</label>
          <a href="#">Forgot Password?</a>
        </div>
        <button type="submit" disabled={loading}>
          {loading ? 'Loading...' : 'Login'}
        </button>
        <p className="switch">Don't have an account? <a href="#" onClick={(e) => { e.preventDefault(); onSwitch(); }}>Register</a></p>
        <p className="switch"><a href="#" onClick={(e) => { e.preventDefault(); onBack(); }}>Back to map</a></p>
      </form>
    </div>
  );
}