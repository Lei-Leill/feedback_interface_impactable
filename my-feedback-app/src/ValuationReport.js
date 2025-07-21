import React from 'react';
import './ValuationReport.css';

// Sub-component to display source details consistently
const SourceCard = ({ title, data }) => {
  // If the entire data object is missing, render a graceful message
  if (!data) {
    return (
      <div className="source-card error">
        <p><strong>{title}:</strong> Data is missing or incomplete.</p>
      </div>
    );
  }
  return (
    <div className="source-card">
      <p><strong>{title}:</strong></p>
      <ul>
        {/* Safely render value and probability only if they exist */}
        {data.value != null && <li><strong>Value:</strong> {data.value}</li>}
        {data.probability != null && <li><strong>Probability:</strong> {data.probability}</li>}
        <li>
          <strong>Source:</strong> 
          <a href={data?.source_url ?? '#'} target="_blank" rel="noopener noreferrer">
            {data?.source_name ?? 'N/A'}
          </a>
        </li>
      </ul>
      <blockquote className="source-quote">
        "{data?.source_quotation ?? 'No quotation available.'}"
      </blockquote>
      <p className="source-reasoning">
        {data?.reasoning ?? 'No reasoning provided.'}
      </p>
    </div>
  );
};


function ValuationReport({ data }) {
  if (!data || data.error) {
    return (
      <div className="report-container error-container">
        <h3>Valuation Failed</h3>
        <p>The backend encountered an error: <strong>{data?.error || "Unknown error."}</strong></p>
      </div>
    );
  }

  const formatCurrency = (value) => {
    if (value == null) return '$0';
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
  };

  const grandTotal = data?.grand_total_valuation;
  const reports = data?.individual_chain_reports || [];

  return (
    <div className="report-container">
      <div className="report-header">
        <h3>Executive Summary</h3>
        <div className="summary-card">
          <div className="summary-item">
            <span className="label">Grand Total Valuation</span>
            <span className="value">{formatCurrency(grandTotal?.value)}</span>
          </div>
        </div>
      </div>

      <div className="report-section">
        <h3>Valuation Breakdown</h3>
        {reports.length > 0 ? (
          reports.map((report, index) => (
            <div key={index} className="vertical-report-card">
              <div className="step-header">
                <h3>Metric {index + 1}: {report.metric_chain}</h3>
              </div>

              <div className="step-container">
                <h4>Step 1: Counterfactual Analysis</h4>
                <p>This is what would have happened without the company's intervention, based on AI-powered research.</p>
                {report.researched_counterfactuals?.map((cf, cf_index) => (
                  <SourceCard key={cf_index} title={`Counterfactual: ${cf.scenario}`} data={cf} />
                ))}
              </div>

              <div className="step-container">
                <h4>Step 2: First-Order Outcome (Net Impact)</h4>
                <div className="first-order-card">
                  {/* This now correctly accesses the value from the passed object */}
                  <span className="value">{report.first_order_outcome?.value?.toFixed(2)} {report.first_order_outcome?.unit}</span>
                  <p>This is the calculated net impact. A positive number here indicates a positive societal impact.</p>
                </div>
              </div>

              <div className="step-container">
                <h4>Step 3: Second-Order Outcomes &amp; Valuation</h4>
                <p>Here's how the net impact from Step 2 translates into real-world outcomes.</p>
                {report.second_order_details?.map((so, so_index) => (
                  <div key={so_index} className="so-card">
                    <h5>{so.description}</h5>
                    <div className="so-details-grid">
                      <SourceCard title="Conversion Factor" data={so.source_details?.conversion_factor} />
                      <SourceCard title="Impact Value per Unit" data={so.source_details?.impact_value_per_unit} />
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="chain-total">
                Calculated Value for this Metric: <strong>{formatCurrency(report.chain_valuation_usd)}</strong>
              </div>
            </div>
          ))
        ) : (
          <p>No individual impact chains were successfully valuated.</p>
        )}
      </div>
    </div>
  );
}

export default ValuationReport;