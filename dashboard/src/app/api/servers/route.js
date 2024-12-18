// src/app/api/servers/route.js
import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';

export async function GET() {
  try {
    const aws = new AWSWrapper();
    return NextResponse.json({ servers: [] });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { message: 'Internal server error' },
      { status: 500 }
    );
  }
}
