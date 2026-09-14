# AgenticBI
An event-driven, containerized AI Data Analyst built with Python, Docker, and AWS. Automatically extracts anomaly insights from S3 streams via Bedrock.

markdown# 🛡️ AgenticBI

> **An Autonomous, Event-Driven AI Data Analyst for Serverless Anomaly Detection.**

AgenticBI transitions enterprise data operations from traditional reactive dashboard monitoring to proactive, event-driven AI orchestration. Built entirely on a containerized serverless stack, it monitors incoming raw data streams unattended, uses an AI Agent to dynamically extract metrics, handles unsupervised anomaly detection, and compiles actionable intervention strategies instantly.

---

## 🏗️ Architecture Blueprint

```text
                                    AWS CLOUD (us-east-1)
 ┌─────────────────┐       ┌──────────────────────────────────────┐       ┌────────────────┐
 │                 │       │           AWS LAMBDA SERVICE         │       │                │
 │                 │──────>│ ┌──────────────────────────────────┐ │──────>│ Amazon Bedrock │
 │                 │ S3    │ │      OCI DOCKER CONTAINER        │ │Stream │  (Nova Lite)   │
 │                 │ Event │ │ ┌──────────────┐┌──────────────┐ │ │       └────────────────┘
 │  Amazon S3      │       │ │ │  Data Engine ││ AI Framework │ │ │               │
 │  Data Bucket    │       │ │ │ (Pandas,NumPy││   (Strands   │ │ │               │ Context &
 │                 │       │ │ │ Matplotlib)  ││  Agents SDK) │ │ │<──────────────┘ Strategies
 │ ┌─────────────┐ │       │ │ └──────────────┘└──────────────┘ │ │
 │ │  /input     │ │       │ │           │           ▲          │ │
 │ └─────────────┐ │       │ │           ▼           │          │ │       ┌────────────────┐
 │                 │<──────│ │   Generates Telemetry & Reports  │ │       │ Local Engine / │
 │ ┌─────────────┐ │ Writes│ └──────────────────────────────────┘ │       │ Developer PC   │
 │ │  /output    │ │Outputs│                                      │       ├────────────────┤
 │ └─────────────┘ │       └──────────────────────────────────────┘       │  Streamlit UI  │
 └─────────────────┘                                                      │   Dashboard    │
          │                                                               └────────────────┘
          └───────────────────── Pulls Manifest (Boto3 API) ──────────────────────┘
```

### 💡 Core Architectural Decision: Docker Containers vs. Lambda Layers
Standard AWS Lambda layers enforce a strict **250 MB unzipped storage limit**. Heavy data science frameworks and visualization engines expand past this threshold instantly:
* `NumPy`: ~90MB+ unzipped
* `Matplotlib`: ~80MB+ unzipped
* `Pandas`: ~100MB+ unzipped
* `Strands Agents SDK`: ~40MB+ unzipped

**Our Solution:** We decoupled our stack from traditional zip layers and packaged our microservice as an **OCI-compliant Docker Container Image** deployed via Amazon ECR. This bypassed the 250 MB ceiling, replacing it with a massive **10 GB container limit**—granting our AI Agent full database processing, model orchestration, and graphical capability.

---

## 🛠️ Stack & Technologies
* **Runtime Environment:** Python 3.12 (AWS Lambda Base Image)
* **AI Orchestration Framework:** Strands Agents SDK
* **Foundation LLM:** Amazon Bedrock (`amazon.nova-lite-v1:0`) via ConverseStream
* **Data Processing & Graphics:** Pandas, NumPy, Matplotlib
* **Cloud Storage & Events:** Amazon S3 (`ObjectCreated` Notification Triggers with folder prefix rules)
* **User Presentation Interface:** Streamlit (Dynamic cross-column data visualization platform)

---

## 🚀 Getting Started

### 1. Repository Structure
```text
AgenticBI/
├── Dockerfile              # Container building blueprint
├── lambda_function.py      # Main application core & AI Agent loop
├── app.py                  # Streamlit dashboard interface 
├── .gitignore              # Excludes environment clutter from commits
└── requirements.txt        # Managed software package library dependencies
```

### 2. Manual Deployment via AWS CLI / CloudShell
Ensure you are inside the project folder containing the files:
```bash
# 1. Compile and build the container assets locally
docker build -t lambda-matplotlib:latest .

# 2. Authenticate the local Docker engine to your remote Amazon ECR Repository
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin \${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# 3. Tag and push the asset image package
docker tag lambda-matplotlib:latest \${ACCOUNT_ID}://
docker push \${ACCOUNT_ID}://
```

### 3. Launching the Management Control Dashboard
To view live outputs parsed by the agent from S3, boot up the local Streamlit layout console:
```bash
export AWS_PROFILE=office
pip install -r requirements.txt
streamlit run app.py
```

---

## 📊 Sample Pipeline Output Telemetry

When an arbitrary dataset lands in `input/sales_data.csv`, the pipeline automatically fires and yields synchronized dual outputs: a visual anomaly tracking graph and a structured JSON executive action summary:

```json
{
  "total_rows": 15,
  "anomalies_found": 1,
  "target_numerical_column": "sales",
  "target_date_column": "date",
  "recommendation_steps": [
    "1. Investigate the 1 data point spikes flagged on the generated chart.",
    "2. Audit backend platform telemetry specifically at timestamps matching anomalies in column 'date'.",
    "3. Cross-reference network load or transaction queues with these isolated data timestamps."
  ]
}
```
