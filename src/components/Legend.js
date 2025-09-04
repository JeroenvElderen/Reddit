import React from 'react';

export default function Legend() {
  const categories = ['official', 'restricted', 'unofficial', 'illegal', 'secluded'];
  return (
    <div id="legend">
      {categories.map(c => (
        <label key={c} className="legend-item">
          <input type="checkbox" defaultChecked />
          <span className={`legend-marker ${c}`}></span>
          {c}
        </label>
      ))}
    </div>
  );
}