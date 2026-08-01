chatbot

Receive Question
        │
        ▼
Generate Prompt
        │
        ▼
Call LLM
        │
        ▼
Receive SQL
        │
        ▼
Validate SQL
        │
        ▼
Execute SQL
        │
        ▼
Generate Final Answer
        │
        ▼
Return Response


                          User Question
                                │
                                ▼
                    Determine Retrieval Scope
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
  System Manuals         User Documents         PostgreSQL (SQL)
        │                       │                        │
        └───────────────┬───────┴───────────────┬────────┘
                        ▼
              Retrieved Context + SQL Results
                        │
                        ▼
                 Conversation Memory
                        │
                        ▼
                      Gemini
                        │
                        ▼
                    Final Answer




                User Question
                      │
                      ▼
               Chat/RAG Endpoint
                      │
                      ▼
                 RAGService
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
     Retriever             Prompt Builder
          │                       │
          └───────────┬───────────┘
                      ▼
                    Gemini
                      │
                      ▼
              Final Answer

              