import os
import requests
import json
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
#from flask_socketio import SocketIO # <-- NEW IMPORT


# --- Basic App Setup ---
app = Flask(__name__)
CORS(app)

# --- Perplexity AI Configuration ---
#PERPLEXITY_API_KEY = "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"
PERPLEXITY_API_KEY = "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"
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

# --- PROMPT STORAGE ---
# A dictionary to hold all the specialized prompts for our agents with their full text.
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
    "val_identify_impacts": """Analyze the provided data to extract a clear list of specific positive societal and environmental impacts. For each impact, provide a precise description and its measured quantity with units. Your output MUST be a valid JSON list of objects. Example: [{{"description": "Reduced CO2 emissions", "quantity": 1000, "unit": "tons"}}]""",
    
    # --- NEW "VALUATION BRIDGE" PROMPTS ---
    "val_identify_consequences": """For the impact '{description}' (Quantity: {quantity} {unit}), what are the most direct, tangible economic or social consequences? List up to two distinct consequences. Be specific. Your output MUST be a valid JSON list of strings. Example: ["Avoided agricultural losses", "Reduced infrastructure damage"]""",
    "val_devise_pathway": """For the consequence '{consequence}', devise a research pathway to find a financial value. What specific, searchable financial data point should be looked for online? The data point must include a monetary value and a unit (e.g., '$/hectare', '$/person'). Your output MUST be a single JSON object with the key "pathway".""",
    "val_targeted_search": """Execute the following research plan: **{pathway}**. Search the internet for this specific data point. For each finding, provide the value, the unit, the source, and a confidence score from 0.0 to 1.0. The 'value' field in the JSON output must be a single, final number (no calculations or comments). Your output MUST be a valid JSON list of objects.""",
    
    "val_harmonize_units": """Given the impact quantity '{impact_quantity} {impact_unit}' and the monetary equivalent unit '{me_unit}', find or apply necessary conversion factors to align the units. The goal is to make the impact quantity directly multiplicable by the monetary equivalent. Your output MUST be a single JSON object with 'success' (boolean), 'converted_quantity' (float), and 'reasoning' (string) keys. If a reliable conversion cannot be found, set 'success' to false.""",
    "val_calculate_initial_value": """Calculate the initial dollar value for the impact '{impact_description}' by applying the most appropriate harmonized monetary equivalents provided. Choose the most reliable proxy (highest confidence) or provide a weighted average if multiple strong proxies exist. Clearly state which proxy was used. Your output MUST be a single JSON object with 'value' (float), 'base_proxy_source' (string), and 'confidence' (float) keys.""",
    "val_adjust_for_context": """Refine the initial dollar value of {initial_value} for the impact '{impact_description}' by applying relevant contextual adjustments. Consider geographical differences (e.g., purchasing power), the time horizon of the impact (e.g., discount rates for future benefits), and specific socio-economic factors relevant to the beneficiary group based on the provided company context. Provide clear notes for each adjustment. Your output MUST be a single JSON object with 'value' (float), 'notes' (string), and 'confidence' (float) keys.""",
    "val_prevent_overlap": """Carefully review all adjusted dollar values across the different impacts provided to identify and eliminate any potential overlaps or double-counted benefits. For instance, if 'cleaner water' leads to 'reduced healthcare costs', ensure these aren't valued as entirely separate, additive benefits. Provide a single, non-overlapping total dollar value and list the specific adjustments you made. Your output MUST be a single JSON object with 'total_value' (float) and 'overlap_adjustments' (list of strings) keys.""",
    "val_sensitivity_analysis": """Perform a sensitivity analysis on the consolidated total dollar value of {consolidated_value} by varying key underlying assumptions (e.g., the chosen monetary equivalent values, discount rates). Provide a credible range of possible total dollar values and highlight which assumptions have the greatest influence. Your output MUST be a single JSON object with 'base_value' (float), 'min_value' (float), 'max_value' (float), and 'key_sensitivities' (list of strings) keys.""",
    "val_generate_report": """Generate a comprehensive, expert-level written report section explaining the quantified societal and environmental impact. This narrative must clearly justify the methodology, the specific monetary equivalents chosen, all assumptions made, and explicitly state any limitations or uncertainties. The report should be clear, logical, and suitable for a client seeking in-depth analysis.""",
    "val_traceability_log": """Compile a meticulous and exhaustive audit trail of all data sources, specific monetary equivalents used, internal calculations, and any transformations applied throughout the entire impact quantification process. This log must be clear enough to allow independent verification and ensure full transparency. Format as a markdown list."""

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
    This endpoint uses the new clean_and_parse_json helper for robust AI responses.
    """
    initial_ai_outputs = request.get_json()
    if not initial_ai_outputs:
        return jsonify({"error": "Initial analysis data is required."}), 400
    
    print("VALUATION MANAGER: Starting LIVE valuation pipeline.")
    
    # === AGENT 1: IMPACT IDENTIFICATION ===
    print("--- Calling Agent 1: Impact Identification ---")
    impacts_prompt = PROMPTS["val_identify_impacts"] + "\n\nHere is the data to analyze:\n" + json.dumps(initial_ai_outputs)
    impacts_text = call_perplexity([{"role": "user", "content": impacts_prompt}])
    identified_impacts = clean_and_parse_json(impacts_text)
    print(identified_impacts)
    if not identified_impacts:
        return jsonify({"error": "Agent 1 (Impact Identification) failed to return valid JSON.", "raw_output": impacts_text}), 500

    all_impact_valuations = []

    # === MAIN LOOP: PROCESS EACH IMPACT ===
    for impact in identified_impacts:
        # --- Initial data validation for the impact object ---
        if not isinstance(impact, dict): continue
        description = impact.get('description')
        quantity = impact.get('quantity')
        unit = impact.get('unit')
        if not all([description, quantity is not None, unit]): continue
        print(f"\n[Manager] Processing impact: {description}")

        # === START OF VALUATION BRIDGE ===
        # 1. Consequence Identification Agent
        print(f"--- Calling Consequence Agent for '{description}' ---")
        consequences_prompt = format_prompt(PROMPTS["val_identify_consequences"], impact)
        consequences_text = call_perplexity([{"role": "user", "content": consequences_prompt}])
        consequences = clean_and_parse_json(consequences_text)
        
        if not consequences or not isinstance(consequences, list):
            print(f"[Manager] WARNING: No valid consequences found for '{description}'. Skipping impact.")
            continue
        
        print(consequences)
        successful_pathways = []
        # --- Loop through each consequence to find a value ---
        for consequence in consequences:
            print(f"  -- Pathway for consequence: '{consequence}' --")
            
            # 2. Valuation Pathway Agent
            pathway_prompt = format_prompt(PROMPTS["val_devise_pathway"], {"consequence": consequence})
            pathway_obj = clean_and_parse_json(call_perplexity([{"role": "user", "content": pathway_prompt}]))
            if not pathway_obj or not pathway_obj.get("pathway"):
                print(f"  [Manager] WARNING: Could not devise a pathway for '{consequence}'.")
                continue
            pathway = pathway_obj["pathway"]

            # 3. Targeted Data Search Agent
            print(f"  -- Executing targeted search: '{pathway}' --")
            search_prompt = format_prompt(PROMPTS["val_targeted_search"], {"pathway": pathway})
            monetary_equivalents_raw = clean_and_parse_json(call_perplexity([{"role": "user", "content": search_prompt}]))
            if not monetary_equivalents_raw or not isinstance(monetary_equivalents_raw, list):
                print(f"  [Manager] WARNING: Targeted search found no data for pathway '{pathway}'.")
                continue

            # 4. Unit Harmonization Agent
            harmonized_data = []
            for me in monetary_equivalents_raw:
                data_for_uh = {"impact_quantity": quantity, "impact_unit": unit, "me_unit": me.get('unit', '')}
                uh_prompt = format_prompt(PROMPTS["val_harmonize_units"], data_for_uh)
                harmonized_result = clean_and_parse_json(call_perplexity([{"role": "user", "content": uh_prompt}]))
                
                if harmonized_result and harmonized_result.get("success") and "converted_quantity" in harmonized_result:
                    harmonized_data.append({"impact_quantity_converted": harmonized_result["converted_quantity"], "monetary_equivalent_details": me})
            
            if not harmonized_data:
                print(f"  [Manager] WARNING: No suitable harmonized proxies found for this pathway.")
                continue

            # 5. Dollar Value Calculation Agent
            dvc_prompt = format_prompt(PROMPTS["val_calculate_initial_value"], {"impact_description": description})
            dvc_prompt += "\n\nHere is the harmonized data:\n" + json.dumps(harmonized_data)
            initial_dollar_value = clean_and_parse_json(call_perplexity([{"role": "user", "content": dvc_prompt}]))
            if not initial_dollar_value: continue

            # 6. Contextual Adjustment Agent
            data_for_ca = {"initial_value": initial_dollar_value.get('value'), "impact_description": description}
            ca_prompt = format_prompt(PROMPTS["val_adjust_for_context"], data_for_ca)
            ca_prompt += "\n\nCompany Context:\n" + json.dumps(initial_ai_outputs)
            adjusted_dollar_value = clean_and_parse_json(call_perplexity([{"role": "user", "content": ca_prompt}]))
            if not adjusted_dollar_value: continue

            # If a pathway is fully successful, add its result
            successful_pathways.append({
                "consequence": consequence,
                "pathway": pathway,
                "final_value": adjusted_dollar_value
            })
        print(successful_pathways)
        # --- After checking all consequences, process the successful ones ---
        if successful_pathways:
            # For simplicity, we'll take the first successful pathway's result as the value for the entire impact.
            # A more advanced implementation could average them or take the highest confidence one.
            best_pathway = successful_pathways[0]
            
            all_impact_valuations.append({
                "impact_details": impact,
                "successful_pathway": best_pathway,
                "adjusted_dollar_value": best_pathway['final_value']
            })

    if not all_impact_valuations:
        return jsonify({"error": "Could not successfully monetize any impacts."}), 500

    # === AGGREGATE AGENTS (After loop) ===
    op_prompt = PROMPTS["val_prevent_overlap"] + "\n\nHere are all the valued impacts:\n" + json.dumps(all_impact_valuations)
    consolidated_total_value = clean_and_parse_json(call_perplexity([{"role": "user", "content": op_prompt}]))
    if not consolidated_total_value: consolidated_total_value = {"total_value": 0, "overlap_adjustments": ["Error parsing agent output."]}
    
    sa_prompt = format_prompt(PROMPTS["val_sensitivity_analysis"], {"consolidated_value": consolidated_total_value.get('total_value', 0)})
    sa_prompt += "\n\nHere are all the valued impacts:\n" + json.dumps(all_impact_valuations)
    value_range_analysis = clean_and_parse_json(call_perplexity([{"role": "user", "content": sa_prompt}]))
    if not value_range_analysis: value_range_analysis = {"base_value": 0, "min_value": 0, "max_value": 0, "key_sensitivities": ["Error parsing agent output."]}

    # ... (Agent 8 & 9 and Final Assembly remain the same) ...
    report_data_for_ai = {"all_impact_valuations": all_impact_valuations, "consolidated_total_value": consolidated_total_value, "value_range_analysis": value_range_analysis}
    report_prompt = PROMPTS["val_generate_report"] + "\n\nUse this data to generate the report:\n" + json.dumps(report_data_for_ai)
    trace_prompt = PROMPTS["val_traceability_log"] + "\n\nUse this data to generate the log:\n" + json.dumps(report_data_for_ai)
    report_narrative = call_perplexity([{"role": "user", "content": report_prompt}])
    traceability_log = call_perplexity([{"role": "user", "content": trace_prompt}])

    final_valuation_result = {
        "consolidated_total_value": consolidated_total_value,
        "value_range_analysis": value_range_analysis,
        "report_narrative": report_narrative,
        "traceability_log": traceability_log,
        "all_impact_valuations": all_impact_valuations,
        "prompts": {
            "impact_identification": PROMPTS["val_identify_impacts"],
            "monetary_equivalent_search": PROMPTS["val_find_monetary_equivalents"],
            "sensitivity_analysis": PROMPTS["val_sensitivity_analysis"],
            "report_generation": PROMPTS["val_generate_report"]
        }
    }
    
    return jsonify(final_valuation_result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
    #socketio.run(app, debug=True, port=5001)