import React, { useState } from 'react';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    patient_first_name: '',
    patient_last_name: '',
    patient_mrn: '',
    patient_dob: '',
    provider_name: '',
    provider_npi: '',
    primary_diagnosis: '',
    medication_name: '',
    additional_diagnoses: '',
    medication_history: '',
    patient_records: '',
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/orders/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      setResult(data);
    } catch (err) {
      setResult({ status: 'failed', care_plan: 'Network error: ' + err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <h1>Care Plan Generator</h1>

      <form onSubmit={handleSubmit}>
        <section>
          <h2>Patient Information</h2>
          <div className="form-row">
            <label>
              First Name
              <input name="patient_first_name" value={formData.patient_first_name} onChange={handleChange} />
            </label>
            <label>
              Last Name
              <input name="patient_last_name" value={formData.patient_last_name} onChange={handleChange} />
            </label>
          </div>
          <div className="form-row">
            <label>
              MRN (6 digits)
              <input name="patient_mrn" value={formData.patient_mrn} onChange={handleChange} placeholder="e.g. 001234" />
            </label>
            <label>
              Date of Birth
              <input type="date" name="patient_dob" value={formData.patient_dob} onChange={handleChange} />
            </label>
          </div>
          <label>
            Primary Diagnosis (ICD-10)
            <input name="primary_diagnosis" value={formData.primary_diagnosis} onChange={handleChange} placeholder="e.g. G70.0" />
          </label>
          <label>
            Additional Diagnoses
            <textarea name="additional_diagnoses" value={formData.additional_diagnoses} onChange={handleChange} placeholder="e.g. I10, K21.0" />
          </label>
        </section>

        <section>
          <h2>Provider Information</h2>
          <div className="form-row">
            <label>
              Provider Name
              <input name="provider_name" value={formData.provider_name} onChange={handleChange} />
            </label>
            <label>
              Provider NPI (10 digits)
              <input name="provider_npi" value={formData.provider_npi} onChange={handleChange} placeholder="e.g. 1234567890" />
            </label>
          </div>
        </section>

        <section>
          <h2>Medication</h2>
          <label>
            Medication Name
            <input name="medication_name" value={formData.medication_name} onChange={handleChange} placeholder="e.g. IVIG" />
          </label>
          <label>
            Medication History
            <textarea name="medication_history" value={formData.medication_history} onChange={handleChange} placeholder="List current and past medications..." />
          </label>
        </section>

        <section>
          <h2>Patient Records</h2>
          <label>
            Clinical Notes
            <textarea
              name="patient_records"
              rows="6"
              value={formData.patient_records}
              onChange={handleChange}
              placeholder="Paste patient records or clinical notes here..."
            />
          </label>
        </section>

        <button type="submit" disabled={loading}>
          {loading ? 'Generating Care Plan... (may take 10-20s)' : 'Submit Order'}
        </button>
      </form>

      {result && (
        <div className={'result ' + result.status}>
          <h2>Care Plan</h2>
          <p className="order-id">Order ID: {result.id}</p>
          <p className="status">Status: <span>{result.status}</span></p>
          {result.care_plan && <pre>{result.care_plan}</pre>}
        </div>
      )}
    </div>
  );
}

export default App;
