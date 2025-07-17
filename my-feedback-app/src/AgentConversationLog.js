import React from 'react';
import './AgentConversationLog.css';

function AgentConversationLog({ log }) {
  if (!log || log.length === 0) {
    return null; // Don't render anything if there's no log
  }

  // Helper to format the content for display
  const formatContent = (content) => {
    if (typeof content === 'string') {
      return content;
    }
    // Pretty-print JSON objects for readability
    return JSON.stringify(content, null, 2);
  };

  return (
    <div className="log-container report-section">
      <h3>Agent Conversation Log</h3>
      <div className="log-entries">
        {log.map((entry, index) => (
          <div key={index} className={`log-entry log-entry-${entry.type}`}>
            <div className="entry-header">
              <span className="agent-name">{entry.agent}</span>
              <span className="entry-type">{entry.type}</span>
            </div>
            <pre className="entry-content">
              <code>{formatContent(entry.content)}</code>
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AgentConversationLog;