import { NextRequest, NextResponse } from 'next/server';
import { readFile } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

/**
 * API route to serve images from public/images/{topic}/{image_name}
 * This handles URL-encoded paths correctly
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  try {
    // Handle both sync and async params (Next.js 14+ uses async params)
    const resolvedParams = params instanceof Promise ? await params : params;
    
    // Decode the path segments
    const decodedPath = resolvedParams.path.map(segment => decodeURIComponent(segment));
    
    // Construct the file path
    const filePath = join(process.cwd(), 'public', 'images', ...decodedPath);
    
    // Check if file exists
    if (!existsSync(filePath)) {
      return NextResponse.json(
        { error: 'Image not found' },
        { status: 404 }
      );
    }
    
    // Read and serve the file
    const fileBuffer = await readFile(filePath);
    const fileExtension = decodedPath[decodedPath.length - 1].split('.').pop()?.toLowerCase();
    
    // Determine content type
    const contentType = fileExtension === 'jpg' || fileExtension === 'jpeg' 
      ? 'image/jpeg' 
      : fileExtension === 'png' 
      ? 'image/png' 
      : 'image/jpeg';
    
    return new NextResponse(fileBuffer, {
      headers: {
        'Content-Type': contentType,
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    });
  } catch (error) {
    console.error('Error serving image:', error);
    return NextResponse.json(
      { error: 'Failed to serve image' },
      { status: 500 }
    );
  }
}

