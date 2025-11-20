'use client';

import { useState } from 'react';
import ImageUpload from '@/components/ImageUpload';
import { fileToBase64, generateUUID, saveImageToPublic } from '@/lib/utils';
import { getEmbedding, upsertVector } from '@/lib/api';

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const handleImageSelect = (file: File) => {
    setSelectedFile(file);
    setMessage(null);
    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage({ type: 'error', text: 'Please select an image first' });
      return;
    }

    setIsUploading(true);
    setMessage(null);

    try {
      // Step 1: Save image to public/images
      const filename = await saveImageToPublic(selectedFile);
      const imageUrl = `/images/${filename}`;

      // Step 2: Convert image to base64
      const imageBase64 = await fileToBase64(selectedFile);

      // Step 3: Get embedding from embedding API
      const embedding = await getEmbedding(imageBase64);

      // Step 4: Generate UUID and upsert vector
      const vectorId = generateUUID();
      await upsertVector(vectorId, embedding, imageUrl, selectedFile.name);

      setMessage({
        type: 'success',
        text: `Image uploaded successfully! Vector ID: ${vectorId}`,
      });

      // Reset form
      setSelectedFile(null);
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
    } catch (error) {
      console.error('Upload error:', error);
      setMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Failed to upload image',
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-center">
          Image Repository - Upload
        </h1>

        <div className="space-y-6">
          <ImageUpload
            onImageSelect={handleImageSelect}
            disabled={isUploading}
            label="Select an image to upload and index"
          />

          {previewUrl && (
            <div className="mt-4">
              <h2 className="text-xl font-semibold mb-2">Preview</h2>
              <div className="relative w-full max-w-md mx-auto">
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="w-full h-auto rounded-lg shadow-md"
                />
              </div>
            </div>
          )}

          {selectedFile && (
            <div className="text-center">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'Uploading...' : 'Upload and Index Image'}
              </button>
            </div>
          )}

          {message && (
            <div
              className={`p-4 rounded-lg ${
                message.type === 'success'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {message.text}
            </div>
          )}

          <div className="mt-8 text-center">
            <a
              href="/search"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              Go to Search Page →
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}

