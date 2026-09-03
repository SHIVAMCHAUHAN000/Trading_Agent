"""
Script to test multi-turn context memory and quant brain orchestration.
"""

import asyncio
import sys

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from brain import quant_brain


async def main():
    session = "test_session_context_1"

    print("=== TURN 1: 'What is NIFTY doing?' ===")
    r1 = await quant_brain.process_query(session, "What is NIFTY doing?")
    print(f"Symbol: {r1['symbol']} | Intent: {r1['intent']}")
    print(r1["response"][:250] + "...\n")

    print("=== TURN 2: 'Why?' ===")
    r2 = await quant_brain.process_query(session, "Why?")
    print(f"Symbol: {r2['symbol']} | Intent: {r2['intent']}")
    print(r2["response"][:250] + "...\n")

    print("=== TURN 3: 'Where is liquidity?' ===")
    r3 = await quant_brain.process_query(session, "Where is liquidity?")
    print(f"Symbol: {r3['symbol']} | Intent: {r3['intent']}")
    print(r3["response"][:250] + "...\n")

    print("=== TURN 4: 'Price of gold?' ===")
    r4 = await quant_brain.process_query(session, "Price of gold?")
    print(f"Symbol: {r4['symbol']} | Intent: {r4['intent']}")
    print(r4["response"][:250] + "...\n")

    print("=== TURN 5: 'Is there a setup?' ===")
    r5 = await quant_brain.process_query(session, "Is there a setup?")
    print(f"Symbol: {r5['symbol']} | Intent: {r5['intent']}")
    print(r5["response"][:250] + "...\n")


if __name__ == "__main__":
    asyncio.run(main())
