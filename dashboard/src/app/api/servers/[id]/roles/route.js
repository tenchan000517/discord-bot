// src/app/api/servers/[id]/roles/route.js
import { NextResponse } from 'next/server';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export async function GET(request, { params }) {
    const { id } = await params;  // awaitを追加

    const session = await getServerSession(authOptions);
    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const response = await fetch(`https://discord.com/api/v10/guilds/${id}/roles`, {
            headers: {
                Authorization: `Bot ${process.env.DISCORD_BOT_TOKEN}`,
            },
        });

        if (!response.ok) {
            throw new Error('Failed to fetch roles from Discord');
        }

        const roles = await response.json();
        const filteredRoles = roles
            .filter(role => role.name !== '@everyone')
            .map(role => ({
                id: role.id,
                name: role.name,
                color: role.color,
                position: role.position
            }))
            .sort((a, b) => b.position - a.position);

        return NextResponse.json({ roles: filteredRoles });
    } catch (error) {
        console.error('Error fetching roles:', error);
        return NextResponse.json(
            { error: 'Failed to fetch roles' },
            { status: 500 }
        );
    }
}