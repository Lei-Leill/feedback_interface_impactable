import React, { useState } from 'react';

function FeedbackSection({ stepData, onUpdate, context }) {
  const [prompt, setPrompt] = useState(stepData.prompt);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    try {
      const response = await fetch('http://localhost:5001/api/regenerate_step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stepId: stepData.id,
          prompt: prompt,
          context: context // Send previous AI outputs as context
        }),
      });
      const data = await response.json();
      // Update the parent state with the new prompt and response
      onUpdate({ prompt: prompt, response: data.response });
    } catch (error) {
      console.error('Error regenerating step:', error);
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="feedback-section">
      <h3>{stepData.title}</h3>
      <div className="two-column-layout">
        <div className="column">
          <h4>Prompt</h4>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows="15"
          />
          <button onClick={handleRegenerate} disabled={isRegenerating}>
            {isRegenerating ? '...' : 'Regenerate with this Prompt'}
          </button>
        </div>
        <div className="column">
          <h4>AI Generated Result</h4>
          <div className="response-box">{stepData.response}</div>
          <div className="feedback-inputs">
            <label>Rating (1-5):</label>
            <input
              type="number"
              min="1"
              max="5"
              value={stepData.rating}
              onChange={(e) => onUpdate({ rating: parseInt(e.target.value, 10) })}
            />
            <label>Comments:</label>
            <textarea
              value={stepData.comments}
              onChange={(e) => onUpdate({ comments: e.target.value })}
              rows="3"
              placeholder="Provide qualitative feedback here..."
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default FeedbackSection;