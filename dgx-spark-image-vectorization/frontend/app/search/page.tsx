'use client';

import { useState } from 'react';
import ImageUpload from '@/components/ImageUpload';
import ImageGrid from '@/components/ImageGrid';
import { fileToBase64 } from '@/lib/utils';
import { getEmbedding, searchVectors, SearchResult } from '@/lib/api';

export default function SearchPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleImageSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);
    setResults([]);
    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleSearch = async () => {
    if (!selectedFile) {
      setError('Please select an image first');
      return;
    }

    setIsSearching(true);
    setError(null);
    setResults([]);

    try {
      // Step 1: Convert image to base64
      const imageBase64 = await fileToBase64(selectedFile);

      // Step 2: Get embedding from embedding API
      const queryVector = await getEmbedding(imageBase64);

      // Step 3: Search for similar vectors
      const searchResults = await searchVectors(queryVector, 4);

      setResults(searchResults);
    } catch (err) {
      console.error('Search error:', err);
      setError(err instanceof Error ? err.message : 'Failed to search images');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">
          Image Repository - Search
        </h1>

        <div className="space-y-6">
          <ImageUpload
            onImageSelect={handleImageSelect}
            disabled={isSearching}
            label="Select an image to find similar images"
          />

          {previewUrl && (
            <div className="mt-4">
              <h2 className="text-xl font-semibold mb-2">Query Image</h2>
              <div className="relative w-full max-w-md mx-auto">
                <img
                  src={previewUrl}
                  alt="Query preview"
                  className="w-full h-auto rounded-lg shadow-md"
                />
              </div>
            </div>
          )}

          {selectedFile && (
            <div className="text-center">
              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isSearching ? 'Searching...' : 'Find Similar Images'}
              </button>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-red-100 text-red-800">
              {error}
            </div>
          )}

          {results.length > 0 && (
            <div className="mt-8">
              <h2 className="text-2xl font-semibold mb-4">
                Similar Images ({results.length})
              </h2>
              <ImageGrid results={results} />
            </div>
          )}

          <div className="mt-8 text-center">
            <a
              href="/"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              ← Go to Upload Page
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}

