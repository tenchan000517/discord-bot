import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export async function PUT(request, { params }) {
    try {
        const session = await getServerSession(authOptions);
        if (!session) {
            return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
        }

        const { id: serverId } = await params;
        if (!serverId) {
            return NextResponse.json({ message: "Server ID is required" }, { status: 400 });
        }

        const body = await request.json();
        const aws = new AWSWrapper();

        // リクエストデータのバリデーション
        if (!body) {
            return NextResponse.json({ message: "Request body is required" }, { status: 400 });
        }

        // ruleIdの取得（URLクエリパラメータまたはボディから）
        const ruleId = body.ruleId || null;

        try {
            const result = await aws.updateAutomationRule(serverId, ruleId, body);
            return NextResponse.json(result);
        } catch (error) {
            console.error('Error updating automation rule:', error);
            return NextResponse.json({ 
                message: error.message || 'Failed to update automation rule'
            }, { status: 400 });
        }
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json({ message: error.message }, { status: 500 });
    }
}

export async function GET(request, { params }) {
    try {
        const session = await getServerSession(authOptions);
        if (!session) {
            return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
        }

        const { id: serverId } = await params;
        if (!serverId) {
            return NextResponse.json({ message: "Server ID is required" }, { status: 400 });
        }

        const aws = new AWSWrapper();
        const rules = await aws.getAutomationRules(serverId);
        const history = await aws.getAutomationHistory(serverId, 10);

        return NextResponse.json({ rules, history });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json({ message: error.message }, { status: 500 });
    }
}

export async function POST(request, { params }) {
    try {
        const session = await getServerSession(authOptions);
        if (!session) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const { id: serverId } = await params;
        if (!serverId) {
            return NextResponse.json({ error: "Server ID is required" }, { status: 400 });
        }

        const body = await request.json();
        const aws = new AWSWrapper();
        const result = await aws.createAutomationRule(serverId, body);

        return NextResponse.json({
            success: true,
            data: result
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: error.message || 'Internal server error' },
            { status: 500 }
        );
    }
}

export async function DELETE(request, { params }) {
    try {
        const session = await getServerSession(authOptions);
        if (!session) {
            return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
        }

        const { id: serverId } = await params;
        if (!serverId) {
            return NextResponse.json({ error: "Server ID is required" }, { status: 400 });
        }

        const { searchParams } = new URL(request.url);
        const ruleId = searchParams.get('ruleId');

        if (!ruleId) {
            return NextResponse.json(
                { error: "Rule ID is required" },
                { status: 400 }
            );
        }

        const aws = new AWSWrapper();
        await aws.deleteAutomationRule(serverId, ruleId);

        return NextResponse.json({
            success: true,
            message: 'Rule deleted successfully'
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: error.message || 'Internal server error' },
            { status: 500 }
        );
    }
}