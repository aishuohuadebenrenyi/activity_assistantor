# Activity Assistant Frontend

This is the uni-app x frontend for Activity Assistant.

## Development

1. Open this directory (`frontend/`) in **HBuilderX**.
2. Run to Browser or App Playground.

## Backend Connection

The backend is located in the `../backend` directory.
Currently, the frontend uses mock data. To connect to the backend:
1. Update `store/index.uts` and page files to use `uni.request`.
2. Point API calls to `http://localhost:9000/api/...`.
