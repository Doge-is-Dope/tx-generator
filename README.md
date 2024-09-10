### Set up

Create a `.env` file in the root directory of the project and add the following environment variables:

```bash
# For LangSmith tracing
LANGCHAIN_API_KEY=

# AI providers
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_APPLICATION_CREDENTIALS=Path_to_google_credentials.json

# Model provider: openai, anthropic, google
MODEL_PROVIDER=openai
```

### Data processing

All of the processed data is stored in the `data` folder.

- `data/raw`: Raw data from Bento Batch. i.e. source code.

### Intent processing

1. Intent conversion: Convert the raw intent into a list of steps.
2. Step conversion: Convert the list of steps into a list of transactions.
   2.1. Simulate each step to check if it's valid.
   2.2. Generate the corresponding transactions.
   2.3. Map the description to the generated transactions.
3. Return result: Return the list of steps and transactions.
