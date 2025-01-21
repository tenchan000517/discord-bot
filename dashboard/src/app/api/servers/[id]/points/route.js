// C:\discord-gacha-bot\dashboard\src\app\api\servers\[id]\points\route.js
import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

// points/route.js
export async function PUT(request, { params }) {
    const { id: serverId } = await params;
    const session = await getServerSession(authOptions);

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const { userId, points, unitId } = await request.json();

        const aws = new AWSWrapper();
        const response = await aws.updateUserPoints(serverId, userId, points, unitId);

        return NextResponse.json({
            success: true,
            data: response
        });
    } catch (error) {
        console.error('Detailed API Error:', error);
        return NextResponse.json(
            { error: error.message || 'Internal server error' },
            { status: 500 }
        );
    }
}