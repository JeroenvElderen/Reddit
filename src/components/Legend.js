import React from 'react';

export default function Legend() {
  const categories = ['official', 'restricted', 'unofficial', 'illegal', 'secluded'];

  const legendStyle = {
    position: 'fixed',
    top: 10,
    left: 10,
    zIndex: 2,
    background: 'radial-gradient(ellipse at right top,#00458f8f 0%,#151419 45%,#151419 100%)',
    color: '#fff',
    padding: '1rem 1.5rem',
    borderRadius: '1rem',
    boxShadow: '0.063em 0.75em 1.563em rgb(0 0 0 / 78%)',
    fontFamily: '"Poppins", sans-serif',
    fontSize: '0.9rem',
  };

  const itemStyle = {
    display: 'flex',
    alignItems: 'center',
    margin: '4px 0',
  };

  const inputStyle = {
    marginRight: '4px',
  };

  const markerBase = {
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: '4px',
    fontSize: '0.75rem',
    border: '1px solid #fff',
    color: '#000',
  };

  const markerColors = {
    official: '#2eea9d',
    restricted: '#ffd84d',
    unofficial: '#5a81ff',
    illegal: '#fe6c9b',
    secluded: '#9d5aff',
  };

  return (
    <div style={legendStyle}>
      {categories.map(c => (
        <label key={c} style={itemStyle}>
          <input type="checkbox" defaultChecked style={inputStyle} />
          <span style={{ ...markerBase, background: markerColors[c] }}></span>
          {c}
        </label>
      ))}
    </div>
  );
}