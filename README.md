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

### Intent processing

1. Receive User Intent

   - Input: Natural language prompt (e.g., "Stake 0.03 ETH with Lido and deposit to Eigenpie.")
   - Task: Translate the user’s intent into concrete steps.
   - Output: List of steps (e.g., "Stake 0.03 ETH to Lido", "Approve stETH to Eigenpie", "Stake stETH to Eigenpie")

2. Simulate Transactions (Per Step)

   - Input: Each step from the previous phase (e.g., "Stake 0.03 ETH to Lido")
   - Task: For each step, convert it into appropriate transaction parameters and simulate the transaction to ensure feasibility.
   - Output: Simulated results, including whether the step succeeded or failed, and any necessary adjustments.

3. Refine and Update Steps

   - Input: Results from simulation
   - Task: Refine each step as needed based on the simulation results.
     - If the simulation fails (e.g., invalid parameters), adjust the parameters.
     - If the step passes simulation, mark it as successful.
   - Output: Updated steps, ready to be presented to the user.

4. Return Results to User

   - Input: Finalized steps.
   - Task: Return the list of steps and their associated transaction parameters to the user.
   - Output: A object containing the steps and their associated transaction details.

### Example

```json
{
  "description": "Stake 0.03 ETH with Lido and deposit to Eigenpie",
  "steps": [
    {
      "description": "Stake 0.03 ETH to Lido",
      "tx_params": {
        "to": "0x0",
        "value": "0x0",
        "data": "0x0"
      }
    },
    {
      "description": "Approve stETH to Eigenpie",
      "tx_params": {
        "to": "0x0",
        "value": "0x0",
        "data": "0x0"
      }
    },
    {
      "description": "Stake stETH to Eigenpie",
      "tx_params": {
        "to": "0x0",
        "value": "0x0",
        "data": "0x0"
      }
    }
  ]
}
```

### Data processing

All of the processed data is stored in the `data` folder.

- `data/raw`: Raw data from Bento Batch. i.e. source code.

### Implemented tools

- `abi/fetch_contract_abi`: Fetch the ABI of a contract
- `address/convert_to_checksum_address`: Convert an address to a checksum address
- `address/resolve_ens`: Resolve an ENS name to an address
- `address/get_contract_address_by_name`: Get the contract address by name
