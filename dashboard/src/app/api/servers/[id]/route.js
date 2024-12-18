import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export async function GET(request, { params }) {
    const { id } = await params;

    // セッションチェック
    const session = await getServerSession(authOptions);

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const aws = new AWSWrapper();
        const serverData = await aws.getServerData(id);
    
        // ここにログと補完コードを追加
        console.log('Normalized Server Settings Gacha:', JSON.stringify(serverData.settings.feature_settings.gacha, null, 2));
    
        if (serverData.settings.feature_settings.gacha) {
            serverData.settings.feature_settings.gacha = {
                ...serverData.settings.feature_settings.gacha,
                messages: serverData.settings.feature_settings.gacha.messages || {
                    setup: '',
                    daily: '',
                    win: '',
                    custom_messages: {}
                },
                media: serverData.settings.feature_settings.gacha.media || {
                    setup_image: '',
                    banner_gif: ''
                }
            };
        }

        // Discordからユーザー情報を取得
        const userPromises = serverData.rankings.map(async (user) => {
            try {
                const userResponse = await fetch(
                    `https://discord.com/api/v10/guilds/${id}/members/${user.user_id}`,
                    {
                        headers: {
                            Authorization: `Bot ${process.env.DISCORD_BOT_TOKEN}`,
                        },
                    }
                );

                if (userResponse.ok) {
                    const member = await userResponse.json();
                    return {
                        ...user,
                        displayName: member.nick || member.user?.username,
                        avatar: member.user?.avatar
                    };
                }
                return user;
            } catch (error) {
                console.error(`Error fetching user ${user.user_id}:`, error);
                return user;
            }
        });

        const enhancedRankings = await Promise.all(userPromises);

        return NextResponse.json({
            settings: serverData.settings,
            rankings: enhancedRankings
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { error: 'Internal server error' },
            { status: 500 }
        );
    }
}