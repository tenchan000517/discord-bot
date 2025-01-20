// src/app/api/servers/[id]/points/consumption/route.js
import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export async function GET(request, { params }) {
    const { id } = params;
    const session = await getServerSession(authOptions);

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const aws = new AWSWrapper();
        const history = await aws.getPointConsumptionHistory(id);

        return NextResponse.json({
            success: true,
            data: history
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}

export async function POST(request, { params }) {
    const { id } = params;
    const session = await getServerSession(authOptions);

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const body = await request.json();
        const { user_id, points, thread_id } = body;

        const aws = new AWSWrapper();
        const request = await aws.createConsumptionRequest(id, user_id, points, thread_id);

        return NextResponse.json({
            success: true,
            data: request
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}

export async function PUT(request, { params }) {
    const { id } = params;
    const session = await getServerSession(authOptions);

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const body = await request.json();
        const { timestamp, status, admin_id, reason } = body;

        const aws = new AWSWrapper();
        const result = await aws.updateConsumptionStatus(id, timestamp, status, admin_id, reason);

        return NextResponse.json({
            success: true,
            data: result
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}