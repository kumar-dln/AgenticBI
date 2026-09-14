import os
import io
import json
import urllib.parse
import boto3
import pandas as pd

# Headless rendering fix for serverless environments (Prevents Tkinter crashes)
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

from strands import Agent, tool
from strands.models import BedrockModel

# Initialize clients globally outside the handler for rapid container reuse
model = BedrockModel(model_id="amazon.nova-lite-v1:0")
s3 = boto3.client('s3')

# ─── STRANDS AGENT TOOLS ──────────────────────────────────────────────────

@tool
def download_and_inspect_csv(bucket: str, key: str) -> str:
    """Downloads a CSV from S3, reads the first 5 rows to understand schema and context."""
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        # Streams the object file directly over the network into a Pandas RAM memory buffer
        df = pd.read_csv(io.BytesIO(obj['Body'].read()), nrows=5)
        return f"Columns detected: {list(df.columns)}. Sample data structure: {df.to_json(orient='records')}"
    except Exception as e:
        return f"Error downloading/reading file from S3: {str(e)}"

@tool
def execute_anomaly_detection_and_save(bucket: str, key: str, numerical_column: str, date_column: str) -> str:
    """
    Runs a Z-score anomaly check, builds a visual matplotlib chart, and saves 
    both the chart and a recommendation JSON summary back to the S3 'output/' directory.
    """
    try:
        # Fetch the complete CSV file over the network stream into Lambda memory
        obj = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(io.BytesIO(obj['Body'].read()))
        
        # Calculate statistical anomalies
        mean = df[numerical_column].mean()
        std = df[numerical_column].std()
        df['is_anomaly'] = (abs(df[numerical_column] - mean) / (std if std != 0 else 1)) > 2.0
        anomalies_count = int(df['is_anomaly'].sum())
        
        # Draw the graph safely inside the headless background memory thread
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df[date_column], df[numerical_column], label="Metric Value Data", color='blue')
        
        anomalies = df[df['is_anomaly'] == True]
        ax.scatter(anomalies[date_column], anomalies[numerical_column], color='red', label="Flagged Anomalies")
        ax.set_title(f"Automated Anomaly Detection Visual - Column: ({numerical_column})")
        ax.legend()
        
        # Strict Path Isolation: Strip input/ folder prefix to target output/ safely
        pure_filename = os.path.basename(key)
        base_name = pure_filename.replace(".csv", "")
        
        out_key_img = f"output/{base_name}.png"
        out_key_json = f"output/{base_name}.json"
        
        # Save matplotlib output straight to an in-memory byte buffer, then stream upload to S3
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        s3.put_object(Bucket=bucket, Key=out_key_img, Body=img_buffer, ContentType="image/png")
        plt.close(fig) # Liberate system memory allocation
        
        # Generate the structured analysis report text metadata
        report = {
            "total_rows": len(df),
            "anomalies_found": anomalies_count,
            "target_numerical_column": numerical_column,
            "target_date_column": date_column,
            "recommendation_steps": [
                f"1. Investigate the {anomalies_count} data point spikes flagged on the generated chart.",
                f"2. Audit backend platform telemetry specifically at timestamps matching anomalies in column '{date_column}'.",
                "3. Cross-reference network load or transaction queues with these isolated data timestamps."
            ]
        }
        
        # Upload the JSON report string deliverable straight back to the output path
        s3.put_object(Bucket=bucket, Key=out_key_json, Body=json.dumps(report, indent=2), ContentType="application/json")
        
        return f"Success! Created visuals and insights deliverables: s3://{bucket}/{out_key_img} and s3://{bucket}/{out_key_json}"
    except Exception as e:
        return f"Error executing internal anomaly engine tool: {str(e)}"


# ─── AWS LAMBDA MAIN EVENT ENTRY POINT ────────────────────────────────────

def lambda_handler(event, context):
    print("🎬 S3 Object Created Event received by Lambda function container.", flush=True)
    
    # 1. Automatically dissect bucket and object string variables from incoming S3 trigger JSON
    bucket = event['Records'][0]['s3']['bucket']['name']
    raw_key = event['Records'][0]['s3']['object']['key']
    key = urllib.parse.unquote_plus(raw_key) # Decodes spaces or special character patterns
    
    print(f"🎯 Target File Detected: s3://{bucket}/{key}", flush=True)
    
    # 2. Critical Safety Verification Guardrail
    # Only processes files uploaded explicitly inside the 'input/' folder path.
    # This keeps output generation logs clean and explicitly prevents infinite execution billing loops.
    if not key.startswith("input/"):
        print(f"⚠️ Skipping execution. File '{key}' does not reside in the 'input/' directory folder.", flush=True)
        return {"status": "skipped", "reason": "Target file out of input/ boundary prefix paths."}
        
    # 3. Formulate the overarching instruction context prompt for your Strands Agent orchestrator
    system_prompt = f"""
    You are an expert domain-agnostic data validation agent.
    Tasks:
    1. Inspect the incoming CSV layout map using download_and_inspect_csv tool.
    2. Assess columns to target a dynamic, active numerical indicator and a corresponding temporal axis (date/time string).
    3. Run the execute_anomaly_detection_and_save tool to save charts and reports directly into the output folders.
    """
    
    # 4. Initialize the Strands core agent architecture map 
    agent = Agent(
        model=model,
        tools=[download_and_inspect_csv, execute_anomaly_detection_and_save],
        system_prompt=system_prompt
    )
    
    # 5. Execute agent workflow strategy instructions
    prompt = f"Inspect file s3://{bucket}/{key}. Identify layout context, parse anomalies, and route outputs cleanly."
    print("🧠 Invoking Strands Agent token stream pipeline processing loop...", flush=True)
    
    # Executing using direct functional object invocation (Strands framework standard override)
    agent_reasoning_log = agent(prompt)
    
    print("🏁 Serverless automated pipeline execution cycle finished successfully.", flush=True)
    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "success",
            "processed_file": f"s3://{bucket}/{key}",
            "agent_trace": str(agent_reasoning_log)  # Forced to string to prevent nested object issues
        })
    }
