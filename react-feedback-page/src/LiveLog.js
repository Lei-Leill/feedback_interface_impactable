import React, { useEffect, useRef } from 'react';
import './LiveLog.css';

function LiveLog({ messages }) {
  const logEndRef = useRef(null);

  // Automatically scroll to the bottom when new messages arrive
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="live-log-container">
      <h3>Agent Process Log</h3>
      <pre className="log-box">
        {messages.map((msg, index) => (
          <div key={index}>{msg}</div>
        ))}
        <div ref={logEndRef} />
      </pre>
    </div>
  );
}

export default LiveLog;