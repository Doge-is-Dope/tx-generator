### Set up

Create a `.env` file in the root directory of the project and add the following environment variables:

```plaintext
LANGCHAIN_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GITHUB_ACCESS_TOKEN=
GOOGLE_APPLICATION_CREDENTIALS=PATH_TO_GOOGLE_APPLICATION_CREDENTIALS
```

Choose your preferred provider from the following options: `openai`, `anthropic`, or `google`.

```plaintext
MODEL_PROVIDER=
```

### Data

- data: Data used for retrieving/training
- raw_data: Raw data from Bento Batch. i.e. source code.
