import os
import requests
import json
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import pint
import traceback
import re


ureg = pint.UnitRegistry()
ureg.define('USD = [currency]')
ureg.define('dollar = USD')

# --- Basic App Setup ---
app = Flask(__name__)
CORS(app)

# --- Perplexity AI Configuration ---
# Personal
#PERPLEXITY_API_KEY = "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"
# Impactable
#PERPLEXITY_API_KEY = "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"
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
    "generate_second_order": """You are an expert evaluator consolidating an impact analysis. Your task is to generate a final, structured markdown output that includes the metric, its counterfactuals, its first-order outcome, and its second-order outcomes.

### Output Format
For each metric analyzed, generate a block of text using the exact markdown structure below.
Use bold labels as shown. Separate each complete metric block with a double newline.

### Metric [Number]
**Description:** [The name of the metric]
**Units:** [The primary unit for the metric]

**Counterfactuals:**
- [Counterfactual 1 Name] [Unit]
- [Counterfactual 2 Name] [Unit]

**First-Order Outcome:**
- [First-Order Outcome Name] [Unit]

**Second-Order Outcomes:**
- [Second-Order Outcome 1 Name] [Unit]
- [Second-Order Outcome 2 Name] [Unit]
- [Second-Order Outcome 3 Name] [Unit]
""",
    "critique_second_order": "Now, critique and revise the Second Order Outcomes you just generated. Output only the corrected list in the original format.",
    
    # --- VALUATION AGENT PROMPTS ---
    "val_identify_impacts": """Analyze the provided data to extract ONE key societal or environmental impact. Provide a precise description of the impact and its standard unit of measurement. Your output MUST be a valid JSON object. Example: {{\"description\": \"Reduction in wildfire response time\", \"unit\": \"hours\"}}""",

    "val_research_counterfactuals": """
    For the primary metric '{metric_description}' (unit: {unit}), research its counterfactual scenarios.
    Metric: {metric_description}
    Counterfactual Scenarios to research:
    {counterfactual_list}

    For EACH scenario, your output MUST be a JSON object containing:
    - "scenario": The name of the scenario.
    - "value": A realistic numerical value in '{unit}'.
    - "probability": The likelihood of this scenario (decimal, sum of all must be 1.0).
    - "source_name": The name of the source publication or organization (e.g., "U.S. Forest Service Report").
    - "source_url": A direct URL to the source.
    - "source_quotation": The exact text from the source justifying the 'value'.
    - "reasoning": A brief explanation for why this source and probability are appropriate.

    Output a valid JSON list of these objects.
    """,

    "val_research_abstract_unit": """
    You are an economic analyst. The system needs to find a value for '{so_description}', but the primary unit, '{first_order_unit}', is an abstract, non-physical unit.

    Standard unit conversion is not possible. Your task is to perform two direct research queries:

    1.  **Direct Conversion Factor:** Find a credible value for the relationship expressed directly as '{so_unit}' per '{first_order_unit}'.
    2.  **Monetary Proxy:** Find a credible monetary value (in USD) for one '{so_unit}'.

    Your output MUST be a single JSON object with full sourcing.
    Example for "Tonnes of CO2 emissions avoided per incident":
    {{
      "conversion_factor": {{
        "value": 0.5,
        "source_name": "Report on GHG from Industrial Accidents, 2022",
        "source_url": "...",
        "source_quotation": "On average, a significant industrial incident releases approximately 0.5 tonnes of CO2 equivalent.",
        "reasoning": "This source directly links the abstract 'incident' to a physical quantity, which is required here."
      }},
      "monetary_proxy": {{
        "value": 51,
        "source_name": "US EPA - Social Cost of Carbon",
        "source_url": "...",
        "source_quotation": "The central estimate for the social cost of carbon... is $51 per metric ton.",
        "reasoning": "This is the standard proxy for monetizing carbon emissions."
      }}
    }}
    """,
    "val_research_and_monetize_so": """
    You are an economic analyst. For the second-order outcome '{so_description}', find a conversion factor and a monetary proxy.

    - First-Order Outcome Unit: '{first_order_unit}'
    - Second-Order Outcome Unit: '{so_unit}'

    Your output MUST be a single JSON object with two keys: "conversion_factor" and "monetary_proxy".
    Each key must contain an object with: "value", "source_name", "source_url", "source_quotation", and "reasoning".

    1.  **conversion_factor:** How many '{so_unit}' are impacted per '{first_order_unit}'?
    2.  **monetary_proxy:** What is the monetary value (in USD) per '{so_unit}'?

    Example JSON structure:
    {{
      "conversion_factor": {{
        "value": 3.0,
        "source_name": "IPCC Special Report on Climate Change and Land",
        "source_url": "https://www.ipcc.ch/srccl/",
        "source_quotation": "Average carbon emissions from temperate forest fires are estimated to be approximately 3.0 tonnes of C per hectare burned.",
        "reasoning": "The IPCC is the leading international body for climate change assessment, making its emission factors highly credible for this analysis."
      }},
      "impact_value_per_unit": {{
        "value": 51,
        "source_name": "US EPA - Report on the Social Cost of Greenhouse Gases",
        "source_url": "https://www.epa.gov/environmental-economics/social-cost-greenhouse-gases",
        "source_quotation": "The central estimate for the social cost of carbon (SC-CO2) for a 2020 emission year is $51 per metric ton...",
        "reasoning": "The EPA's Social Cost of Carbon is a widely accepted standard in the US for monetizing carbon emissions damage."
      }}
    }}""",
    "agent_determine_metric_polarity": """
        For the metric '{metric_description}', does a higher number represent a better, more desirable outcome? 
        Respond with the single word 'positive'. 
        If a lower number is better (e.g., CO2 emissions, response time), respond with the single word 'negative'.
        """,
    "agent_define_unit": """
    The following word was used as a unit of measurement but is not a known physical unit: '{unit_name}'.
    Is this word a simple, countable, dimensionless item (like 'people', 'cases', 'events', 'reports')?
    Respond with the single word 'countable' if yes. Otherwise, respond with 'unknown'.
    """,
    # --- AGGREGATION & REPORTING PROMPTS ---
    "val_sensitivity_analysis": """Perform a sensitivity analysis on the final valuation by varying the key underlying assumptions. The key assumptions are the values and probabilities in the counterfactual analysis and the monetary value per unit. Provide a credible range (min and max) for the final valuation and explain which assumption has the greatest influence. Your output MUST be a single JSON object with 'base_value', 'min_value', 'max_value', and 'key_sensitivities' (list of strings) keys.""",
    "val_generate_report": """Generate a comprehensive, expert-level written report section explaining the quantified societal and environmental impact. This narrative must clearly justify the methodology, the counterfactual scenarios chosen, the monetization proxy used, all assumptions made, and explicitly state any limitations or uncertainties. The report should be clear, logical, and suitable for a client seeking in-depth analysis.""",
    "val_traceability_log": """Compile a meticulous audit trail of all data sources, calculations, and transformations used in the valuation. Include the metric, counterfactuals (with values and probabilities), the calculated first-order outcome, and the monetization proxy (with its source). Format as a markdown list."""
}


