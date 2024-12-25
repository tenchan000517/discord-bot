// src/app/api/servers/[id]/channels/route.js
import { NextResponse } from 'next/server';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export async function GET(request, { params }) {
    try {
        const session = await getServerSession(authOptions);
        if (!session) {
            return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
        }

        const { id: serverId } = await params; // 非同期で params を取得
        if (!serverId) {
            return NextResponse.json({ message: "Server ID is required" }, { status: 400 });
        }

        // Discord APIからチャンネル一覧を取得
        const response = await fetch(`https://discord.com/api/v10/guilds/${serverId}/channels`, {
            headers: {
                Authorization: `Bot ${process.env.DISCORD_BOT_TOKEN}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch channels from Discord');
        }

        const channels = await response.json();
        
        // テキストチャンネルのみをフィルタリング
        const textChannels = channels.filter(channel => channel.type === 0).map(channel => ({
            id: channel.id,
            name: channel.name,
            type: channel.type,
            position: channel.position
        }));

        return NextResponse.json({ channels: textChannels });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json({ message: error.message }, { status: 500 });
    }
}
