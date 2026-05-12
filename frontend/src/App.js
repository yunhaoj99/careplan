import React, { useState, useRef, useCallback } from 'react';
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
  const [polling, setPolling] = useState(false);
  const [pollCount, setPollCount] = useState(0);
  const timerRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setPolling(false);
  }, []);

  const startPolling = useCallback((carePlanId) => {
    setPolling(true);
    setPollCount(0);

    timerRef.current = setInterval(async () => {
      setPollCount((prev) => prev + 1);
      try {
        const res = await fetch(`http://localhost:8000/api/careplan/${carePlanId}/status/`);
        const data = await res.json();

        if (data.status === 'completed' || data.status === 'failed') {
          stopPolling();
          setResult((prev) => ({
            ...prev,
            status: data.status,
            care_plan: data.content || '',
          }));
        }
      } catch (err) {
        // Network error during polling — keep trying
      }
    }, 3000);
  }, [stopPolling]);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    stopPolling();

    try {
      const response = await fetch('http://localhost:8000/api/orders/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      const data = await response.json();
      setResult(data);
      setLoading(false);

      if (data.status === 'pending' || data.status === 'processing') {
        startPolling(data.care_plan_id);
      }
    } catch (err) {
      setResult({ status: 'failed', care_plan: 'Network error: ' + err.message });
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
          {loading ? 'Submitting...' : 'Submit Order'}
        </button>
      </form>

      {result && (
        <div className={'result ' + result.status}>
          <h2>Care Plan</h2>
          <p className="order-id">Order ID: {result.id}</p>
          <p className="status">
            Status: <span>{result.status}</span>
            {polling && <span className="poll-indicator"> (checking every 3s... #{pollCount})</span>}
          </p>
          {result.care_plan && <pre>{result.care_plan}</pre>}
        </div>
      )}
    </div>
  );
}

export default App;