# --- Core AI Function ---
def call_perplexity(messages, temperature=0.2, max_tokens=4096):
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

def clean_and_parse_json(ai_string):
    """
    A much more robust function to find, clean, and parse JSON from an AI's text response.
    """
    # 1. First, try to find a JSON markdown block. This is the most reliable method.
    match = re.search(r'```json\s*([\s\S]*?)\s*```', ai_string)
    if match:
        json_text = match.group(1)
    else:
        # 2. If no markdown, find the first '[' or '{' to start from.
        start_bracket = ai_string.find('[')
        start_curly = ai_string.find('{')
        
        if start_bracket == -1 and start_curly == -1:
            print("JSON PARSING FAILED: No JSON start character '[' or '{' found.")
            return None

        if start_bracket != -1 and (start_bracket < start_curly or start_curly == -1):
            json_text = ai_string[start_bracket:]
        else:
            json_text = ai_string[start_curly:]

    # 3. Clean up common AI-induced errors and attempt to parse.
    try:
        # --- THIS IS THE FIX ---
        # Remove commas and underscores used as thousands separators in numbers.
        # The regex (?<=\d) and (?=\d) are lookarounds that ensure we only remove
        # commas/underscores that are between two digits.
        json_text = re.sub(r'(?<=\d),(?=\d)', '', json_text)
        json_text = re.sub(r'(?<=\d)_(?=\d)', '', json_text)
        
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"JSON PARSING FAILED for string: {json_text}\nError: {e}")
        return None


