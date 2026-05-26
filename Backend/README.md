# Pet First-Aid Web Application - Backend API Prototype

This repository contains the complete 5-Tier RESTful API backend for the **Pet First-Aid Web Application** prototype. It is architected strictly using standard object-oriented patterns in Python, Flask, and MongoDB (`pymongo`) without heavy ORMs.

---

## 🏗️ Architectural Overview (5-Tier Framework)

The project codebase strictly isolates data concerns, domain structures, and presentation contracts across independent logic layers:

1. **Data Access Layer (`database.py`)**
   * Implemented as a thread-safe Singleton wrapper.
   * **The exclusive module permitted to import `pymongo`.**
   * Uses atomic write operations (e.g., `find_one_and_update`, `$push`, `$inc`) to prevent operational race conditions.
   * Enforces compound database indexes and contains a robust tracking data automation method (`seed_data()`).

2. **Domain / Entity Layer (`models.py`)**
   * Lightweight entity containers enforcing strict validation constraints during object constructor initialization.
   * Provides decoupled mapping serialization capabilities (`toDict()` and `fromDict()`) to interact seamlessly with database documents and web JSON outputs.

3. **Business Logic / Control Layer (`services.py`)**
   * Houses independent, coordinate Control entities (`AuthenticationManager`, `TriageEngine`, `SearchEngine`, etc.).
   * Handles user role verification, rule execution paths, and structural status changes.

4. **Application Routing Layer (`app.py`)**
   * The REST API gateway exposing endpoint bindings returning standardized JSON objects.
   * Employs robust error validation and context lifecycle cleanup hooks.

---

## Directory Structure

Ensure your local backend root workspace directory matches this layout before pushing/running:

```text
PFA/
│
├── env/                  <-- Virtual environment folder (Excluded from git tracking)
│
├── database.py           <-- Tier 1 & 2: Database Singleton & indexing hooks
├── models.py             <-- Tier 3: Program domain object definition blueprints
├── services.py           <-- Tier 4: Business logic automation control units
├── app.py                <-- Tier 5: REST API Flask routing manager (JSON endpoints)
│
└── requirements.txt      <-- Pinned core dependency workspace environment configurations