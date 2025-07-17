import React from 'react';
import './ValuationReport.css';

function ValuationReport({ data }) {
  // This error handling block is still correct.
  if (!data || data.error) {
    return (
      <div className="report-container error-container">
        <h3>Valuation Failed</h3>
        <p>The backend encountered an error and could not complete the valuation.</p>
        <pre className="error-log">
          <strong>Error:</strong> {data?.error || "Unknown error."}
          <br/><br/>
          <strong>Raw AI Output:</strong> {data?.raw_output || "Not available."}
        </pre>
      </div>
    );
  }

  const formatCurrency = (value) => {
    // A small check to handle potential null or undefined values gracefully.
    if (value == null) return '$0'; 
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  };

  // A helper variable to make accessing the nested details cleaner.
  const details = data?.valuation_pipeline_details;

  return (
    <div className="report-container">
      <div className="report-header">
        <h3>Executive Summary</h3>
        <div className="summary-card">
          <div className="summary-item">
            {/* UPDATED: Changed label for clarity */}
            <span className="label">Final Calculated Value</span>
            {/* FIX: Accessing the correct property for the final value */}
            <span className="value">{formatCurrency(data?.final_valuation?.value)}</span>
          </div>
          <div className="summary-item">
            <span className="label">Value Range (Sensitivity Analysis)</span>
            <span className="value">
              {formatCurrency(data?.value_range_analysis?.min_value)} - {formatCurrency(data?.value_range_analysis?.max_value)}
            </span>
          </div>
        </div>
        <p className="sensitivities">
          <strong>Key Sensitivities:</strong> {data?.value_range_analysis?.key_sensitivities?.join(', ') || 'N/A'}
        </p>
      </div>

      <div className="report-section">
        <h3>Valuation Narrative</h3>
        <p className="narrative">{data?.report_narrative || 'No narrative was generated.'}</p>
      </div>

      {/* --- REWORKED SECTION --- */}
      {/* This entire section is replaced to show the new single pipeline structure */}
      <div className="report-section">
        <h3>Valuation Pipeline Details</h3>
        {details ? (
          <div className="summary-card details-card">
            <div className="summary-item">
              <span className="label">Metric</span>
              <span className="value">{details.metric?.description}</span>
              <span className="sub-value">Input Quantity: {details.metric?.quantity} {details.metric?.unit}</span>
            </div>
            <div className="summary-item">
              <span className="label">First-Order Outcome</span>
              <span className="value">Net Improvement: {details.first_order_outcome?.value?.toFixed(1)} {details.first_order_outcome?.unit}</span>
            </div>
            <div className="summary-item">
              <span className="label">Monetization Proxy</span>
              <span className="value">{formatCurrency(details.monetization?.value)} per {details.monetization?.unit}</span>
              <span className="sub-value">Source: {details.monetization?.source}</span>
            </div>
          </div>
        ) : (
          <p>Detailed pipeline data is not available.</p>
        )}
      </div>
      
      <div className="report-section">
        <h3>Traceability Log</h3>
        <pre className="trace-log">{data?.traceability_log || 'No log available.'}</pre>
      </div>
    </div>
  );
}

export default ValuationReport;