def parse_all_metric_chains(analysis_data):
    """
    Parses the entire analysis data and returns a structured list of all metric chains.
    """
    # ... (The full function from the previous response goes here) ...
    # This function takes analysis_data and returns the `chains` list.
    metric_response = analysis_data['steps'][0]['response']
    counterfactual_response = analysis_data['steps'][1]['response']
    so_response = analysis_data['steps'][3]['response']
    metric_blocks = metric_response.strip().split('\n\n')
    counterfactual_blocks = counterfactual_response.strip().split('\n\n')
    so_blocks = so_response.strip().split('\n\n')
    chains = []
    for i, metric_block in enumerate(metric_blocks):
        try:
            metric_lines = metric_block.strip().split('\n')
            metric_desc = metric_lines[0].strip().replace('-', '').strip()
            unit = None
            for line in metric_lines:
                if 'units:' in line.lower():
                    unit = line.split(':')[1].split(',')[0].strip().lower()
                    break
            if not unit: continue
            cf_items = [line.replace('-', '').strip() for line in counterfactual_blocks[i].strip().split('\n')[1:]]
            so_items = []
            for line in so_blocks[i].strip().split('\n'):
                if line.strip().startswith('-'):
                    match = re.search(r'-\s*(.*?)\s*\[(.*?)]', line)
                    if match:
                        so_items.append({"description": match.group(1).strip(), "unit": match.group(2).strip().lower()})
            chains.append({
                "metric": {"description": metric_desc, "unit": unit},
                "counterfactuals": cf_items,
                "second_order_outcomes": so_items
            })
        except IndexError:
            print(f"WARNING: Mismatch in block counts at index {i}. Skipping this chain.")
            continue
    return chains


