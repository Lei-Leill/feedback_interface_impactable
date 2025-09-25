# Overview

A full-stack application featuring a React frontend and a Python/Flask backend that uses AI to generate quantifiable impact metrics by analyzing a company's website.

The Backend:

- [X] Utilize a multi-agent setup with autogen and Perplexity API to generate the impact analysis. 
- [X] Grounded by dynamic examples from a Bubble.io database.
- [X] Provides a REST API for the frontend to use.

The Frontend (React):

- [X] Provides a clean, intuitive user interface for entering a URL.
- [X] Communicates with the backend to fetch and display the impact analysis.
- [X] Allows users to review the results.



# How to run the WebApp

1. Git clone the repository

2. Create an .env file on your local machine with API keys
```
BUBBLE_API_TOKEN = ""
PERPLEXITY_API_KEY = ""
```

3. Make sure you have all the library installed in your environment, e.g. react

4. Open up a terminal, and start the backend server
```
python3 backend.py
```

5. Open up another terminal to start the front-end
```
cd react-feedback-page
npm start
```

# Structure of the Code

```
feedback-interface-impactable/
├── .env    <-- You have to create this on your local machine with API keys
├── .gitignore          
├── backend.py              <-- main Flask app
└── bubble_helper.py    <-- helper functions for parsing bubble data 
└── 📁react-feedback
└───── src 
└─────── App.js      <-- Front-end main file
└─────── ValuationReport.js  
└─────── FeedbackSEction.js
└─────── App.css     <-- Styling
```

# Demo

# Future Directions
1. How to effectively incorporate human feedback to keep the AI improving? 
Create a database for AI to learn about its own good (bad) examples for continuous learning
2. More Detailed Loading States to keep user engaged and understand what the backend is currently doing. This can greatly improve user experience
3. Consideration of Tokens: Using vectorized databases for RAG to reduce token usage and ground results with similar companies’ data.
4. How to make the AI generate a stably good answer? Since AI can generate way different results for a single company, that makes it unreliable
