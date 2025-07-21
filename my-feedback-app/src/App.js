import React, { useState } from 'react';
import FeedbackSection from './FeedbackSection';
import ValuationReport from './ValuationReport';
import LiveLog from './LiveLog';
import AgentConversationLog from './AgentConversationLog'; // Import the new component
import './App.css';

function App() {
  // State for the initial analysis
  const [url, setUrl] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const [metricValue, setMetricValue] = useState(100); 

  // State for the valuation process
  const [isValuating, setIsValuating] = useState(false);
  const [logMessages, setLogMessages] = useState([]);
  const [valuationData, setValuationData] = useState(null);
  const [conversationLog, setConversationLog] = useState([]); // State for the conversation

  // General status message state
  const [statusMessage, setStatusMessage] = useState('');

  const handleGenerate = async () => {
    if (!url) {
      alert('Please enter a website URL.');
      return;
    }
    // Reset all states for a new run
    setIsLoading(true);
    setAnalysisData(null);
    setValuationData(null);
    setLogMessages([]);
    setConversationLog([]); // Reset conversation log
    setStatusMessage('');

    try {
      const response = await fetch('http://localhost:5001/api/generate_all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url }),
      });
      const data = await response.json();
      setAnalysisData(data);
    } catch (error) {
      console.error('Error generating analysis:', error);
      setStatusMessage('Failed to generate analysis.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRunValuation = async () => {
    if (!analysisData) {
      alert('Please generate the initial analysis first.');
      return;
    }
    // Reset states for a new valuation run
    setLogMessages([]);
    setValuationData(null);
    setConversationLog([]);
    setIsValuating(true);
    setStatusMessage('');

    const payload = {
      analysis_data: analysisData,
      metric_value: metricValue,
    };
    console.log("SENDING THIS TO BACKEND:", JSON.stringify(payload.analysis_data, null, 2));

    try {
      const response = await fetch('http://localhost:5001/api/run_valuation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload), 
      });

      const data = await response.json();

      if (!response.ok) {
        throw data;
      }
      
      setValuationData(data);
      setConversationLog(data.conversation_log || []); // Set the conversation log from the response
      if (data.traceability_log) {
        setLogMessages(data.traceability_log.split('\n'));
      } else {
        setLogMessages(['Log not available.']);
      }

    } catch (error) {
      console.error('Error running valuation:', error);
      setValuationData(error); 
      setConversationLog(error.conversation_log || []); // Also try to set log on error
      const errorLog = error.raw_output || 'An unexpected error occurred. Check the backend console for details.';
      setLogMessages([`Error: ${error.error || 'Unknown Error'}`, errorLog]);
    } finally {
      setIsValuating(false);
    }
  };

  const handleUpdateStep = (stepId, updatedData) => {
    const newSteps = analysisData.steps.map(step => 
      step.id === stepId ? { ...step, ...updatedData } : step
    );
    setAnalysisData({ ...analysisData, steps: newSteps });
  };

  const handleSubmitFeedback = async () => {
      setStatusMessage('Feedback submitted. Thank you!');
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Impact Analysis & Valuation</h1>
        <p>Enter a company website to begin the AI-powered impact analysis.</p>
      </header>

      <div className="input-section">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter website URL"
        />
        <button onClick={handleGenerate} disabled={isLoading}>
          {isLoading ? 'Analyzing...' : '1. Generate Impacts'}
        </button>
      </div>

      {isLoading && <div className="loader"></div>}

      {analysisData && (
        <div className="analysis-container">
          <div className="valuation-section">
            <h2>Financial Valuation</h2>
            <p>Once satisfied, provide a quantity for the primary impact and run the valuation.</p>
            
            <div className="valuation-input-group">
              <label htmlFor="metricValue">Metric Quantity:</label>
              <input
                id="metricValue"
                type="number"
                value={metricValue}
                onChange={(e) => setMetricValue(Number(e.target.value))}
                placeholder="e.g., 100"
              />
            </div>
            
            <button onClick={handleRunValuation} disabled={isValuating}>
              {isValuating ? 'Valuating...' : '2. Run Financial Valuation'}
            </button>
          </div>
          
          {isValuating && <div className="loader"></div>}
          
          {valuationData && (
            <>
              <ValuationReport data={valuationData} />
            </>
          )}

          <h2 className="feedback-title">Impact Identification Feedback</h2>
          {analysisData.steps.map((step, index) => (
            <FeedbackSection
              key={step.id}
              stepData={step}
              onUpdate={(updatedData) => handleUpdateStep(step.id, updatedData)}
              context={analysisData.steps.slice(0, index).map(s => s.response).join('\n\n')}
            />
          ))}
          <button className="submit-button" onClick={handleSubmitFeedback}>
            Finish and Submit All Feedback
          </button>
        </div>
      )}
      {statusMessage && <p className="status-message">{statusMessage}</p>}
    </div>
  );
}

export default App;