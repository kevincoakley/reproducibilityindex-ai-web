# AGENTS.md

> Purpose: This file provides context, conventions, and setup instructions for AI agents working on this repository.

## 1. Project Overview
- Description: This repository contains the dynamic website using the Flask framework for the reproducibilityindex.ai project
- Language: Python
- Package Manager: `uv` (Do not use pip or poetry directly)

## 2. Directory Structure

```
.
├── .coveragerc                     # Coverage configuration file
├── .dockerignore                   # Docker ignore file
├── .gitignore                      # Git ignore file
├── .python-version                 # Python version file
├── AGENTS.md                       # This file
├── app                             # Flask application package 
│   ├── __init__.py                 # Package initializer
│   ├── datastore                   # Data access layer
│   │   ├── __init__.py             # Package initializer
│   │   ├── base.py                 # Base datastore interface
│   │   └── sqlite_store.py         # SQLite implementation of the datastore
│   ├── routes.py                   # Flask route definitions
│   ├── static                      # Static files (CSS, JS, images)
│   │   └── styles.css              # Main stylesheet
│   └── templates                   # HTML templates
│       ├── base.html               # Base template with common layout
│       ├── conference_results.html # Template for /conferences/<conference>
│       ├── conference_years.html   # Template for /conferences/<conference>/<year>
│       ├── home.html               # Template for homepage
│       ├── paper_detail.html       # Template for /paper/<key>
│       └── run_detail.html         # Template for /runs/<run>
├── Dockerfile                      # Docker configuration file
├── pyproject.toml                  # Project configuration
├── README.md                       # Project description
├── results.sqlite                  # SQLite database file for dynamic website
├── run.py                          # Entry point for running the dynamic website
├── technical-debt                  # Technical debt tracking
├── tests/                          # Directory for test files
└── uv.lock                         # Lock file for dependencies
```

## 3. Development Workflow & Commands
Always use `uv` for package management and script execution.

### Setup
- First time setup: `uv sync` (Installs environment based on lockfile)
- Update environment: `uv sync`

### Dependency Management
- Add production dependency: `uv add <package_name>`
- Add dev/test dependency: `uv add <package_name> --group test`
- Remove dependency: `uv remove <package_name>`

### Running Code
- Run script: `uv run python <script_path>`

### Testing
- Install test environment: `uv sync --group test`
- Run all tests: `uv run pytest`
- Write tests for new features
- Maintain existing test coverage
- Use pytest fixtures for common setup
- Create separate test files for each module
- Create test in a `tests/` directory at the root level
- Name test files as `test_<module>.py`
- Test coverage: `uv run pytest --cov=.`

## Development Workflow
1. Write/update tests first (TDD approach)
2. Implement changes
3. Run tests to ensure they pass
4. Format code with Black

## 4. Coding Conventions & Style

### Formatting
- Formatter: Black
  - Command: `uv run black .`
  - Rule: Always run formatting before declaring a task complete.
- Follow PEP 8 conventions
- Use type hints where appropriate
- Write docstrings for functions and classes

### Commenting
- Use clear and concise comments to explain non-obvious code
- Use docstrings for all public modules, functions, classes, and methods

### Type Hinting
- Use standard Python type hints for function arguments and return values.
- Example: `def my_func(name: str) -> int:`

## 5. Website Style Guidelines
- The website style should be Academic Minimalist or a Technical Documentation style
- Specific characteristics of this design include:
  - Clean Typography: It uses standard, highly legible sans-serif fonts with clear hierarchical headings to organize information.
  - Grid-Based Leaderboards: The central focus is a dense, sortable data table, which is typical for benchmarking and technical comparison sites.
  - Simple Iconography: It utilizes standard icons (like the GitHub "octocat" and paper icons) for quick navigation to code, data, and publications.
  - Functional Layout: There is very little "fluff" or decorative imagery; every element serves a direct purpose, such as providing introduction text, a changelog, or model rankings.
  - Bootstrap-inspired Aesthetic: The buttons, spacing, and overall responsiveness are reminiscent of modern web frameworks like Bootstrap or Tailwind, which are commonly used for scientific and open-source project pages.
