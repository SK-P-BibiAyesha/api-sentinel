# API Drift Detection and Backward Compatibility Analysis

An automated tool to compare two versions of an API specification, identify changes, detect potential breaking changes, and generate a compatibility report.

<p align="center">
  <a href="https://api-sentinel-delta.vercel.app">Live Demo</a> •
  <a href="https://api-sentinel-r2c6.onrender.com/docs">API Documentation</a> •
  <a href="https://github.com/SK-P-BibiAyesha/api-sentinel">Source Code</a>
</p>

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Abstract](#2-abstract)
3. [Problem Statement](#3-problem-statement)
4. [Why This Project Is Needed](#4-why-this-project-is-needed)
5. [Proposed Solution](#5-proposed-solution)
6. [Objectives](#6-objectives)
7. [Scope of the Project](#7-scope-of-the-project)
8. [Key Features](#8-key-features)
9. [How the System Works](#9-how-the-system-works)
10. [System Architecture](#10-system-architecture)
11. [Technology Stack](#11-technology-stack)
12. [API Drift and Breaking Changes](#12-api-drift-and-breaking-changes)
13. [Example Input](#13-example-input)
14. [Example Output](#14-example-output)
15. [Project Structure](#15-project-structure)
16. [System Requirements](#16-system-requirements)
17. [Installation and Setup](#17-installation-and-setup)
18. [Running the Project](#18-running-the-project)
19. [Using the Application](#19-using-the-application)
20. [Testing](#20-testing)
21. [Deployment](#21-deployment)
22. [Report Export](#22-report-export)
23. [Advantages](#23-advantages)
24. [Limitations](#24-limitations)
25. [Future Enhancements](#25-future-enhancements)
26. [Applications](#26-applications)
27. [Learning Outcomes](#27-learning-outcomes)
28. [Contributing](#28-contributing)
29. [License](#29-license)
30. [Author and Project Links](#30-author-and-project-links)

---

## 1. Project Overview

**Project Title:** API Drift Detection and Backward Compatibility Analysis

**Project Category:** Software Engineering, API Testing, and Developer Tools

**Project Type:** Web-based API specification comparison and compatibility analysis tool

This project helps developers understand what has changed between two versions of an API.

An API allows two software applications to communicate with each other. When an API changes, applications that depend on it may stop working correctly.

This tool compares an older API specification with a newer specification and identifies changes that may affect existing applications.

The results are displayed in a report containing detected changes, their severity, a summary, and an overall compatibility verdict.

### Project Links

- **Live application:** https://api-sentinel-delta.vercel.app
- **Backend API documentation:** https://api-sentinel-r2c6.onrender.com/docs
- **Backend health endpoint:** https://api-sentinel-r2c6.onrender.com/health
- **GitHub repository:** https://github.com/SK-P-BibiAyesha/api-sentinel

---

## 2. Abstract

Application Programming Interfaces (APIs) are important components of modern software systems. They allow different applications and services to exchange data and communicate with one another.

As software evolves, API specifications may change. Some changes are compatible with existing applications, while others can cause errors or require changes in client-side code. Identifying these changes manually can be time-consuming and error-prone.

The proposed project, **API Drift Detection and Backward Compatibility Analysis**, provides a web-based approach to comparing two versions of an API specification. The system accepts OpenAPI specification files in supported JSON or YAML formats, analyzes the differences, applies compatibility rules, and identifies potential breaking changes.

The backend processes the specifications and returns structured findings. The frontend presents the results in an understandable dashboard, including change summaries, severity information, and an overall compatibility verdict. The application also provides report-export functionality where implemented.

The main goal is to help developers discover potentially dangerous API changes before releasing an updated API, reducing manual checking and improving awareness of backward compatibility risks.

**Keywords:** API Drift, Backward Compatibility, OpenAPI, API Testing, Breaking Changes, FastAPI, React, Software Quality.

---

## 3. Problem Statement

APIs are frequently updated to introduce new features, modify existing behavior, and improve software systems.

However, a change in an API may affect applications that already depend on its previous version.

For example:
- A response field used by a client application is removed.
- A field changes from a number to a string.
- An endpoint or operation is removed or modified.
- A required parameter changes and existing requests no longer satisfy the API contract.

Developers may need to compare API specifications manually to identify these changes. This can become difficult when an API contains many endpoints, parameters, schemas, and response fields.

**Problem:** There is a need for an automated tool that compares API specification versions, highlights potential breaking changes, and presents the results in a clear report.

---

## 4. Why This Project Is Needed

Without automated comparison, developers may overlook changes that affect existing API consumers.

This project aims to address the following challenges:

- Manual comparison requires time and attention.
- Important changes may be hidden in large specification files.
- Incompatible changes can cause failures in applications that depend on an API.
- Developers need a clear summary instead of manually inspecting every difference.
- Teams need information about the severity and impact of detected changes before releasing a new version.

The project supports early detection of potential compatibility problems. It does not replace complete integration testing or guarantee that every runtime problem will be detected.

---

## 5. Proposed Solution

The proposed system provides a web interface where users can supply an old API specification and a new API specification.

The backend analyzes both specifications and identifies changes according to the implemented comparison and compatibility rules.

The system then displays a report containing the detected changes, their classifications, and a summary of the comparison.

### Proposed workflow

1. The user opens the web application.
2. The user provides the previous API specification.
3. The user provides the updated API specification.
4. The frontend sends the specifications to the backend.
5. The backend parses and validates the supported inputs.
6. The comparison engine identifies differences.
7. Compatibility rules classify applicable changes.
8. The system prepares a structured report.
9. The frontend displays the results.
10. The user reviews the findings and exports the report when needed.

---

## 6. Objectives

The main objectives of the project are:

- To automate the comparison of two API specification versions.
- To detect API changes that may affect existing clients.
- To identify potential breaking changes using compatibility rules.
- To classify findings according to the implemented severity categories.
- To display a clear summary of detected changes.
- To provide an overall compatibility verdict based on the implemented rules.
- To make API comparison easier through a web-based interface.
- To support report export for documentation and review.
- To help developers identify compatibility risks before releasing API updates.

---

## 7. Scope of the Project

### Included in the current project

- Comparison of older and newer API specifications.
- Support for OpenAPI 3.x specifications in supported JSON and YAML formats.
- Identification of supported API structure and schema changes.
- Compatibility analysis based on implemented rules.
- Structured findings and summary counts.
- An overall PASS/FAIL verdict according to the configured analysis rules.
- A React-based user interface.
- A FastAPI backend.
- Report export functionality implemented in the frontend.

### Outside the current scope

The project should not be considered a complete replacement for runtime API testing, security testing, performance testing, or end-to-end integration testing.

Its analysis is based primarily on API specifications and the rules implemented in the comparison engine. It cannot guarantee the detection of every semantic, business-logic, or runtime incompatibility.

---

## 8. Key Features

### 8.1 API Specification Comparison

Compares an older API specification with an updated specification to identify differences.

### 8.2 Breaking Change Detection

Highlights changes that may cause existing API consumers to fail or require modifications.

### 8.3 Change Classification

Organizes detected changes according to the severity categories supported by the implementation.

### 8.4 Summary Dashboard

Presents important comparison information, such as total changes, breaking changes, warnings, and the overall result.

### 8.5 Detailed Findings

Provides information about individual findings, including the affected operation or location and an explanation of the detected change where available.

### 8.6 Compatibility Verdict

Displays a PASS or FAIL result according to the project's implemented compatibility rules.

### 8.7 Report Export

Provides available export options for saving and sharing comparison results.

### 8.8 Web-Based Interface

Uses a React frontend to make the comparison workflow easier to use.

### 8.9 Backend API

Uses FastAPI to expose backend functionality and provide structured responses to the frontend.

---

## 9. How the System Works

The project can be understood through five main stages.

**Stage 1 — Input**

The user provides the older and newer API specification files.

**Stage 2 — Parsing**

The backend reads the supported specification formats and prepares their API information for comparison.

**Stage 3 — Comparison**

The comparison engine examines the supported parts of the specifications and identifies differences.

**Stage 4 — Compatibility Analysis**

The system applies the implemented rules to classify changes and determine which findings may be breaking.

**Stage 5 — Report Generation**

The backend returns a structured result, and the frontend displays the summary and detailed findings.

### Simplified flow

```text
Old API Specification
          |
          v
     Input Parsing
          |
          |       New API Specification
          |                 |
          +--------+--------+
                   |
                   v
          API Comparison Engine
                   |
                   v
        Compatibility Rule Analysis
                   |
                   v
            Findings and Summary
                   |
                   v
          Frontend Results Dashboard
                   |
                   v
            Review / Export
```

---

## 10. System Architecture

The project uses a frontend-backend architecture.

### Frontend Layer

The frontend provides the user interface for submitting specifications, starting comparisons, viewing findings, and exporting reports.

### Backend Layer

The backend receives requests, processes the input specifications, executes the comparison logic, and returns structured results.

### Comparison Engine

The comparison engine identifies differences between API versions and applies compatibility rules to classify supported changes.

### Report Layer

The report layer presents the comparison summary and individual findings in a form that users can review.

### Architecture diagram

```text
+----------------------------------+
|             User                 |
+----------------------------------+
                 |
                 v
+----------------------------------+
|       React 19 + Vite            |
|      Frontend Dashboard          |
+----------------------------------+
                 |
                 | HTTP Requests
                 v
+----------------------------------+
|          FastAPI Backend         |
|      Request Processing          |
+----------------------------------+
                 |
                 v
+----------------------------------+
|       API Comparison Engine      |
|                                  |
|  - Specification Comparison      |
|  - Compatibility Rules           |
|  - Finding Classification        |
|  - Result Summary                |
+----------------------------------+
                 |
                 v
+----------------------------------+
|       Structured JSON Result     |
+----------------------------------+
                 |
                 v
+----------------------------------+
|       Results Dashboard          |
|        Report Export             |
+----------------------------------+
```

---

## 11. Technology Stack

| Layer | Technologies | Purpose |
|---|---|---|
| Frontend | HTML5, CSS3, JavaScript ES6+ | Page structure, styling, and interactions |
| Frontend framework | React 19 | Reusable UI components |
| Development and build | Vite | Frontend development server and production builds |
| HTTP communication | Fetch API | Communication between frontend and backend |
| PDF generation | jsPDF | PDF export where implemented |
| Backend language | Python | Backend logic and comparison processing |
| Backend framework | FastAPI | HTTP endpoints and request handling |
| Input specifications | OpenAPI 3.x, JSON, YAML | API contracts being compared |
| Testing | pytest | Automated backend tests |
| Source control | Git and GitHub | Version control and collaboration |
| Frontend hosting | Vercel | Deployment of the frontend |
| Backend hosting | Render | Deployment of the backend |

The table describes the project's known stack. Additional dependencies should be documented according to the current source code and dependency files.

---

## 12. API Drift and Breaking Changes

### What is API drift?

API drift occurs when an API specification or contract changes between versions.

Some changes are safe for existing consumers, while others may require client applications to change.

### What is backward compatibility?

An API update is backward compatible when existing clients can continue to interact with it successfully under the relevant contract and behavior assumptions.

### What is a breaking change?

A breaking change is a change that can cause an existing client to fail or require modifications to keep working.

### Examples of API changes

| Change | Potential impact |
|---|---|
| Removing a response field | Existing clients may fail if they depend on that field |
| Changing a field's data type | Client parsing or processing may fail |
| Removing an operation | Existing requests may no longer be supported |
| Adding an optional response field | Often compatible, depending on the client |
| Adding a required request parameter | Existing requests may become invalid |

These are general examples. Whether a change is detected and how it is classified depends on the project's implemented rules.

---

## 13. Example Input

Consider an API that returns product information.

### Old API response

```json
{
  "productId": 101,
  "productName": "Laptop",
  "price": 55000
}
```

### New API response

```json
{
  "productId": 101,
  "price": "55000",
  "category": "Electronics"
}
```

### Changes

1. The `productName` field has been removed.
2. The `price` field has changed from a number to a string.
3. The `category` field has been added.

### Possible impact

- A client that expects `productName` may fail to display the product name.
- A client that performs numeric calculations using `price` may need changes.
- A newly added field may be harmless to clients that ignore unknown fields.

The comparison engine can identify the supported structural differences. The actual effect on an application depends on how that application uses the API.

---

## 14. Example Output

A sample result from a project comparison is shown below.

```json
{
  "old_version": "1.0.0",
  "new_version": "2.0.0",
  "total_changes": 7,
  "breaking_changes": 4,
  "warnings": 0,
  "result": "FAIL",
  "findings": [
    {
      "severity": "BREAKING",
      "description": "Response field removed"
    },
    {
      "severity": "INFO",
      "description": "Response field added"
    }
  ]
}
```

**Note:** This is an abbreviated illustrative response based on the project's earlier test output. It is not a complete report, and the findings shown here are not intended to reproduce every field in the live API response.

### Understanding the result

- `old_version`: identifies the earlier API version.
- `new_version`: identifies the updated API version.
- `total_changes`: the total number of changes reported.
- `breaking_changes`: the number of findings classified as breaking.
- `warnings`: the number of warnings reported.
- `result`: the overall verdict produced by the implemented rules.
- `findings`: details about the individual detected changes.

A `FAIL` result indicates that the comparison has met the project's configured failure conditions. It should not be interpreted as proof that every client will fail.

---

## 15. Project Structure

The exact directory layout should match the current repository. The following is a conceptual overview of the main components.

```text
api-sentinel/
|
|-- frontend/
|   |-- src/
|   |-- public/
|   |-- package.json
|   |-- vite.config.js
|   `-- index.html
|
|-- backend/
|   |-- api.py
|   |-- comparator.py
|   `-- ...
|
|-- main.py
|-- tests/
|-- requirements.txt
|-- README.md
|-- API_Drift_Detection_Project_Documentation.docx
`-- Automated-Microservice-API-Drift-Detector-and-Backward-Compatibility-Breaking-Change-Linter.pptx
```

**Important:** This is a documentation example, not a verified file listing. Keep only the directories and filenames that actually exist in your repository. The location of your frontend and test files may differ.

### Main components

- **Frontend:** provides the user interface and renders comparison results.
- **Backend API:** receives requests and returns structured responses.
- **Comparator:** compares the two specifications.
- **Compatibility rules:** classify supported changes.
- **Tests:** verify expected behavior of the backend logic.
- **Documentation:** explains the project, setup, architecture, and results.

---

## 16. System Requirements

### Hardware

- A computer running Windows, Linux, or macOS.
- At least 4 GB RAM; 8 GB is recommended for a smoother development experience.
- Sufficient free disk space for Python packages, Node.js packages, and the project files.
- An internet connection for installing dependencies and accessing the deployed application.

### Software

- Python compatible with the project's backend dependencies.
- Node.js and npm.
- Git.
- A code editor such as Visual Studio Code.
- A modern web browser.
- Supported OpenAPI JSON or YAML input files.

Use the Python version and dependency versions specified by the current project files whenever available.

---

## 17. Installation and Setup

### Step 1: Clone the repository

```powershell
git clone https://github.com/SK-P-BibiAyesha/api-sentinel.git
cd api-sentinel
```

### Step 2: Create a Python virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install backend dependencies

If the project has a root-level `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

If the requirements file is located inside the backend directory, use the corresponding path instead.

### Step 4: Install frontend dependencies

Navigate to the actual frontend directory containing `package.json`.

For example, if it is located in `frontend`:

```powershell
cd frontend
npm install
```

If `package.json` is located at the repository root, run `npm install` there instead.

---

## 18. Running the Project

Run the frontend and backend in separate terminal windows.

### Start the backend

From the project root, activate the virtual environment and use the actual FastAPI application module.

For example, if `backend/api.py` exposes a FastAPI object named `app`, run:

```powershell
python -m uvicorn backend.api:app --reload
```

If your FastAPI application object is defined in a different module, adjust the command to match the actual file and object name.

When running locally, the backend may be available at:

```text
http://127.0.0.1:8000
```

The interactive API documentation is typically available at:

```text
http://127.0.0.1:8000/docs
```

### Start the frontend

Open another terminal, navigate to the directory containing `package.json`, and run:

```powershell
npm run dev
```

Vite will print the local frontend URL in the terminal. Open that URL in your browser.

### Build the frontend for production

From the frontend project directory:

```powershell
npm run build
```

This creates a production build using the project's Vite configuration.

**Note:** The commands above assume conventional file locations. Check your actual files and scripts before running them.

---

## 19. Using the Application

Follow these steps to compare two API versions.

1. Open the [live application](https://api-sentinel-delta.vercel.app).
2. Locate the API comparison interface.
3. Provide the older API specification.
4. Provide the newer API specification.
5. Start the comparison using the available interface control.
6. Wait for the backend to process the request.
7. Review the total changes and breaking-change summary.
8. Inspect individual findings to understand the detected differences.
9. Review the overall PASS/FAIL verdict.
10. Export the report using the available download option, if needed.

The precise labels and available controls may vary with the current frontend implementation.

---

## 20. Testing

Automated tests help verify that the backend behaves as expected for supported comparison cases.

The project previously passed a test run with **108 passing tests**. Test results can change as the code changes, so run the suite again before claiming the latest test status.

### Run the tests

From the project root with the virtual environment activated:

```powershell
python -m pytest -q
```

### What to verify

- The application handles valid specification inputs.
- Supported changes are detected.
- Compatibility rules classify supported findings correctly.
- The summary counts match the findings.
- The overall verdict follows the configured rules.
- Invalid inputs and error conditions are handled appropriately.
- The frontend can communicate with the backend.

A passing test suite verifies only the behaviors covered by those tests; it does not prove that every possible API incompatibility can be detected.

---

## 21. Deployment

The project is deployed using separate frontend and backend services.

### Frontend deployment

**Platform:** Vercel

**Live URL:** https://api-sentinel-delta.vercel.app

The frontend communicates with the backend using its configured API base URL.

The deployment configuration uses this environment variable:

```text
VITE_API_BASE_URL=https://api-sentinel-r2c6.onrender.com
```

Set the variable in the Vercel project settings for the relevant deployment environment, then redeploy if required.

### Backend deployment

**Platform:** Render

**Backend URL:** https://api-sentinel-r2c6.onrender.com

**API documentation:** https://api-sentinel-r2c6.onrender.com/docs

**Health endpoint:** https://api-sentinel-r2c6.onrender.com/health

The backend must be running and accessible for the frontend's comparison requests to succeed.

The health endpoint can be used to check service availability. A successful health response alone does not guarantee that every comparison operation works correctly.

---

## 22. Report Export

The frontend provides report-export functionality for saving comparison results.

Available formats depend on the current implementation and interface.

### PDF report

PDF export is useful for presenting or sharing a comparison report in a readable format.

### JSON report

JSON is useful for retaining structured comparison data or examining findings programmatically, where supported.

Exported reports should be reviewed before being shared to ensure that they contain the expected data and do not expose sensitive API information.

---

## 23. Advantages

- Reduces the effort required to manually compare API specifications.
- Helps identify potential breaking changes earlier.
- Presents findings in a structured and understandable format.
- Provides a web-based interface for reviewing comparison results.
- Supports an automated compatibility-analysis workflow.
- Helps developers understand how API changes may affect existing consumers.
- Can be integrated into future development and release workflows.
- Supports documentation and review through report exports.

---

## 24. Limitations

- Detection is limited to the changes and compatibility rules implemented in the project.
- Specification comparison alone cannot identify every runtime or business-logic incompatibility.
- Some changes require understanding how individual clients use the API.
- The quality of the results depends on the quality and completeness of the input specifications.
- A PASS verdict does not guarantee that every existing client will work correctly.
- A FAIL verdict indicates that the configured rules found a condition requiring attention; the exact impact should still be reviewed.
- The project does not replace integration tests, contract tests, security checks, or production monitoring.

---

## 25. Future Enhancements

Possible future improvements include:

1. **CI/CD integration:** Run API compatibility checks automatically during pull requests and release pipelines.
2. **More detailed recommendations:** Explain how developers can address each detected breaking change.
3. **Improved rule coverage:** Add and validate additional OpenAPI compatibility rules.
4. **Historical comparison:** Compare multiple API versions and track changes over time.
5. **Report improvements:** Add more detailed PDF and machine-readable reports.
6. **Team collaboration:** Allow team members to review and discuss findings.
7. **Configurable policies:** Let teams define their own compatibility requirements.
8. **Test generation:** Generate suggested test cases for detected changes.
9. **Change visualization:** Display API changes in a clearer visual format.
10. **Performance improvements:** Optimize comparison of large specifications.

These are proposed enhancements and should not be understood as features already implemented.

---

## 26. Applications

The project can be useful in:

- Microservice-based applications.
- Backend API development.
- API version migration.
- Software maintenance.
- Code review and release preparation.
- Development teams maintaining public or internal APIs.
- Systems where multiple client applications depend on the same API.
- Educational demonstrations of API contracts and backward compatibility.

---

## 27. Learning Outcomes

This project provides practical experience with:

- Understanding API contracts and OpenAPI specifications.
- Comparing structured data.
- Applying rule-based compatibility analysis.
- Developing REST endpoints using FastAPI.
- Building a frontend using React.
- Connecting a frontend to a backend using HTTP requests.
- Writing automated tests with pytest.
- Using Git and GitHub for source control.
- Deploying web applications with Vercel and Render.
- Communicating technical findings through reports and documentation.

---

## 28. Contributing

Contributions and suggestions are welcome.

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes.
4. Add or update relevant tests.
5. Run the test suite.
6. Commit your changes with a clear message.
7. Push your branch.
8. Open a pull request describing your changes.

Example:

```bash
git checkout -b feature/improve-compatibility-rules
git add .
git commit -m "Improve API compatibility analysis"
git push origin feature/improve-compatibility-rules
```

Before submitting a contribution, check that the change does not unintentionally alter existing comparison behavior.

---

## 29. License

No license has been specified in this documentation.

Before making the repository public for reuse, choose an appropriate open-source license and add a `LICENSE` file. Until a license is added, do not assume that others have permission to reuse, modify, or redistribute the source code.

---

## 30. Author and Project Links

**Project:** API Drift Detection and Backward Compatibility Analysis

**GitHub Repository:**  
https://github.com/SK-P-BibiAyesha/api-sentinel

**Live Application:**  
https://api-sentinel-delta.vercel.app

**Backend API Documentation:**  
https://api-sentinel-r2c6.onrender.com/docs

**Backend Health Endpoint:**  
https://api-sentinel-r2c6.onrender.com/health

### Conclusion

API Drift Detection and Backward Compatibility Analysis aims to make API specification comparison easier, faster, and more understandable.

By comparing API versions and identifying potential compatibility risks, the project helps developers review changes before releasing updates. Its web-based interface and structured reports make the comparison process more accessible, while further rule coverage, automated testing, and CI/CD integration offer opportunities for future improvement.

**The main goal is simple: identify potentially risky API changes before they become problems for applications that depend on the API.**
