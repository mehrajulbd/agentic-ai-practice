# Task 1

The Goal: 
Build an RPG engine where the LLM cannot simply "hallucinate" items. It must use tools to interact with a persistent world state.

The Tools:
 - get_inventory(): Returns a list of items from a local JSON file
 - use_item(item_id, target): Updates the JSON file to remove/modify items.

Structured Output: 
Force the LLM to return every response in a JSON schema containing narrative_text, current_hp, and available_actions[].

Note: 
The LLM must verify if an item exists via tool calling before it is allowed to describe the player using it in the narrative.



# Task 2
Build a support agent that actually checks order status and processes refunds, but only if certain conditions are met.

The Tools: 
- check_order(id): Returns order date and status.
- process_refund(id): Returns success/failure.

Prompting: 
Use System Instructions to enforce a strict policy: "Only refund if the order is < 30 days old and status is 'Damaged'."

Note: 
The agent must use check_order first. It is strictly forbidden from calling process_refund unless the data from the first tool call satisfies the policy.