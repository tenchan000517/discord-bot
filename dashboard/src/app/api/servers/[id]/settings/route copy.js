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

        // 詳細なデータ構造のログ出力
        console.log('AWS Response Details:', {
            hasSettings: !!serverData?.settings,
            settingsKeys: Object.keys(serverData?.settings || {}),
            hasFeatureSettings: !!serverData?.settings?.feature_settings,
            featureSettingsKeys: Object.keys(serverData?.settings?.feature_settings || {}),
            rawFeatureSettings: JSON.stringify(serverData?.settings?.feature_settings, null, 2),
            rawSettings: JSON.stringify(serverData?.settings, null, 2),
            fullData: JSON.stringify(serverData, null, 2)
        });

        console.log("AWS Server Data Response:", JSON.stringify(serverData, null, 2));

        // データの構造が正しくない場合のデフォルト値設定
        if (!serverData.settings.feature_settings) {
            serverData.settings.feature_settings = {
                battle: {
                    enabled: false,
                    points_per_kill: 0,
                    winner_points: 0,
                    start_delay_minutes: 0
                },
                gacha: {
                    enabled: false,
                    items: []
                },
                fortune: {
                    enabled: false
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

                if (!userResponse.ok) {
                    console.error(`Failed to fetch user ${user.user_id}: ${userResponse.status}`);
                    return user;
                }

                const member = await userResponse.json();
                return {
                    ...user,
                    displayName: member.nick || member.user?.username,
                    avatar: member.user?.avatar
                };
            } catch (error) {
                console.error(`Error fetching user ${user.user_id}:`, error);
                return user;
            }
        });

        const enhancedRankings = await Promise.all(userPromises);

        // レスポンスを返す前に構造を確認
        const response = {
            settings: serverData.settings,
            rankings: enhancedRankings
        };

        console.log('Final Response:', {
            hasSettings: !!response.settings,
            hasFeatureSettings: !!response.settings?.feature_settings,
            featureSettingsKeys: Object.keys(response.settings?.feature_settings || {}),
            rawResponse: JSON.stringify(response, null, 2)
        });

        return NextResponse.json(response);
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { 
                error: 'Internal server error',
                details: error.message
            },
            { status: 500 }
        );
    }
}

export async function PUT(request, { params }) {
    const { id } = await params;  // 正しい書き方
    
    // セッションチェック
    const session = await getServerSession(authOptions);
    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const aws = new AWSWrapper();
        const body = await request.json();
        const { section, settings } = body;

        let response;
        if (section === 'server-settings') {
            response = await aws.updateServerSettings(id, settings);
        } else if (section === 'feature-settings') {
            response = await aws.updateFeatureSettings(id, settings.feature_settings);
        } else {
            return NextResponse.json({ error: "Invalid section" }, { status: 400 });
        }

        return NextResponse.json({
            success: true,
            data: response
        });
    } catch (error) {
        console.error('API Error:', error);
        return NextResponse.json(
            { 
                error: 'Internal server error',
                details: error.message
            },
            { status: 500 }
        );
    }
}