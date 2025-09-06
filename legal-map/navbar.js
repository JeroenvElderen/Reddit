document.addEventListener('DOMContentLoaded', async () => {
  const hamburger = document.getElementById('hamburger');
  const mobileMenu = document.getElementById('mobile-menu');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      mobileMenu.classList.toggle('show');
    });
  }

  const currentPage = window.location.pathname.split('/').pop();
  document.querySelectorAll('#bottom-nav a, #mobile-menu a').forEach(link => {
    if (link.getAttribute('href') === currentPage) {
      link.classList.add('active');
    }
  });

  const authLink = document.getElementById('auth-link');
  const authLinkMobile = document.getElementById('auth-link-mobile');
  const links = [authLink, authLinkMobile];

  let client = window.supabaseClient;
  if (!client && window.supabase && typeof SUPABASE_URL !== 'undefined' && typeof SUPABASE_ANON_KEY !== 'undefined') {
    client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    window.supabaseClient = client;
  }

  if (client) {
    const { data: { session } } = await client.auth.getSession();
    if (session) {
      links.forEach(link => {
        if (!link) return;
        link.textContent = 'Logout';
        link.href = '#';
        link.addEventListener('click', async (e) => {
          e.preventDefault();
          await client.auth.signOut();
          window.location.href = 'login.html';
        });
      });
    } else {
      links.forEach(link => {
        if (!link) return;
        link.textContent = 'Login';
        link.href = 'login.html';
      });
    }
  } else {
    links.forEach(link => {
      if (!link) return;
      link.textContent = 'Login';
      link.href = 'login.html';
    });
  }
});