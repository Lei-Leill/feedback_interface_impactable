'''
Bubble_helper file is adapted from impactablex/src/external/bubble.ts
I adapted it into python so it can be incorporated into the app.py for bubble data integration into the prompt
Date: 09/23/2025
'''

import os
from dotenv import load_dotenv
import requests
import json
from loguru import logger

load_dotenv() # load environment variables from .env file
# --- Configuration ---
BUBBLE_API_TOKEN = os.getenv("BUBBLE_API_TOKEN")
BUBBLE_API_URL = "https://app.impactablex.com/version-live/api/1.1/obj"

# --- Helper Functions ---
def _fetch_bubble_data(endpoint: str) -> list:
    """Generic function to fetch data from a Bubble API endpoint."""
    try:
        headers = {"Authorization": f"Bearer {BUBBLE_API_TOKEN}"}
        response = requests.get(f"{BUBBLE_API_URL}/{endpoint}", headers=headers)
        response.raise_for_status()
        return response.json().get("response", {}).get("results", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from {endpoint}: {e}")
        return []

def _find_by_id(data: list, id_to_find: str) -> dict | None:
    """Finds an item in a list of dictionaries by its _id."""
    if not id_to_find:
        return None
    for item in data:
        if item.get("_id") == id_to_find:
            return item
    return None

# --- Main Functions ---
def get_bubble_measurement_units():
    return _fetch_bubble_data("systemvalueunit")

def get_bubble_system_metrics():
    return _fetch_bubble_data("systemmetric")

def get_bubble_system_counterfactuals():
    return _fetch_bubble_data("systemcounterfactual")

def get_bubble_system_outcomes(order_number: int):
    results = _fetch_bubble_data("systemoutcome")
    return [item for item in results if item.get("OrderNo") == order_number]

def get_bubble_system_costs():
    return _fetch_bubble_data("systemcost")

def get_bubble_system_examples() -> dict:
    """
    Fetches and processes all system examples from the Bubble API, structuring them
    into a comprehensive dictionary for AI prompting.
    """
    try:
        # Fetch all raw data
        measurement_units = get_bubble_measurement_units()
        system_metrics = get_bubble_system_metrics()
        system_counterfactuals = get_bubble_system_counterfactuals()
        system_outcomes_all = _fetch_bubble_data("systemoutcome")
        system_costs = get_bubble_system_costs()

        # Helper lookups
        get_unit_by_id = lambda uid: _find_by_id(measurement_units, uid)
        get_metric_by_id = lambda mid: _find_by_id(system_metrics, mid)
        get_counterfactual_by_id = lambda cid: _find_by_id(system_counterfactuals, cid)
        get_outcome_by_id = lambda oid: _find_by_id(system_outcomes_all, oid)
        get_cost_by_id = lambda cid: _find_by_id(system_costs, cid)

        # Process Metrics
        system_metrics_result = [
            {
                "name": m.get("Name"),
                "unit": get_unit_by_id(m.get("ValueUnit"))["Name"] if get_unit_by_id(m.get("ValueUnit")) else None,
                "subcategories": m.get("Subcategories", []),
                "counterfactuals": [
                    {
                        "name": cf.get("Name"),
                        "description": cf.get("Description"),
                        "unit": get_unit_by_id(cf.get("ValueUnit"))["Name"] if get_unit_by_id(cf.get("ValueUnit")) else None,
                    } for cf in (get_counterfactual_by_id(cid) for cid in m.get("SystemCounterfactuals", [])) if cf
                ]
            } for m in system_metrics
        ]

        # Process Second Order Outcomes (the most comprehensive chain)
        system_second_order_outcomes_result = [
            {
                "name": o.get("Name"),
                "unit": get_unit_by_id(o.get("ValueUnit"))["Name"] if get_unit_by_id(o.get("ValueUnit")) else None,
                "metrics": [
                    {
                        "name": m.get("Name"),
                        "unit": get_unit_by_id(m.get("ValueUnit"))["Name"] if get_unit_by_id(m.get("ValueUnit")) else None,
                        "subcategories": m.get("Subcategories", []),
                    } for m in (get_metric_by_id(mid) for mid in o.get("SystemMetrics", [])) if m
                ],
                "counterfactual": (
                    lambda fo: {
                        "name": get_counterfactual_by_id(fo.get("SystemCounterfactual", "")).get("Name"),
                        "description": get_counterfactual_by_id(fo.get("SystemCounterfactual", "")).get("Description"),
                        "unit": get_unit_by_id(get_counterfactual_by_id(fo.get("SystemCounterfactual", "")).get("ValueUnit"))["Name"] if get_unit_by_id(get_counterfactual_by_id(fo.get("SystemCounterfactual", ""))) else None
                    } if fo and fo.get("SystemCounterfactual") and get_counterfactual_by_id(fo.get("SystemCounterfactual", "")) else None
                )(get_outcome_by_id(o.get("ParentOutcome", ""))),
                "first_order_outcome": (
                    lambda fo: {
                        "name": fo.get("Name"),
                        "unit": get_unit_by_id(fo.get("ValueUnit"))["Name"] if get_unit_by_id(fo.get("ValueUnit")) else None,
                    } if fo else None
                )(get_outcome_by_id(o.get("ParentOutcome", ""))),
                "costs": [
                    {
                        "name": c.get("Description"),
                        "unit": get_unit_by_id(c.get("ValueUnit"))["Name"] if get_unit_by_id(c.get("ValueUnit")) else None,
                    } for c in (get_cost_by_id(cid) for cid in o.get("Costs", [])) if c and c.get("Description")
                ],
            } for o in system_outcomes_all if o.get("OrderNo") == 2 and o.get("ParentOutcome")
        ]

        # Filter for complete chains
        metrics_chain = [item for item in system_second_order_outcomes_result if item.get("metrics") and item.get("counterfactual") and item.get("first_order_outcome") and item.get("costs")]
        cf_fo_so_cost_chain = [item for item in system_second_order_outcomes_result if item.get("counterfactual") and item.get("first_order_outcome") and item.get("costs")]
        cf_fo_so_chain = [item for item in system_second_order_outcomes_result if item.get("counterfactual") and item.get("first_order_outcome")]

        # Use a simple map to handle deduping and formatting
        def get_formatted_examples(data_list):
            return [
                {
                    "metric": item["metrics"][0] if item.get("metrics") else None,
                    "counterfactual": item["counterfactual"],
                    "first_order_outcome": item["first_order_outcome"],
                    "second_order_outcome": {"name": item.get("name"), "unit": item.get("unit")},
                    "cost": item["costs"][0] if item.get("costs") else None,
                } for item in data_list
            ]
        
        return {
            "metrics": system_metrics_result,
            "metrics_chain": get_formatted_examples(metrics_chain),
            "cf_fo_so_cost_chain": get_formatted_examples(cf_fo_so_cost_chain),
            "cf_fo_so_chain": get_formatted_examples(cf_fo_so_chain)
        }
    except Exception as e:
        logger.error(f"Failed to process Bubble examples: {e}")
        return {}

def format_correct_examples_context(bubble_examples: dict) -> str:
    """Formats the fetched examples into a string for the AI prompt."""
    context_parts = []
    counter = 1

    # Format Metrics
    if bubble_examples.get("metrics"):
        context_parts.append("\n======== METRICS ========")
        for item in bubble_examples["metrics"]:
            context_parts.append(
                f"----- Example {counter} -----\n"
                "--------\n"
                f"METRIC\nName: {item.get('name')}\n"
                f"Unit: {item.get('unit')}\n"
                f"Category: {', '.join(item.get('subcategories', []))}\n"
                "--------"
            )
            counter += 1

    # Format full chain examples
    if bubble_examples.get("metrics_chain"):
        context_parts.append("\n======== METRICS -> COUNTERFACTUALS -> FIRST ORDER OUTCOMES -> SECOND ORDER OUTCOMES -> COSTS ========")
        for item in bubble_examples["metrics_chain"]:
            metric = item.get("metric", {})
            counterfactual = item.get("counterfactual", {})
            first_order = item.get("first_order_outcome", {})
            second_order = item.get("second_order_outcome", {})
            cost = item.get("cost", {})
            context_parts.append(
                f"----- Example {counter} -----\n"
                "--------\n"
                f"METRIC\nName: {metric.get('name')}\nUnit: {metric.get('unit')}\n"
                "--------\n"
                f"COUNTERFACTUAL\nName: {counterfactual.get('name')}\nUnit: {counterfactual.get('unit')}\n"
                "--------\n"
                f"FIRST ORDER OUTCOME\nName: {first_order.get('name')}\nUnit: {first_order.get('unit')}\n"
                "--------\n"
                f"SECOND ORDER OUTCOME\nName: {second_order.get('name')}\nUnit: {second_order.get('unit')}\n"
                "--------\n"
                f"COST\nName: {cost.get('name')}\nUnit: {cost.get('unit')}\n"
                "--------"
            )
            counter += 1
            
    # Add other formatted chains here as needed...
    
    return "\n".join(context_parts)
    
def get_wrong_examples_context() -> str:
    # This remains the same as it's static content
    return """
    ++++++++++++++++++++++++    
    
        ======== METRICS -> COUNTERFACTUALS -> FIRST ORDER OUTCOMES -> SECOND ORDER OUTCOMES ========
        ----- Wrong Example 1 -----
        --------
        METRIC
        Name: Tonnes of MIRUM® Sold
        Unit: Tonnes
        Description: Quantifies the amount of MIRUM® material sold in tonnes.
        --------
        --------
        COUNTERFACTUAL
        Name: Tonnes of Synthetic (Plastic-based) Leather Used
        Unit: Tonnes
        Description: Highlights continued preference for synthetic leather options without the availability of MIRUM®.
        --------
        --------
        FIRST ORDER OUTCOME
        Name: Reduction in Synthetic Leather Consumption
        Unit: Tonnes
        --------
        --------
        SECOND ORDER OUTCOME
        Name: Lowered Petroleum Extraction
        Unit: Barrels
        --------
        
        EXPLANATION:
        The second order outcome "Lowered Petroleum Extraction" is not a consequence of the first order outcome "Reduction in Synthetic Leather Consumption". Correct is "Lower petroleum usage for synthetic leather production".
        ---------------------------

        ----- Wrong Example 2 -----
        --------
        METRIC
        Name: Number of Products Manufactured with MIRUM®
        Unit: Items
        Description: Tracks the quantity of items produced using MIRUM® material.
        --------
        --------
        COUNTERFACTUAL
        Name: Number of Products Manufactured with Traditional Leather
        Unit: Items
        Description: Suggests that manufacturers would revert to using traditional leather in the absence of MIRUM®.
        --------
        
        EXPLANATION:
        We will not be able to find data on the internet for "Number of Products Manufactured with Traditional Leather" because the number of products is not usually tracked in statistics. Thus, the counterfactual is not valid, and moreover, the metric that led to this counterfactual was invalid from the start.
        ---------------------------
        
        ----- Wrong Example 3 -----
        --------
        METRIC
        Name: Number of Products Manufactured with MIRUM®
        Unit: Items
        Description: Tracks the quantity of items produced using MIRUM® material.
        --------
        
        EXPLANATION:
        MIRUM® is a material, not a product. Company does not produce products (which is measured in "Items"). The metric is invalid from the start. 
        CORRECT: Square Meters of MIRUM® Produced
        ---------------------------

        ----- Wrong Example 4 -----
        --------
        METRIC
        Name: Liters of Water Saved by Using Biodesigned Ingredients Instead of Traditional Palm Oil Production
        Unit: Liters
        Description: This metric measures the amount of water conserved by utilizing biodesigned ingredients over traditional palm oil production methods.
        --------
        
        EXPLANATION:
        It is an outcome, not a metric. Metrics must answer questions like: "What does a company produce?" or "What does a company sell?" This example refers to a company's operational process, which is incorrect. Therefore, the metric is invalid from the start.
        
        ---------------------------
        
        ++++++++++++++++++++++++
    """

if __name__ == '__main__':
    # This block can be used for testing the functions directly
    examples = get_bubble_system_examples()
    formatted_context = format_correct_examples_context(examples)
    print(formatted_context)