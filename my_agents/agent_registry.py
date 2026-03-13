from my_agents.complaints_agent import complaints_agent
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent
from handoffs import make_handoff


def setup_agent_handoffs():
    all_agents = [complaints_agent, menu_agent, order_agent, reservation_agent]

    for agent in all_agents:
        agent.handoffs = [
            make_handoff(other)
            for other in all_agents
            if other.name != agent.name
        ]