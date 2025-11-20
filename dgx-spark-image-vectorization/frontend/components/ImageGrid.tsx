'use client';

import ImageModal from './ImageModal';
import { useState } from 'react';
import { constructImageUrl } from '@/lib/api';

interface ImageResult {
  id: string;
  score: number;
  metadata: {
    topic: string;
    image_name: string;
  };
}

interface ImageGridProps {
  results: ImageResult[];
}

export default function ImageGrid({ results }: ImageGridProps) {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  if (results.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No similar images found
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
        {results.map((result) => {
          const imageUrl = constructImageUrl(result.metadata.topic, result.metadata.image_name);
          return (
            <div
              key={result.id}
              className="relative group cursor-pointer overflow-hidden rounded-lg shadow-md hover:shadow-xl transition-shadow"
              onClick={() => setSelectedImage(imageUrl)}
            >
              <div className="aspect-square relative">
                {/* topic={encodeURIComponent(result.metadata.topic)}
                image_name={encodeURIComponent(result.metadata.image_name)}
                imageUrl={`http://localhost:3000/images/${encodeURIComponent(result.metadata.topic)}/${encodeURIComponent(result.metadata.image_name)}`} */}
                <img
                  src={`http://localhost:3000/images/${encodeURIComponent(result.metadata.topic)}/${encodeURIComponent(result.metadata.image_name)}`}
                  alt={result.metadata.image_name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.src = '/placeholder-image.png';
                  }}
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-opacity flex items-center justify-center">
                  <span className="text-white opacity-0 group-hover:opacity-100 text-sm font-medium">
                    Click to view full size
                  </span>
                </div>
              </div>
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                <p className="text-white text-xs truncate">
                  {result.metadata.image_name}
                </p>
                <p className="text-white/80 text-xs">
                  Similarity: {(1 - result.score).toFixed(3)}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {selectedImage && (
        <ImageModal
          imageUrl={selectedImage}
          onClose={() => setSelectedImage(null)}
        />
      )}
    </>
  );
}