@app.route('/api/run_valuation', methods=['POST'])
def run_valuation():
    data = request.get_json()
    analysis_data = data.get('analysis_data')
    metric_value = float(data.get('metric_value'))

    if not all([analysis_data, metric_value]):
        return jsonify({"error": "A valid 'analysis_data' and 'metric_value' are required."}), 400

    try:
        all_metric_chains = parse_all_metric_chains(analysis_data)
        if not all_metric_chains:
            return jsonify({"error": "Failed to parse any valid metric chains from the input."}), 400
        
        print(f"MANAGER: Parsing successful. Found {len(all_metric_chains)} metric chains to process.")
        
        final_reports = []
        grand_total_valuation = 0 * ureg.USD

        # === MAIN LOOP: PROCESS EACH METRIC CHAIN ===
        for chain_index, metric_chain in enumerate(all_metric_chains):
            metric_info = metric_chain['metric']
            counterfactual_list = metric_chain['counterfactuals']
            so_list = metric_chain['second_order_outcomes']
            
            print(f"\n--- Processing Chain {chain_index + 1}/{len(all_metric_chains)}: '{metric_info['description']}' ---")

            # 1. Determine Metric Polarity
            polarity_prompt = format_prompt(PROMPTS["agent_determine_metric_polarity"], {"metric_description": metric_info['description']})
            polarity = call_perplexity([{"role": "user", "content": polarity_prompt}], temperature=0.1).lower()
            
            # 2. Research Counterfactuals
            cf_prompt = format_prompt(PROMPTS["val_research_counterfactuals"], {"metric_description": metric_info['description'], "unit": metric_info['unit'], "counterfactual_list": "\n".join(f"- {cf}" for cf in counterfactual_list)})
            researched_counterfactuals = clean_and_parse_json(call_perplexity([{"role": "user", "content": cf_prompt}]))
            if not researched_counterfactuals:
                print("WARNING: Failed to research counterfactuals. Skipping chain.")
                continue

            # 3. Calculate First-Order Outcome and Adjust for Polarity
            weighted_cf_value = sum(s.get('value', 0) * s.get('probability', 0) for s in researched_counterfactuals)
            first_order_value = metric_value - weighted_cf_value
            adjusted_first_order_value = first_order_value * -1 if 'negative' in polarity else first_order_value
            first_order_outcome = {"description": f"Net change in {metric_info['description']}", "value": adjusted_first_order_value, "unit": metric_info['unit']}
            print(f"MANAGER: First-Order Impact Value: {adjusted_first_order_value:.2f} {metric_info['unit']}")

            # 4. Process Second-Order Outcomes for this chain
            chain_total_valuation = 0 * ureg.USD
            
            # ---> monetized_chains is DEFINED HERE as an empty list for each metric chain.
            monetized_chains = []
            for so_outcome in so_list:
                print(f"  - Processing SO Chain: '{so_outcome['description']}'")
                try:
                    # TIER 1: Attempt calculation with pint
                    so_prompt = format_prompt(PROMPTS["val_research_and_monetize_so"], {"first_order_unit": first_order_outcome['unit'], "so_description": so_outcome['description'], "so_unit": so_outcome['unit']})
                    monetization_data = clean_and_parse_json(call_perplexity([{"role": "user", "content": so_prompt}]))
                    if not monetization_data: continue

                    # first_order_quantity = first_order_outcome['value'] * ureg(first_order_outcome['unit'])
                    # conv_factor = monetization_data['conversion_factor']['value'] * ureg(monetization_data['conversion_factor']['unit'])
                    # monetary_proxy = monetization_data['monetary_proxy']['value'] * ureg(monetization_data['monetary_proxy']['unit'])
                    # so_value = (first_order_quantity * conv_factor * monetary_proxy).to('USD')
                    
                except pint.errors.UndefinedUnitError:
                    # TIER 2: Unit is abstract, switch to direct research
                    print(f"    - WARNING: Unit '{first_order_outcome['unit']}' is abstract. Switching to direct research mode.")
                    so_prompt = format_prompt(PROMPTS["val_research_abstract_unit"], {"first_order_unit": first_order_outcome['unit'], "so_description": so_outcome['description'], "so_unit": so_outcome['unit']})
                    monetization_data = clean_and_parse_json(call_perplexity([{"role": "user", "content": so_prompt}]))
                
                if not monetization_data or 'conversion_factor' not in monetization_data or 'monetary_proxy' not in monetization_data or monetization_data['conversion_factor']['value'] == None or monetization_data['monetary_proxy']['value']== None:
                    print(f"    - ERROR: Direct research agent failed. Skipping SO chain.")
                    continue
                    
                if monetization_data:
                    # A. Normalize AI response (handles AI "inertia")
                    if 'monetary_proxy' in monetization_data and 'impact_value_per_unit' not in monetization_data:
                        monetization_data['impact_value_per_unit'] = monetization_data.pop('monetary_proxy')

                    # B. Verify that all required keys and sub-keys are present
                    cf_data = monetization_data.get('conversion_factor', {})
                    ipu_data = monetization_data.get('impact_value_per_unit', {})
                    
                    if cf_data.get('value') is not None and ipu_data.get('value') is not None:
                        # C. If all data is present, perform the calculation
                        try:
                            so_value_mag = first_order_outcome['value'] * cf_data['value'] * ipu_data['value']
                            so_value = so_value_mag * ureg.USD
                            print(f"    - SUCCESS: Value is {so_value:~P.2f}")
                        except Exception as calc_error:
                             print(f"    - ERROR: Calculation failed with an unexpected error: {calc_error}")
                    else:
                        print(f"    - ERROR: AI response was incomplete (missing a 'value' key).")
                else:
                    print(f"    - ERROR: AI research agent failed to return any valid data.")
                
                
                chain_total_valuation += so_value
                print(f"    - SUCCESS: Value is {so_value:~P.2f}")
                
                # ---> monetized_chains is POPULATED HERE with the results of a successful calculation.
                monetized_chains.append({
                    "description": so_outcome['description'],
                    "value": round(so_value.magnitude, 2),
                    "source_details": monetization_data
                })

            # 5. Finalize this chain's report
            print(f"--- Chain {chain_index + 1} Total Valuation: {chain_total_valuation:~P.2f} ---")
            grand_total_valuation += chain_total_valuation
            final_reports.append({
                "metric_chain": metric_info['description'],
                "chain_valuation_usd": round(chain_total_valuation.magnitude, 2),
                "first_order_outcome": first_order_outcome,
                "researched_counterfactuals": researched_counterfactuals,
                "second_order_details": monetized_chains 
            })
        
        print(f'final report {final_reports}')
        # --- FINAL AGGREGATION ---
        print(f"\n--- VALUATION COMPLETE ---")
        print(f"GRAND TOTAL VALUATION: {grand_total_valuation:~P.2f}")
        final_result_data = {
            "grand_total_valuation": {"value": round(grand_total_valuation.magnitude, 2), "currency": "USD"},
            "individual_chain_reports": final_reports
        }
        return jsonify(final_result_data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"A fatal error occurred: {str(e)}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True, port=5001)