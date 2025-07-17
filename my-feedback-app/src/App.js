// import logo from './logo.svg';
// import './App.css';

// function App() {
//   return (
//     <div className="App">
//       <header className="App-header">
//         <img src={logo} className="App-logo" alt="logo" />
//         <p>
//           Edit <code>src/App.js</code> and save to reload.
//         </p>
//         <a
//           className="App-link"
//           href="https://reactjs.org"
//           target="_blank"
//           rel="noopener noreferrer"
//         >
//           Learn React
//         </a>
//       </header>
//     </div>
//   );
// }

// export default App;
/*
import React, { useState } from 'react';
import FeedbackSection from './FeedbackSection';
import ValuationReport from './ValuationReport'; 
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [analysisData, setAnalysisData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [valuationData, setValuationData] = useState(null);
  const [isValuating, setIsValuating] = useState(false);


  const handleGenerate = async () => {
    if (!url) {
      alert('Please enter a website URL.');
      return;
    }
    setIsLoading(true);
    setAnalysisData(null);
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
    setIsValuating(true);
    setValuationData(null);
    setStatusMessage('Running financial valuation pipeline...');

    try {
      const response = await fetch('http://localhost:5001/api/run_valuation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(analysisData), // Send initial analysis as input
      });
      const data = await response.json();
      setValuationData(data);
      setStatusMessage('Valuation complete.');
    } catch (error) {
      console.error('Error running valuation:', error);
      setStatusMessage('Failed to run valuation.');
    } finally {
      setIsValuating(false);
    }
  };

  const handleUpdateStep = (stepId, updatedData) => {
    // Update the master state with new prompt, response, rating, or comments
    const newSteps = analysisData.steps.map(step => 
      step.id === stepId ? { ...step, ...updatedData } : step
    );
    setAnalysisData({ ...analysisData, steps: newSteps });
  };

  const handleSubmitFeedback = async () => {
      setStatusMessage('Submitting feedback...');
      try {
          const response = await fetch('http://localhost:5001/api/submit_feedback', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(analysisData)
          });
          const result = await response.json();
          setStatusMessage(result.message);
      } catch (error) {
          console.error('Error submitting feedback:', error);
          setStatusMessage('Failed to submit feedback.');
      }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Impact Analysis Feedback Interface</h1>
        <p>Enter a company website to begin the AI-powered impact analysis.</p>
      </header>

      <div className="input-section">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter website URL (e.g., https://www.rain.aero/)"
        />
        <button onClick={handleGenerate} disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Analyze Website'}
        </button>
      </div>

      {isLoading && <div className="loader"></div>}

            {analysisData && (
        <div className="analysis-container">

        <div className="valuation-section">
            <h2>Financial Valuation</h2>
            <p>Once you are satisfied with the generated impacts, run the financial valuation pipeline.</p>
            <button onClick={handleRunValuation} disabled={isValuating}>
              {isValuating ? 'Valuating...' : '🚀 Run Financial Valuation'}
            </button>
          </div>
          
          {isValuating && <div className="loader"></div>}
          
          {valuationData && <ValuationReport data={valuationData} />}

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
*/

// import React, { useState, useEffect } from 'react';
// import { io } from 'socket.io-client';

// import FeedbackSection from './FeedbackSection';
// import ValuationReport from './ValuationReport';
// import LiveLog from './LiveLog';

// import './App.css';

// // Establish the socket connection. It's defined outside the component
// // so it doesn't reconnect on every re-render.
// const socket = io('http://localhost:5001');

// function App() {
//   // State for the initial analysis
//   const [url, setUrl] = useState('');
//   const [analysisData, setAnalysisData] = useState(null);
//   const [isLoading, setIsLoading] = useState(false);

//   // State for the valuation process
//   const [isValuating, setIsValuating] = useState(false);
//   const [logMessages, setLogMessages] = useState([]);
//   const [valuationData, setValuationData] = useState(null);

//   // General status message state
//   const [statusMessage, setStatusMessage] = useState('');

//   // Effect hook to manage all Socket.IO event listeners
//   useEffect(() => {
//     // Listener for live status updates from the backend
//     socket.on('status_update', (data) => {
//       setLogMessages((prevMessages) => [...prevMessages, data.message]);
//     });

//     // Listener for when the final valuation result is ready
//     socket.on('valuation_complete', (data) => {
//       setValuationData(data);
//       setIsValuating(false);
//       setLogMessages((prev) => [...prev, '--- VALUATION COMPLETE ---']);
//     });
    
