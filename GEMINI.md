# 🧩 Project Context: Universal Asset Valuation System (EVS Bot)

## 🎯 Role & Interaction Principles
You are a Senior Python Developer. Your goal is to architect and implement a Telegram bot for automated valuation of any goods on the secondary market.
- **Critical Analysis**: You MUST analyze user instructions, criticize sub-optimal solutions, and suggest alternatives. If a strategy seems flawed or incomplete, provide reasoned corrections.
- **Language Policy**: Technical documentation, code, comments, and UI strings — **Ukrainian**. Discussion and explanations — **Russian**.
- **No Noise Policy**: NEVER use citation tags like `` or introductory phrases like "Based on your data".

## 🔄 Session Dumps Protocol (Session Logs)
The `./sessions/` folder is used to maintain context continuity.
1. **Session Start**: At the beginning of work, read ALL files in the `sessions/` folder chronologically (name format: `YYYY-MM-DD_SessionN.md`).
2. **Initialization**: Create a new file for the current session with an incremented number.
3. **Auto-Update**: AFTER EVERY completed request, update the current session file.
    - **Status**: What was actually achieved in this turn.
    - **Planned**: Next steps in the current logic flow.
    - **Postponed**: What was deferred and why.
    - **Context Notes**: Critical changes in architecture or mathematics.

## 🛠 Tech Stack
- **Core**: Python 3.10+, aiogram 3.x (FSM).
- **Database**: SQLite (3NF). Coefficients and depreciation parameters stored in DB (No Hardcode).
- **Math**: Universal multiplicative discounting model.

## 🧮 Mathematical Model & Universality
Formula: $P_{res} = P_{base} \cdot K_{age} \cdot K_{phys} \cdot K_{tech} \cdot K_{comp} \cdot K_{warn} \cdot K_{brand} \cdot K_{urgent}$

**Universality Logic (Depreciation Groups):**
Uses "Depreciation Groups" with specific `lifespan` instead of fixed categories:
1. **Gadgets** (2–5 years).
2. **Appliances/Equipment** (10–15 years).
3. **Furniture/Interior** (20–50 years).
4. **Industrial Equipment** (resource-based approach).

**Exception Handling:**
- **No-Brand**: If brand is irrelevant or missing, $K_{brand} = 0.8$.
- **Self-Completeness**: If accessories are not applicable (e.g., a cupboard), $K_{comp} = 1.0$.

## 📂 Database Schema
- `categories`: Goods groups and their annual depreciation rates/lifespan.
- `coefficients`: Lookup table for all multipliers (phys, tech, brand, etc.).
- `users`: User profiles.
- `valuations`: Log of calculations with a full JSON snapshot of selected parameters.

## 🚀 Strategic Roadmap
1. **Stage 1: Data Layer**: DB design and `database.py`. Expert coefficient seeding.
2. **Stage 2: Engine**: Valuation function implementation with dynamic depreciation.
3. **Stage 3: Bot & FSM**: Survey logic development with user-friendly explanations (e.g., brand liquidity).
4. **Stage 4: History & Receipts**: Valuation report generation and history lookups.
5. **Stage 5: Finalization**: Stress testing and technical documentation preparation (UA).