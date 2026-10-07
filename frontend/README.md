# Campus Customs front end

Vite + React + TypeScript. See the [main README](../README.md) for how to run the whole site.

```
npm install
npm run dev     # http://localhost:5173 (expects the backend on port 8000)
npm run build   # type-check and build to dist/
npm run lint
```

`/api` and `/images` requests are proxied to the FastAPI backend in `vite.config.ts`.