- Always use Chart.js (https://www.chartjs.org) for any charts or visualizations on the website.
- The title of the website should be: reproducibilityindex.ai . However, this should be a varaible and not hard coded.
- Always use Tippy.js v6 (https://atomiks.github.io/tippyjs/) for all tooltips on the website. It is loaded via CDN in `base.html` and therefore applies site-wide. Load order matters: `@popperjs/core@2` must come before `tippy.js@6` (use the unpkg.com URLs from the official docs).
  - Tooltips are triggered by elements with class `tooltip-wrap`; the tooltip content is in a child element with class `tooltip-text`.
  - All tooltips must use `interactive: true` so users can hover into and copy text from tooltips without it closing.
  - Use the custom `site` theme defined in `styles.css` for consistent dark styling.
  - Inline citation tooltips are defined in `app/templates/_references.html` using the `cite(key, label)` Jinja2 macro.
  - Info-icon tooltips (ⓘ) use text from `app/templates/_tooltips.html` via the `text(key)` Jinja2 macro.

### 6. Database
- The database will only read data from the database never write to the database
- The database is at results.sqlite, please read the database if you have any questions about the format:
  - authors_list -> the authors for each paper.
  - countries -> a list of the countries to be displayed.
  - countries_documentation_scores -> the documentation scores for each of the countries.
  - countries_reproducibility_scores -> the reproducibility scores for each of the countries.
  - editions -> a list of the editions for each of the venues.
  - editions_reproducibility_scores -> the reproducibility scores for each of the editions.
  - institutions -> a list of the institutions to be displayed.
  - institutions_documentation_scores -> the documentation scores for each of the institutions.
  - institutions_reproducibility_scores -> the reproducibility scores for each of the institutions.
  - results -> the results of our analysis of the papers. 
  - runs -> details about how the results were found.
  - venue_stats -> the statistics for each of the venues.
  - venues -> a list of the venues to be displayed.
  - year_stats -> the statistics for each of the years.
- Database table links:
  - authors_list.venue = editions.venue = countries_documentation_scores.venue = results.venue = venues.venue = venue_stats.venue
  - authors_list.year = editions.year = countries_documentation_scores.year = results.year = year_stats.year
  - authors_list.run = results.run = runs.run
  - authors_list.key = results.key
  - authors_list.country = countries.country
  - authors_list.institution_normalized = institutions.key
  - countries_documentation_scores.country = countries.country
  - countries_reproducibility_scores.country = countries.country
  - institutions_documentation_scores.institution_normalized = institutions.key
  - institutions_reproducibility_scores.institution_normalized = institutions.key

### 7. Deployment
- The website will be deployed using Docker in production.
- The Dockerfile should be simple and efficient, using a lightweight Python base image.
- Don't include unnecessary files in the Docker image (use .dockerignore effectively).
- Update the Dockerfile when changes are made that might affect the production environment (e.g. new dependencies, changes to how the app is run).
- Update the README.md with instructions for running the code in production using Docker.

### 8. Technical Debt
- The technical debt is tracked in the `technical-debt` directory.
- When I ask you to track technical debt, create a new file in the `technical-debt` directory with the name `YYYY-MM-DD-<description>.md`.
- The file should be a markdown file with the following format:
```markdown
# Technical Debt

## Description

## Solution

## Impact
```

## 9. Critical Rules for Agents
- Do not update `uv.lock` manually. Use `uv add` or `uv sync`.
- Check `pyproject.toml` to see existing dependencies before adding new ones.
- Run tests after every significant code change to ensure no regressions.
- Ensure code is formatted with Black
- Preserve existing code style and patterns
- Aways update the README.md file with instructions for running the code. Be concise, don't include unnecessary information. Focus on how to run the code for testing (unit tests and dev server) and in production.
- Keep the website very simple, it will consist of a few static pages and a few dynamic paths using data from a read-only database.
- Ask for clarification if requirements are unclear
