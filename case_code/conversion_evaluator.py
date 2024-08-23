import sys
import os
import json
from typing import Optional


from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from utils.model_selector import get_chat_model
from case_code import CASE_CONVERTED_PATH


model_provider = get_chat_model()
model_name = model_provider.name
case_data_path = CASE_CONVERTED_PATH.format(model=model_name)


def read_transformed_cases() -> Optional[iter]:
    """
    Lazily load transformed cases as a generator.
    """
    if not os.path.exists(case_data_path):
        print(f"File not found: {case_data_path}")
        return None

    try:
        with open(case_data_path, "r") as f:
            for line in f:
                yield json.loads(line)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


case_examples = """
input: Stake 0.03 ETH with Lido and deposit to Eigenpie
output: 
 - id: stake_eth_lido_eigenpie
 - description: Stake 0.03 ETH with Lido and deposit to Eigenpie
 - total_steps: 3
 - steps: 
   - description: Stake 0.03 ETH to Lido.
   - description: Approve stETH to Eigenpie.
   - description: Stake stETH to Eigenpie.

input: Swap 100 USDT for USDC on Uniswap
output:
 - id: swap_usdt_to_usdc
 - description: Swap 100 USDT for USDC on Uniswap
 - total_steps: 2
 - steps:
   - description: Approve 100 USDT for Uniswap.
   - description: Swap 100 USDT for USDC on Uniswap.
"""

description_examples = """
- Swap 100 USDT for USDC on Uniswap
- Send 20 DAI to A
- Approve 100 USDT for Uniswap
- Stake 0.03 ETH to Lido
- Approve stETH to Eigenpie
- Stake stETH to Eigenpie
"""


def evaluate_case(case: dict) -> dict:
    """
    Evaluate a case by:
    - Checking if the number of steps is correct
    - Checking if the description of the steps are valid
    """
    # Initialize the evaluation result
    evaluation_result = {
        "id": case["id"],
        "mismatch_steps": False,
    }

    # Check if the number of steps is correct
    expected_steps = case["total_steps"]
    actual_steps = len(case["steps"])
    if expected_steps != actual_steps:
        evaluation_result["mismatch_steps"] = True

    # Check if the description of the steps are valid

    return evaluation_result


class DescriptionEvalResult(BaseModel):
    """Description evaluation result"""

    score: int = Field(
        description="The score indicating the quality of the description for converting into an Ethereum transaction"
    )
    reason: str = Field(
        description="Explanation for the given score, detailing the assessment criteria and any shortcomings."
    )
    action: str = Field(
        description="The type of Ethereum transaction inferred from the description, such as swap, approve, stake, etc."
    )


def eval_recipient(recipient: str) -> bool:
    """
    Evaluate if the recipient is a valid Ethereum address.
    """
    return True


def grade_description(desc: str) -> DescriptionEvalResult:
    """
    Score the description of a step.
    """

    # few_shot_prompt_template = ChatPromptTemplate.from_messages(
    #     [
    #         ("human", "{input}"),
    #         ("ai", "{output}"),
    #     ]
    # )

    # few_shot_prompt = FewShotChatMessagePromptTemplate(
    #     example_prompt=few_shot_prompt_template,
    #     examples=examples,
    # )

    grader_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                f"""You are an assistant specializing in EVM Blockchains. Your primary task is to evaluate user-provided descriptions based on their suitability for conversion into an Ethereum transaction.
1.	Grading: Rate each description on a scale of 1 to 10, with 1 being poorly suited and 10 being highly suited for transformation into an Ethereum transaction.
2.	Evaluation Criteria: Consider the following factors when grading:
- Clarity: Is the description clear and unambiguous?
- Completeness: Does the description include all necessary details for an Ethereum transaction (e.g., recipient, amount, etc.)?
- Accuracy: Does the description align with the structure and requirements of an Ethereum transaction?
- Feasibility: Is it technically possible to implement the transaction as described?""",
            ),
            ("human", "{description}"),
        ]
    )

    llm = model_provider.model
    chain = grader_prompt | llm.with_structured_output(DescriptionEvalResult)
    result = chain.invoke({"description": desc})
    return result


if __name__ == "__main__":
    import pandas as pd

    # evaluation_results = []
    # for case in read_transformed_cases():
    #     result = evaluate_case(case)
    #     evaluation_results.append(result)
    # df = pd.DataFrame(evaluation_results)
    # df.to_csv(f"evaluation_{model_name}.csv", index=False)

    results = []
    desc = "Swap 100 USDT to ETH"
    result = grade_description(desc).dict()
    result["description"] = desc
    results.append(result)
    print("Description:", result["description"])
    print("Score:", result["score"])
    print("Reason:", result["reason"])
    print("Action:", result["action"])

    print("--------------------------------")

    desc = "Send 100 USDT to A"
    result = grade_description(desc).dict()
    result["description"] = desc
    results.append(result)
    print("Description:", result["description"])
    print("Score:", result["score"])
    print("Reason:", result["reason"])
    print("Action:", result["action"])
