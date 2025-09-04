function MarkerForm({
  showForm,
  formData,
  setFormData,
  category,
  setCategory,
  categoryClassMap,
  handleFormSubmit,
  editingId,
  onCancel,
}) {
  if (!showForm) return null;
  return (
    <div id="form-container">
      <form id="marker-form" className={`card ${categoryClassMap[category]}`} onSubmit={handleFormSubmit}>
        <input
          value={formData.name}
          onChange={e => setFormData({ ...formData, name: e.target.value })}
          placeholder="Location name"
          required
        />
        <input
          value={formData.country}
          onChange={e => setFormData({ ...formData, country: e.target.value })}
          placeholder="Country"
          required
        />
        <select value={category} onChange={e => setCategory(e.target.value)} className={categoryClassMap[category]}>
          <option value="official">official</option>
          <option value="restricted">restricted</option>
          <option value="unofficial">unofficial</option>
          <option value="illegal">illegal</option>
          <option value="secluded">secluded</option>
        </select>
        <input
          value={formData.description}
          onChange={e => setFormData({ ...formData, description: e.target.value })}
          placeholder="Description"
        />
        <button type="submit">{editingId ? 'Save' : 'Add'}</button>
        <button type="button" onClick={onCancel}>Cancel</button>
      </form>
    </div>
  );
}