//     // Listener for when the backend reports a failure
//     socket.on('valuation_error', (data) => {
//         setIsValuating(false);
//         setLogMessages((prev) => [...prev, `--- ERROR: ${data.error} ---`]);
//         setValuationData(data); // Pass the error object to the report component
//     });

//     // Cleanup function to remove listeners when the component unmounts
//     return () => {
//       socket.off('status_update');
//       socket.off('valuation_complete');
//       socket.off('valuation_error');
//     };
//   }, []); // The empty dependency array means this effect runs only once

//   // Handler for the initial analysis generation
//   const handleGenerate = async () => {
//     if (!url) {
//       alert('Please enter a website URL.');
//       return;
//     }
//     setIsLoading(true);
//     setAnalysisData(null);
//     setValuationData(null); // Reset valuation data on a new run
//     setLogMessages([]);     // Reset logs
//     setStatusMessage('');

//     try {
//       const response = await fetch('http://localhost:5001/api/generate_all', { // Assuming you have this endpoint
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ url }),
//       });
//       const data = await response.json();
//       setAnalysisData(data);
//     } catch (error) {
//       console.error('Error generating analysis:', error);
//       setStatusMessage('Failed to generate analysis.');
//     } finally {
//       setIsLoading(false);
//     }
//   };
  
//   // Handler to start the valuation pipeline via WebSocket
//   const handleRunValuation = () => {
//     if (!analysisData) {
//       alert('Please generate the initial analysis first.');
//       return;
//     }
//     // Reset states for a new valuation run
//     setLogMessages([]);
//     setValuationData(null);
//     setIsValuating(true);

//     // Use socket.emit to send the data and trigger the backend process
//     socket.emit('run_valuation', analysisData);
//   };

//   const handleUpdateStep = (stepId, updatedData) => {
//     const newSteps = analysisData.steps.map(step => 
//       step.id === stepId ? { ...step, ...updatedData } : step
//     );
//     setAnalysisData({ ...analysisData, steps: newSteps });
//   };

//   const handleSubmitFeedback = async () => {
//       // ... (your feedback submission logic)
//   };

//   return (
//     <div className="app-container">
//       <header className="app-header">
//         <h1>Impact Analysis Feedback Interface</h1>
//         <p>Enter a company website to begin the AI-powered impact analysis.</p>
//       </header>

//       <div className="input-section">
//         <input
//           type="text"
//           value={url}
//           onChange={(e) => setUrl(e.target.value)}
//           placeholder="Enter website URL (e.g., https://www.patagonia.com)"
//         />
//         <button onClick={handleGenerate} disabled={isLoading}>
//           {isLoading ? 'Generating...' : 'Analyze Website'}
//         </button>
//       </div>

//       {isLoading && <div className="loader"></div>}

//       {analysisData && (
//         <div className="analysis-container">
//           <div className="valuation-section">
//             <h2>Financial Valuation</h2>
//             <p>Once you are satisfied with the generated impacts, run the financial valuation pipeline.</p>
//             <button onClick={handleRunValuation} disabled={isValuating}>
//               {isValuating ? 'Valuating...' : '🚀 Run Financial Valuation'}
//             </button>
//           </div>
          
//           {/* Conditionally render the live log while valuating */}
//           {isValuating && <LiveLog messages={logMessages} />}
          
//           {/* Conditionally render the final report when data is available */}
//           {valuationData && <ValuationReport data={valuationData} />}

//           <h2 className="feedback-title">Impact Identification Feedback</h2>
//           {analysisData.steps.map((step, index) => (
//             <FeedbackSection
//               key={step.id}
//               stepData={step}
//               onUpdate={(updatedData) => handleUpdateStep(step.id, updatedData)}
//               context={analysisData.steps.slice(0, index).map(s => s.response).join('\n\n')}
//             />
//           ))}
//           <button className="submit-button" onClick={handleSubmitFeedback}>
//             Finish and Submit All Feedback
//           </button>
//         </div>
//       )}
//       {statusMessage && <p className="status-message">{statusMessage}</p>}
//     </div>
//   );
// }

// export default App;


// import React, { useState } from 'react';

// import FeedbackSection from './FeedbackSection';
// import ValuationReport from './ValuationReport';
// import LiveLog from './LiveLog';

// import './App.css';

// function App() {
//   // State for the initial analysis
//   const [url, setUrl] = useState('');
//   const [analysisData, setAnalysisData] = useState(null);
//   const [isLoading, setIsLoading] = useState(false);

//   // State for the valuation process
//   const [isValuating, setIsValuating] = useState(false);
//   const [logMessages, setLogMessages] = useState([]);
//   const [valuationData, setValuationData] = useState(null);

