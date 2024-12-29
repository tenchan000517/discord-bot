// C:\discord-gacha-bot\dashboard\src\app\api\servers\[id]\points\route.js
import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export async function PUT(request, { params }) {
    const { id } = await params;
    const session = await getServerSession(authOptions);

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const body = await request.json();
        console.log('Received data:', body); // デバッグログ

        const { user_id, points } = body;

        console.log('Type of points:', typeof points);

        const aws = new AWSWrapper();
        const response = await aws.updateUserPoints(id, user_id, points);

        return NextResponse.json({
            success: true,
            data: response
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}