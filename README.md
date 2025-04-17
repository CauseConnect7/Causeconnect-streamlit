# 🤝 CauseConnect

**CauseConnect** is a research-based interactive platform that helps nonprofits and for-profit organizations find ideal partners based on mission alignment, resource complementarity, and strategic compatibility. It features an A/B tested recommendation engine powered by OpenAI’s LLMs and semantic embeddings.

> 🌐 **Live Demo**: [https://causeconnect-streamlit-web.onrender.com](https://causeconnect-streamlit-web.onrender.com)

---

## 🧭 Project Overview

CauseConnect was designed at the University of Washington to address a common pain point in the social impact ecosystem: **finding compatible and mission-aligned partners efficiently**. Traditional partnership formation is network-driven and subjective. This platform introduces AI-driven, data-informed matching to streamline that process.

### 🎯 Core Features

- 🔍 **A/B Testing of Algorithms**: Compare structured tag-based (complex) vs. raw description-based (simple) recommendation pipelines
- 💡 **LLM Reasoning & Embedding Matching**: Leverages OpenAI’s GPT and ADA models for semantic partner matching
- 🧪 **User Evaluation**: Participants rate matches and submit feedback to help improve the algorithm
- 💾 **MongoDB Storage**: Records user profiles, ratings, algorithm assignments, and survey responses
- 🧑‍🔬 **Cold-Start Compatible**: Works without relying on historical interaction data

---

## 📦 Tech Stack

| Layer        | Technology                        |
|--------------|-----------------------------------|
| Frontend     | [Streamlit](https://streamlit.io) |
| Backend      | [FastAPI](https://fastapi.tiangolo.com) |
| AI Models    | OpenAI GPT-4o / GPT-3.5 / ADA     |
| Embedding    | `text-embedding-ada-002`          |
| Database     | MongoDB (Cloud via Atlas)         |
| Deployment   | Render (Streamlit + FastAPI)      |

---

## 🧰 Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/causeconnect.git
cd causeconnect
```
### 2. Install Dependencies

We recommend using a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```
###3. Create a .env File
```bash
OPENAI_API_KEY=your_openai_key
MONGODB_URI=your_mongodb_uri
MONGODB_DB_NAME=Organization5
MONGODB_COLLECTION_NONPROFIT=Nonprofit
MONGODB_COLLECTION_FORPROFIT=Forprofit

PROMPT_GEN_ORG_SYSTEM=...
PROMPT_GEN_ORG_USER=...
PROMPT_TAGS_SYSTEM=...
PROMPT_TAGS_USER=...
MATCH_EVALUATION_SYSTEM_PROMPT=...
MATCH_EVALUATION_PROMPT=...
```
###4.Run the Backend
```bash
uvicorn backend.main:app --reload --port 10000
```
###5. Run the Frontend
```bash
streamlit run frontend/app.py
```
## 🔬 Algorithm Logic

### Complex (Tag-Based Matching)

- GPT generates an ideal organization profile  
- GPT decomposes it into 30 tags across 6 dimensions  
- Tags are embedded using OpenAI embeddings  
- Candidates from the database are filtered, scored, and GPT-evaluated  
- Top 20 matches are selected with status (`accepted` / `supplementary`)

### Simple (Description-Based Matching)

- Embedding is generated directly from user’s partnership description  
- Top 20 matches are selected purely by cosine similarity  
- No tags, no evaluation reasoning

---

## 📊 Output Format

Both APIs return JSON with the following structure:

```json
{
  "status": "success",
  "matching_results": [
    {
      "similarity_score": 0.91,
      "evaluation_status": "accepted",
      "organization": {
        "name": "Example Org",
        "mission": "...",
        ...
      }
    },
    ...
  ]
}
```
## 📁 Folder Structure
```bash
. ├── backend/ # FastAPI backend
│ └── main.py ├── frontend/ # Streamlit frontend
│ └── app.py ├── .env # Environment variables
├── requirements.txt # Python dependencies
└── README.md

```
---

## 🧪 Research Context

This project was developed at the **University of Washington Information School** as part of a study on improving partnership formation using AI tools.

If you are a study participant, please refer to the instructions on the [Live Demo](https://causeconnect-streamlit-web.onrender.com) site.

---

## 📬 Contact

- 📧 Email: causeconnect7@gmail.com  
- 📚 Affiliation: University of Washington iSchool  
- 🧠 Lead: Shunxi Wu

---

## 📝 License

This project is intended for **academic research and non-commercial use only**.

If you'd like to collaborate, extend, or reuse this system for your own organization, please reach out for permission or partnership opportunities.