//   // General status message state
//   const [statusMessage, setStatusMessage] = useState('');

//   // Handler for the initial analysis generation
//   const handleGenerate = async () => {
//     if (!url) {
//       alert('Please enter a website URL.');
//       return;
//     }
//     // Reset all states for a new run
//     setIsLoading(true);
//     setAnalysisData(null);
//     setValuationData(null);
//     setLogMessages([]);
//     setStatusMessage('');

//     try {
//       const response = await fetch('http://localhost:5001/api/generate_all', { // Assuming you have this endpoint
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ url }),
//       });
//       const data = await response.json();
//       setAnalysisData(data);
//     } catch (error) {
//       console.error('Error generating analysis:', error);
//       setStatusMessage('Failed to generate analysis.');
//     } finally {
//       setIsLoading(false);
//     }
//   };
  
//   // Handler to start the valuation pipeline
//   const handleRunValuation = async () => {
//     if (!analysisData) {
//       alert('Please generate the initial analysis first.');
//       return;
//     }
//     // Reset states for a new valuation run
//     setLogMessages([]);
//     setValuationData(null);
//     setIsValuating(true);
//     setStatusMessage('');

//     try {
//       const response = await fetch('http://localhost:5001/api/run_valuation', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify(analysisData),
//       });

//       const data = await response.json();

//       // If the server returns an error code (like 400 or 500), throw an error to be caught below
//       if (!response.ok) {
//         throw data;
//       }
      
//       // On success, set both the valuation data and the logs
//       setValuationData(data);
//       setLogMessages(data.log_messages || ['Log not available.']);

//     } catch (error) {
//       // Catch both network errors and errors thrown from a bad server response
//       console.error('Error running valuation:', error);
//       // Set the error data so the report component can display it
//       setValuationData(error); 
//       setLogMessages(error.log_messages || ['An unexpected error occurred. Check the backend console for details.']);
//     } finally {
//       setIsValuating(false);
//     }
//   };

//   const handleUpdateStep = (stepId, updatedData) => {
//     const newSteps = analysisData.steps.map(step => 
//       step.id === stepId ? { ...step, ...updatedData } : step
//     );
//     setAnalysisData({ ...analysisData, steps: newSteps });
//   };

//   const handleSubmitFeedback = async () => {
//       // Your feedback submission logic here
//       setStatusMessage('Feedback submitted. Thank you!');
//   };

//   return (
//     <div className="app-container">
//       <header className="app-header">
//         <h1>Impact Analysis & Valuation</h1>
//         <p>Enter a company website to begin the AI-powered impact analysis.</p>
//       </header>

//       <div className="input-section">
//         <input
//           type="text"
//           value={url}
//           onChange={(e) => setUrl(e.target.value)}
//           placeholder="Enter website URL"
//         />
//         <button onClick={handleGenerate} disabled={isLoading}>
//           {isLoading ? 'Analyzing...' : '1. Generate Impacts'}
//         </button>
//       </div>

//       {isLoading && <div className="loader"></div>}

//       {analysisData && (
//         <div className="analysis-container">
//           <div className="valuation-section">
//             <h2>Financial Valuation</h2>
//             <p>Once you are satisfied with the generated impacts, run the financial valuation pipeline.</p>
//             <button onClick={handleRunValuation} disabled={isValuating}>
//               {isValuating ? 'Valuating...' : '2. Run Financial Valuation'}
//             </button>
//           </div>
          
//           {/* If valuating, show a loading spinner */}
//           {isValuating && <div className="loader"></div>}
          
//           {/* Once complete (success or fail), render both the log and the report */}
//           {valuationData && (
//             <>
//               <LiveLog messages={logMessages} />
//               <ValuationReport data={valuationData} />
//             </>
//           )}

//           <h2 className="feedback-title">Impact Identification Feedback</h2>
//           {analysisData.steps.map((step, index) => (
//             <FeedbackSection
//               key={step.id}
//               stepData={step}
//               onUpdate={(updatedData) => handleUpdateStep(step.id, updatedData)}
//               context={analysisData.steps.slice(0, index).map(s => s.response).join('\n\n')}
//             />
//           ))}
//           <button className="submit-button" onClick={handleSubmitFeedback}>
//             Finish and Submit All Feedback
//           </button>
//         </div>
//       )}
//       {statusMessage && <p className="status-message">{statusMessage}</p>}
//     </div>
//   );
// }

// export default App;

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
              <LiveLog messages={logMessages} />
              <AgentConversationLog log={conversationLog} /> 
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