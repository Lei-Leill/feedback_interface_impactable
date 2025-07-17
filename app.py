import os
import requests
import json
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- Basic App Setup ---
app = Flask(__name__)
CORS(app)

# --- Perplexity AI Configuration ---
PERPLEXITY_API_KEY = "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"
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# --- PROMPT STORAGE ---
PROMPTS = {
    "persona": """You are an expert evaluator supporting an impact analysis task. Your job is to generate a structured list of:

1. **Metrics**
2. **Counterfactuals**
3. **First-order outcomes**
4. **Second-order outcomes**
5. **Cost**

All four categories must be **quantifiable**, **clearly named**, and use **industry-standard units**—so they can later be cross-validated with publicly available data.

### 🎯 Objective
Each item should directly relate to the company’s measurable activities. Your naming must support real-world data discovery—so avoid vague, abstract, or uncommonly tracked concepts.

### Language
Please use clear and simple language that's easy to understand. Wording such as "1.5 incidents increased Aerial firefighting efficiency" is not acceptible

### ⚠️ Prioritize Understanding of Invalid Examples
Below are correct and incorrect examples.  Please pay close attention to the relationships among metrics, counterfactuals, first-order outcomes, second-order outcomes, and costs. Study the **wrong examples especially carefully**. They reveal common logic flaws and will help you avoid similar errors. Understanding **why** something is wrong is more important than simply copying what is correct.

### Logic Breakdown with definition and logic chain 
Example Company: Drone-based wildfire suppression system
1. Metrics: 
- Measurable indicators used to assess success due to the company's product or service
- Unit: Define base unit
   e.g. Number of hours to extinguish a wildfire.

2. Counterfactuals: 
- What would have happened without the company's product or service intervention.
- Unit: Same as Metric Unit
  e.g. Number of hours to extinguish a wildfire with traditional approach (ground-based)

3. First-order outcomes: 
- The direct impact: Net difference between the Metric and Counterfactual. 
- Unit: Same as Metric Unit
  e.g. Number of hours wildfire extinguished shortened

4. Second-order outcomes: 
- Indirect consequences resulting from the first-order outcomes.
- Unit: Derived per unit of first-order outcome.
  e.g. Acres of land saved **per hour**; Number of properties protected **per hour**; CO2 emissions avoided **per hour**

5. Costs: 
- Resources needed to enable the intervention
- Unit: Typically monetary ($), may also be per metric or outcome unit
  e.g. Drone purchase and maintenance, AI monitoring, operator training.

### 💡 Naming Guidance
Think ahead: names must help us find data for counterfactuals and second-order outcomes later. For example, "Number of Products Manufactured with Traditional Leather" is bad, because "number of products manufactured" is not a publicly reported metric. Use commonly measurable units like "tonnes," "square meters," or "liters" when possible.

When generating names, it is important to remember that we do so to search for quantifiable values for counterfactuals and Second Order Outcomes on the internet later. This means that names and units of measurement must be meaningful, commonly used in the industry, and frequently employed in statistics.
When generating metrics, think in advance about generating and finding values for counterfactuals and Second Order Outcomes later.
For example, the counterfactual "Number of Products Manufactured Using Traditional Leather [items]" is problematic because we will not find quantifiable values on the internet, as "Number of Products Manufactured" is not commonly measured. Thus, the metric "Number of Products Manufactured Using the Company's Material [items]" is not relevant.


We will analyze and name each item one by one. Please confirm that you have understood the overall objective, the process, and the examples. Respond with "Let's start" when you are ready to begin the process.
""",
    "summarize_website": "Summarize the following website content in a concise and informative way, focusing on the company's primary product or service and its direct impact.",
    "generate_metrics": """great. now Develop a Comprehensive Metric List for Impact Analysis.

Your task is to compile a detailed list of metrics (max 3) to analyze a company's impact on people, the environment, or society, focusing on the direct outcomes of the company's products or services. This list should include metrics that are measurable, specific, and directly tied to the company's offerings. Avoid metrics that are outcomes of outcomes, such as environmental or social impacts, and focus solely on the primary metrics related to the company's offerings.

**Requirements:**

1. **Metric Identification:** Identify metrics that directly measure the impact of the company's offerings, such as tonnes of product sold, number of services rendered, students enrolled, users subscribed, etc. (which is applicable).
   
2. **Measurement Units:** For each metric, provide up to three applicable units of measurement, for example: Tonnes, Liters, People, KWH, Incidents, Square Meters, Hectares, Hours, KM, Companies, but not monetary or currency units. Ensure these units are relevant and unique to each metric.

3. **Exclusions:** - Avoid high-level impact narratives (e.g., environmental conservation, social impact).
    - Exclude metrics related to production values, operational procedures, or internal company affairs.
    - Do not include metrics implying calculations or measured in currency.
    - Ensure metrics are high-level and do not encompass other metrics within them.

5. **Format:**
- Keep metrics short. Limit their length to a maximum of 8 words.
- For each metric, list up to 3 measurement units
   
Ensure no outcomes, duplicated metrics, or irrelevant units of measurement are included. The goal is to have a concise, clear list that can be used to calculate the company's impact accurately.

No pre-text, no post-text in output. Limit the output to a maximum of 1000 characters.
""",
    "critique_metrics": "Now, critique and revise the metrics you just generated to ensure they meet all the requirements previously outlined. Output only the corrected list in the original format.",
    "generate_counterfactuals": """great. now Create a list of the top 2 counterfactual scenarios for each metric that illustrate what would likely happen if the product or service being measured by the metric (identified as "[Metric Name]") did not exist.

**Key Aspects to Consider:**

1. **Understanding Buyer Behavior:** Identify what alternatives or current preferences buyers would likely lean towards if the "[Metric Name]" were absent, focusing on their existing habits or market norms.

2. **Criteria for Selection:**
   - **Relevance:** Each counterfactual should directly relate to the buyer's alternative options without the "[Metric Name]".
   - **Current Actions:** Highlight what buyers are currently involved in or would revert to in the absence of the "[Metric Name]".
   - **Measurability:** Counterfactuals should be quantifiable, utilizing "[Metric Unit]" for consistency.


3. **Important Considerations:**
   - Avoid referencing the cost or price aspects of the product or service.
   Counterfactuals should not imply "Purchase," "Sales," or "Consumption," etc. Instead, counterfactuals should refer to common industry totals, such as "Total Production," "Total Number of People," "Total Hectares," etc.
   - Include at least one counterfactual indicating a scenario where the absence of the product or service leads to a lack of certain actions or outcomes.

4. **Formulation Guide:**
   - Consider what current solutions or preferences buyers might stick with in the absence of the company's offerings.
   - Reflect on broader market trends and societal norms influencing buyer choices.
   - Review existing data ([Correct Examples]) for inspiration and to ensure creativity and alignment.
   - Always incorporate the buyer's perspective by asking, "What would buyers otherwise opt for or do? What are their current actions?"

5. **Format:**
  - Keep counterfactuals short. Limit their length to a maximum of 8 words.

5. **Output Format:** - Output the list of metrics along with list of their corresponding counterfactuals. 

  No pre-text, no post-text in output. Limit the output to a maximum of 1000 characters.
""",
    "critique_counterfactuals": "Now, critique and revise the counterfactuals you just generated. Output only the corrected list in the original format.",
    "generate_first_order": """Great. Now identify the *First Order Outcome* that captures the immediate and measurable impact of implementing a specific metric, compared to its defined counterfactual.

The First Order Outcome must:
- Represent the **net change** between the metric and counterfactual.
- Be measured in the **same unit** as both the metric and counterfactual.
- Clearly indicate the **direction of change**:
  – If the metric value is *lo wer* than the counterfactual → use "decrease" or "reduction"
  – If the metric value is *higher* than the counterfactual → use "increase" or "growth"
- Use a short and intuitive name (max 8 words), understandable to the general public.

**Output Format:** For each entry:
- Metric  
- Corresponding Counterfactual(s)  
- First Order Outcome (include the direction of change)

No intro or conclusion text. Keep total output under 1000 characters.
""",
    "critique_first_order": "Now, critique and revise the First Order Outcomes you just generated. Output only the corrected list in the original format.",
    "generate_second_order": """Now, based on each First Order Outcome, identify the top **3 distinct, quantifiable Second Order Outcomes** that result indirectly from that outcome.

Each Second Order Outcome must:
- Be logically caused by the First Order Outcome.
- Be **expressed per unit** of the First Order Outcome.
- Use a clear and specific name (max 8 words).
- Use a measurement unit selected from this list: Tonnes, Liters, People, KWH, Incidents, Square Meters, Hectares, Hours, KM, Companies.
- Avoid repetition, vagueness, or generic phrasing.

**Output Format:** For each metric:  
- List its counterfactual(s)  
- Include the associated First Order Outcome  
- Provide 3 distinct Second Order Outcomes (with their measurement units) under each First Order Outcome

Do not include any intro or explanation text.
""",
    "critique_second_order": "Now, critique and revise the Second Order Outcomes you just generated. Output only the corrected list in the original format.",
    
    # --- VALUATION AGENT PROMPTS ---
    "val_identify_impacts": """Analyze the provided data to extract ONE key societal or environmental impact. Provide a precise description of the impact and its standard unit of measurement. Your output MUST be a valid JSON object. Example: {{\"description\": \"Reduction in wildfire response time\", \"unit\": \"hours\"}}""",

    # --- NEW VALUATION PIPELINE PROMPTS ---
    "val_research_counterfactuals": """For the impact '{description}', which represents a baseline performance, identify the top 2 most likely counterfactual scenarios that would have occurred without the company's intervention.
A counterfactual is what would have happened anyway. For each scenario:
1. Provide a brief, realistic description.
2. Estimate the outcome value in the same unit ('{unit}'). This value represents the performance of the alternative scenario (e.g., if the metric is 'hours to extinguish fire', a higher value means it's worse).
3. Estimate the probability of this scenario occurring (as a decimal). The probabilities for all scenarios you list MUST sum to 1.0.

Your output MUST be a valid JSON list of objects.
Example for an impact of 'Time to extinguish wildfire':
[
  {{
    "scenario": "Traditional ground-based firefighting response",
    "value": 150,
    "probability": 0.6
  }},
  {{
    "scenario": "Delayed response due to reliance on regional government aerial support",
    "value": 120,
    "probability": 0.4
  }}
]
""",

    "val_find_monetary_value_per_unit": """For the first-order outcome of '{outcome_description}' measured in '{unit}', find a single, justifiable monetary value per unit.
Your primary goal is to find a proxy from a reliable source like an economic study, government report, academic paper, or industry analysis.
Prioritize direct costs, but you may use well-established social cost estimates (e.g., Social Cost of Carbon) if applicable.

Your output MUST be a single JSON object with the following keys:
- "value": A single number (float or integer).
- "currency": The currency code (e.g., "USD").
- "source": A brief description of the source (e.g., "U.S. Forest Service, 2023 Economic Impact Report").
- "reasoning": A short sentence explaining why this proxy is relevant.

Example:
{{
  "value": 45000,
  "currency": "USD",
  "source": "RAND Corporation study on wildfire economics",
  "reasoning": "This value represents the average economic damage, including property and infrastructure, per hour a large wildfire burns."
}}
""",

    # --- AGGREGATION & REPORTING PROMPTS ---
    "val_sensitivity_analysis": """Perform a sensitivity analysis on the final valuation by varying the key underlying assumptions. The key assumptions are the values and probabilities in the counterfactual analysis and the monetary value per unit. Provide a credible range (min and max) for the final valuation and explain which assumption has the greatest influence. Your output MUST be a single JSON object with 'base_value', 'min_value', 'max_value', and 'key_sensitivities' (list of strings) keys.""",
    "val_generate_report": """Generate a comprehensive, expert-level written report section explaining the quantified societal and environmental impact. This narrative must clearly justify the methodology, the counterfactual scenarios chosen, the monetization proxy used, all assumptions made, and explicitly state any limitations or uncertainties. The report should be clear, logical, and suitable for a client seeking in-depth analysis.""",
    "val_traceability_log": """Compile a meticulous audit trail of all data sources, calculations, and transformations used in the valuation. Include the metric, counterfactuals (with values and probabilities), the calculated first-order outcome, and the monetization proxy (with its source). Format as a markdown list."""
}


