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
