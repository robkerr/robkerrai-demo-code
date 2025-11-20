# Image Repository Frontend

Next.js application for uploading and searching images using vector similarity.

## Features

- **Upload Page**: Upload images, generate embeddings, and store vectors in Chroma
- **Search Page**: Find similar images using vector similarity search

## Setup

1. Install dependencies:
```bash
npm install
```

2. Make sure the backend services are running:
   - Image embedding service at `http://doc:8100`
   - Vector database API at `http://doc:8200`

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

- `app/page.tsx` - Upload page
- `app/search/page.tsx` - Search page
- `app/api/upload-image/route.ts` - API route for saving uploaded images
- `lib/api.ts` - Backend API client functions
- `lib/utils.ts` - Utility functions
- `components/` - Reusable React components
- `public/images/` - Directory for uploaded images (served at `/images/{filename}`)

## Usage

### Upload Page
1. Select or drag-and-drop an image
2. Click "Upload and Index Image"
3. The image will be saved to `public/images/` and its embedding will be stored in Chroma

### Search Page
1. Select or drag-and-drop a query image
2. Click "Find Similar Images"
3. View the top 4 most similar images
4. Click any thumbnail to view the full-size image in a modal