# --- Core AI Function ---
def call_perplexity(messages, temperature=0.2, max_tokens=2000):
    if not PERPLEXITY_API_KEY:
        return "Error: PERPLEXITY_API_KEY is not set."
    
    payload = {
        "model": "sonar-pro",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(PERPLEXITY_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Error from API: {response.status_code}, {response.text}")
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"Error calling API: {e}"

# ========== AGENT FUNCTIONS ==========
def agent_parse_and_summarize(url):
    """
    Agent 1: Fetches website content, parses it, and asks the AI to summarize it.
    """
    print("AGENT: Parsing and Summarizing Website...")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        raw_text = soup.get_text(separator='\n', strip=True)
        
        summary = call_perplexity([
            {"role": "system", "content": PROMPTS["summarize_website"]},
            {"role": "user", "content": raw_text[:16000]}
        ])
        return summary
    except Exception as e:
        print(f"Error in parsing agent: {e}")
        return f"Error parsing website: {str(e)}"

def run_agent_step(conversation_history, generation_prompt_key, critique_prompt_key):
    """
    A generic function to run a standard "generate and critique" sequence.
    """
    conversation_history.append({"role": "user", "content": PROMPTS[generation_prompt_key]})
    generated_text = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": generated_text})
    
    conversation_history.append({"role": "user", "content": PROMPTS[critique_prompt_key]})
    critiqued_text = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": critiqued_text})
    
    return critiqued_text


# ========== API ENDPOINT (The "Manager") ==========
@app.route('/api/generate_all', methods=['POST'])
def generate_all():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    print(f"MANAGER: Starting new analysis for URL: {url}")
    
    # This is our conversation history, which we will manage carefully.
    conversation_history = []

    # --- Step 0: Persona Setup ---
    # The persona prompt is the foundational "system" message.
    conversation_history.append({"role": "system", "content": PROMPTS["persona"]})
    
    # --- Step 1: Website Parsing & Summarization ---
    summary = agent_parse_and_summarize(url)
    if summary.startswith("Error"):
        return jsonify({"error": summary}), 500

    # --- FIX: The 'run_agent_step' helper function was removed. ---
    # We now handle the conversation flow directly here to ensure roles alternate correctly.
    
    # --- Step 2: Generate and Critique Metrics ---
    print("MANAGER: Calling Metrics Agent...")
    # Combine the summary and the first prompt into a single 'user' message.
    first_user_prompt = f"Here is the summary of the company's website ({url}):\n\n{summary}\n\n{PROMPTS['generate_metrics']}"
    conversation_history.append({"role": "user", "content": first_user_prompt})
    # First call to AI
    metrics_generation = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": metrics_generation})
    # Now we can add another 'user' message for the critique.
    conversation_history.append({"role": "user", "content": PROMPTS["critique_metrics"]})
    # Second call to AI
    metrics_result = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": metrics_result})

    # --- Step 3: Generate and Critique Counterfactuals ---
    print("MANAGER: Calling Counterfactuals Agent...")
    conversation_history.append({"role": "user", "content": PROMPTS["generate_counterfactuals"]})
    counterfactuals_generation = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": counterfactuals_generation})
    
    conversation_history.append({"role": "user", "content": PROMPTS["critique_counterfactuals"]})
    counterfactuals_result = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": counterfactuals_result})
    
    # --- Step 4: Generate and Critique First-Order Outcomes ---
    print("MANAGER: Calling First-Order Outcome Agent...")
    conversation_history.append({"role": "user", "content": PROMPTS["generate_first_order"]})
    first_order_generation = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": first_order_generation})

    conversation_history.append({"role": "user", "content": PROMPTS["critique_first_order"]})
    first_order_result = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": first_order_result})
    
    # --- Step 5: Generate and Critique Second-Order Outcomes ---
    print("MANAGER: Calling Second-Order Outcome Agent...")
    conversation_history.append({"role": "user", "content": PROMPTS["generate_second_order"]})
    second_order_generation = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": second_order_generation})

    conversation_history.append({"role": "user", "content": PROMPTS["critique_second_order"]})
    second_order_result = call_perplexity(conversation_history)
    conversation_history.append({"role": "assistant", "content": second_order_result})

    print("MANAGER: Pipeline complete. Formatting response for frontend.")
    
    # Structure the final output for the React front-end
    response_data = {
        "url": url,
        "steps": [
            {"id": "metric", "title": "Metric", "prompt": PROMPTS['generate_metrics'], "response": metrics_result, "rating": 0, "comments": ""},
            {"id": "counterfactual", "title": "Counterfactual", "prompt": PROMPTS['generate_counterfactuals'], "response": counterfactuals_result, "rating": 0, "comments": ""},
            {"id": "first_order", "title": "First-Order Outcome", "prompt": PROMPTS['generate_first_order'], "response": first_order_result, "rating": 0, "comments": ""},
            {"id": "second_order", "title": "Second-Order Outcome", "prompt": PROMPTS['generate_second_order'], "response": second_order_result, "rating": 0, "comments": ""}
        ]
    }
    
    return jsonify(response_data)

# The regenerate_step and submit_feedback endpoints remain unchanged.
@app.route('/api/regenerate_step', methods=['POST'])
def regenerate_step():
    data = request.get_json()
    new_prompt = data.get('prompt')
    context = data.get('context', "") 
    
    messages_for_regen = [
        {"role": "system", "content": f"You are an AI assistant. Here is the context from the previous steps:\n{context}"},
        {"role": "user", "content": new_prompt}
    ]
    
    new_response = call_perplexity(messages_for_regen)
    
    return jsonify({"response": new_response})

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    final_data = request.get_json()
    print("Received final feedback for submission:")
    print(json.dumps(final_data, indent=2))
    
    # TODO: Add logic to save this data to your AWS SQL database.
    
    return jsonify({"status": "success", "message": "Feedback submitted successfully."})

## Important Feature for Valuation
def format_prompt(prompt_template, data_dict):
    """
    Safely replaces placeholders in a prompt template with values from a dictionary.
    Placeholders in the prompt should be like {key_name}.
    """
    prompt = prompt_template
    for key, value in data_dict.items():
        placeholder = f"{{{key}}}"
        prompt = prompt.replace(placeholder, str(value))
    return prompt

# Add this new function to app.py
def clean_and_parse_json(ai_string):
    """
    The definitive function to clean and parse messy AI JSON output.
    It handles markdown fences, extra prose, and missing list brackets.
    """
    # In case there is comment in the json format
    lines = ai_string.split('\n')
    # For each line, split it at the comment marker and take the first part.
    filtered_lines = [line.split('//')[0] for line in lines]
    ai_string = '\n'.join(filtered_lines)

    # 1. First, try to extract content from markdown fences if they exist.
    if '```json' in ai_string:
        try:
            # Takes the content between ```json and ```
            ai_string = ai_string.split('```json')[1].split('```')[0]
        except IndexError:
            # If the format is weird, fallback to finding the main JSON block
            pass
            
    # 2. Find the start and end of the main JSON content (list or object)
    # This effectively strips away any leading/trailing prose.
    start = ai_string.find('{')
    if start == -1:
        start = ai_string.find('[')
    
    end = ai_string.rfind('}')
    if end == -1:
        end = ai_string.rfind(']')

    if start != -1 and end != -1:
        ai_string = ai_string[start:end+1]
    
    # 3. Clean and attempt to parse
    try:
        # Remove any lingering underscores from numbers
        cleaned_text = ai_string.replace("_", "")
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        # If it fails, it might be a list of objects without the outer brackets
        try:
            # Wrap in brackets and try again
            cleaned_text = f"[{ai_string.replace('_', '')}]"
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            # If it still fails, then the format is truly broken
            print(f"JSON PARSING FAILED for string: {ai_string}\nError: {e}")
            return None

@app.route('/api/run_valuation', methods=['POST'])
def run_valuation():
    """
    This endpoint implements the new, direct valuation pipeline based on counterfactual analysis.
    """
    data = request.get_json()
    initial_ai_outputs = data.get('analysis_data')
    metric_value = data.get('metric_value', 100) 

    if not initial_ai_outputs:
        return jsonify({"error": "Initial analysis data ('analysis_data') is required."}), 400
    
    # List to store the full conversation log
    conversation_log = []
    
    log_entry = f"Starting new valuation pipeline with metric value: {metric_value}"
    print(f"VALUATION MANAGER: {log_entry}")
    conversation_log.append({"agent": "Manager", "type": "start", "content": log_entry})
    
    # === AGENT 1: IMPACT IDENTIFICATION ===
    impacts_prompt = PROMPTS["val_identify_impacts"] + "\n\nHere is the data to analyze:\n" + json.dumps(initial_ai_outputs)
    conversation_log.append({"agent": "Impact ID Agent", "type": "prompt", "content": "Analyze data to find one key impact and unit."})
    
    impact_text = call_perplexity([{"role": "user", "content": impacts_prompt}])
    impact = clean_and_parse_json(impact_text)
    
    if not impact or not isinstance(impact, dict) or 'description' not in impact or 'unit' not in impact:
        err_msg = "Agent 1 (Impact Identification) failed to return a valid impact object."
        conversation_log.append({"agent": "Manager", "type": "error", "content": err_msg})
        return jsonify({"error": err_msg, "raw_output": impact_text}), 500

    conversation_log.append({"agent": "Impact ID Agent", "type": "response", "content": impact})
    impact['quantity'] = metric_value 
    log_entry = f"Identified Impact: {impact['description']} ({impact['quantity']} {impact['unit']})"
    print(f"[Manager] {log_entry}")
    conversation_log.append({"agent": "Manager", "type": "info", "content": log_entry})

    valuation_details = {"metric": impact}

    # === AGENT 2: COUNTERFACTUAL RESEARCH ===
    cf_prompt = format_prompt(PROMPTS["val_research_counterfactuals"], impact)
    conversation_log.append({"agent": "Counterfactual Agent", "type": "prompt", "content": "Research counterfactual scenarios, values, and probabilities."})
    
    cf_scenarios_text = call_perplexity([{"role": "user", "content": cf_prompt}])
    counterfactual_scenarios = clean_and_parse_json(cf_scenarios_text)

    if not counterfactual_scenarios or not isinstance(counterfactual_scenarios, list):
         err_msg = "Agent 2 (Counterfactual Research) failed to return valid scenarios."
         conversation_log.append({"agent": "Manager", "type": "error", "content": err_msg})
         return jsonify({"error": err_msg, "raw_output": cf_scenarios_text}), 500
    
    conversation_log.append({"agent": "Counterfactual Agent", "type": "response", "content": counterfactual_scenarios})
    valuation_details["counterfactual_analysis"] = counterfactual_scenarios

    # === CALCULATION STEP 3: WEIGHTED COUNTERFACTUAL & FIRST-ORDER OUTCOME ===
    try:
        weighted_counterfactual_value = sum(s.get('value', 0) * s.get('probability', 0) for s in counterfactual_scenarios)
        first_order_outcome_value = weighted_counterfactual_value - impact['quantity']
        first_order_outcome_desc = f"Net improvement over counterfactuals for '{impact['description']}'"
        first_order_outcome = {"description": first_order_outcome_desc, "value": first_order_outcome_value, "unit": impact['unit']}
        
        valuation_details["first_order_outcome"] = first_order_outcome
        log_entry = f"Calculated First-Order Outcome: {first_order_outcome_value:.1f} {impact['unit']}"
        print(f"[Manager] {log_entry}")
        conversation_log.append({"agent": "Calculation Step", "type": "calculation", "content": log_entry})
    except (TypeError, KeyError) as e:
        err_msg = f"Failed to calculate weighted counterfactual. Error: {e}"
        conversation_log.append({"agent": "Manager", "type": "error", "content": err_msg})
        return jsonify({"error": err_msg, "data": counterfactual_scenarios}), 500

    # === AGENT 4: MONETIZATION RESEARCH ===
    monetization_prompt_data = {"outcome_description": first_order_outcome["description"], "unit": first_order_outcome["unit"]}
    monetization_prompt = format_prompt(PROMPTS["val_find_monetary_value_per_unit"], monetization_prompt_data)
    conversation_log.append({"agent": "Monetization Agent", "type": "prompt", "content": "Find a monetary value per unit for the first-order outcome."})
    
    monetary_value_text = call_perplexity([{"role": "user", "content": monetization_prompt}])
    monetary_value_per_unit = clean_and_parse_json(monetary_value_text)

    if not monetary_value_per_unit or 'value' not in monetary_value_per_unit:
        err_msg = "Agent 4 (Monetization Research) failed to return a valid monetary value."
        conversation_log.append({"agent": "Manager", "type": "error", "content": err_msg})
        return jsonify({"error": err_msg, "raw_output": monetary_value_text}), 500
    
    conversation_log.append({"agent": "Monetization Agent", "type": "response", "content": monetary_value_per_unit})
    valuation_details["monetization"] = monetary_value_per_unit

    # === CALCULATION STEP 5: FINAL VALUATION ===
    try:
        final_usd_value = first_order_outcome["value"] * monetary_value_per_unit["value"]
        valuation_details["final_valuation"] = {"value": final_usd_value, "currency": monetary_value_per_unit.get("currency", "USD")}
        log_entry = f"Calculated Final Valuation: {final_usd_value:,.1f} {monetary_value_per_unit.get('currency', 'USD')}"
        print(f"[Manager] {log_entry}")
        conversation_log.append({"agent": "Calculation Step", "type": "calculation", "content": log_entry})
    except (TypeError, KeyError) as e:
        err_msg = f"Failed to calculate final valuation. Error: {e}"
        conversation_log.append({"agent": "Manager", "type": "error", "content": err_msg})
        return jsonify({"error": err_msg}), 500
        
    # === FINAL AGGREGATION & REPORTING ===
    conversation_log.append({"agent": "Manager", "type": "info", "content": "Generating final report and analysis."})
    
    sa_prompt_data = {"consolidated_value": valuation_details["final_valuation"]["value"]}
    sa_prompt = format_prompt(PROMPTS["val_sensitivity_analysis"], sa_prompt_data)
    value_range_analysis = clean_and_parse_json(call_perplexity([{"role": "user", "content": sa_prompt}]))

    report_data_for_ai = {"valuation_details": valuation_details, "value_range_analysis": value_range_analysis}
    report_prompt = PROMPTS["val_generate_report"] + "\n\nUse this data to generate the report:\n" + json.dumps(report_data_for_ai)
    trace_prompt = PROMPTS["val_traceability_log"] + "\n\nUse this data to generate the log:\n" + json.dumps(report_data_for_ai)
    
    report_narrative = call_perplexity([{"role": "user", "content": report_prompt}])
    traceability_log = call_perplexity([{"role": "user", "content": trace_prompt}])

    final_valuation_result = {
        "final_valuation": valuation_details["final_valuation"],
        "value_range_analysis": value_range_analysis,
        "report_narrative": report_narrative,
        "traceability_log": traceability_log,
        "valuation_pipeline_details": valuation_details,
        "conversation_log": conversation_log # Include the log in the response
    }
    
    return jsonify(final_valuation_result)


if __name__ == '__main__':
    app.run(debug=True, port=5001)