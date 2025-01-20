// C:\discord-gacha-bot\dashboard\src\app\api\servers\[id]\points\route.js
import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

// points/route.js の修正案
export async function PUT(request, { params }) {

    const { id } = await params;
    const session = await getServerSession(authOptions); // これを追加すべき

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {

        const body = await request.json();
        console.log('API received:', body); // デバッグログ追加

        const { user_id, points, unit_id } = body;

        // AWS Wrapperに渡す前にデータ構造を確認
        console.log('Sending to AWS:', { id, user_id, points, unit_id }); // デバッグログ追加

        const aws = new AWSWrapper();
        const response = await aws.updateUserPoints(id, user_id, points, unit_id);

        return NextResponse.json({
            success: true,
            data: response
        });
    } catch (error) {
        // エラーの詳細をログに出力
        console.error('Detailed API Error:', error);
        return NextResponse.json(
            { error: error.message || 'Internal server error' },
            { status: 500 }
        );
    }
}