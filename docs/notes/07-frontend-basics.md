
# CaseMatch Frontend

## Overview

The CaseMatch frontend is built using React, TypeScript,
Vite, and Tailwind CSS.

It provides an interface for searching and reviewing
historical clinical cases.

CaseMatch is intended for case retrieval, not diagnosis.

## Technologies

- React
- TypeScript
- Vite
- Tailwind CSS

## Main Components

### Dashboard

The dashboard provides:
- A search bar for clinical keywords
- Recent searches
- Available case count
- A review queue placeholder

### Sidebar

The sidebar allows users to navigate between:
- Dashboard
- Search Cases

It also supports mobile navigation.

### Search Results

The Search Results page includes:
- Keyword search
- Ranked case cards
- Patient age and case summaries
- Symptom labels
- Loading and error messages
- Keyboard search using Enter

## API Integration

The frontend currently supports mock data and a
configurable backend connection.

Relevant files:

- src/api/cases.ts
- src/api/config.ts
- src/data/mockCases.ts

The .env file controls whether mock data is enabled.

Example configuration:

VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCK_DATA=true

The backend endpoint and JSON response format must
be confirmed with the backend team before integration.

## Running the Frontend

Open a terminal in the frontend directory.

Install dependencies:

npm install

Start the development server:

npm run dev

Open the local URL displayed by Vite, typically:

http://localhost:5173/

## Current Limitations

- Search currently uses fictional mock cases.
- Keyword scores are temporary demonstration scores.
- The review queue is not implemented.
- The case viewer is not implemented.
- Backend integration is pending.
- Recent searches are not saved after refreshing.

## Next Steps

- Confirm the backend API contract.
- Connect real case search results.
- Test responsive layouts and keyboard accessibility.
- Complete final integration testing.
