from ops_eval.agents.greedy import GreedyAgent
from ops_eval.agents.policy import PolicyAgent

AGENTS = {
    "reference": GreedyAgent,
    "greedy": GreedyAgent,
    "policy": PolicyAgent,
}
