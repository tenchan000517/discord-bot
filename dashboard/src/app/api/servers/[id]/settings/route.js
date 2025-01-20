import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

export async function GET(request, { params }) {
    const { id } = await params;

    console.log("Request received for server ID:", id); // リクエスト受付ログ

    // セッションチェック
    const session = await getServerSession(authOptions);
    console.log("Session details:", session ? "Valid session" : "No session"); // セッションログ

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const aws = new AWSWrapper();
        const serverData = await aws.getServerData(id);

        // ガチャ設定の構造チェックと変換
        if (serverData.settings?.feature_settings?.gacha) {
            const gachaSettings = serverData.settings.feature_settings.gacha;
            let needsUpdate = false;
                    
            if (gachaSettings.gacha_list) {
                // channel_idが存在するのにガチャIDが違うものを修正
                serverData.settings.feature_settings.gacha.gacha_list = gachaSettings.gacha_list
                    .filter((gacha, index, self) => 
                        // channel_idが設定されている場合、そのチャンネルの最初のガチャのみ残す
                        gacha.channel_id ? 
                            index === self.findIndex(g => g.channel_id === gacha.channel_id) : 
                            true
                    )
                    .map(gacha => {
                        if (gacha.channel_id) {
                            // チャンネルIDが存在する場合、名前を更新
                            const updatedGacha = {
                                ...gacha,
                                gacha_id: gacha.channel_id, // channel_idをガチャIDとして使用
                                name: gacha.name === "デフォルトガチャ" ? 
                                    `デフォルトガチャ (${gacha.channel_id})` : 
                                    gacha.name
                            };
                            needsUpdate = true;
                            return updatedGacha;
                        }
                        return gacha;
                    });
            }

            if (needsUpdate) {
                await aws.updateFeatureSettings(id, serverData.settings.feature_settings);
                console.log("Cleaned up and updated gacha settings");
            }
        }

        // Discordからユーザー情報を取得
        console.log("Fetching user details from Discord API...");
        const userPromises = serverData.rankings?.map(async (user) => {
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

        const enhancedRankings = userPromises ? await Promise.all(userPromises) : [];
        console.log("Enhanced Rankings:", JSON.stringify(enhancedRankings, null, 2)); // ランキングログ

        // 最終レスポンス生成
        const response = {
            settings: serverData.settings,
            rankings: enhancedRankings
        };

        console.log("Final Response:", JSON.stringify(response, null, 2)); // レスポンスログ

        return NextResponse.json(response);
    } catch (error) {
        console.error('API Error:', error); // エラーログ
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
    const { id } = await params;

    console.log("Request received for PUT on server ID:", id); // リクエストログ

    // セッションチェック
    const session = await getServerSession(authOptions);
    console.log("Session details:", session ? "Valid session" : "No session"); // セッションログ

    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const aws = new AWSWrapper();
        const body = await request.json();
        const { section, settings } = body;

        console.log("PUT request body:", JSON.stringify(body, null, 2)); // リクエストボディログ

        let response;
        if (section === 'server-settings') {
            console.log("Updating server settings...");
            response = await aws.updateServerSettings(id, settings);
        } else if (section === 'feature-settings') {
            console.log("Updating feature settings...");
            
            // ガチャ設定の構造を維持
            if (settings.feature_settings?.gacha) {
                const gachaSettings = settings.feature_settings.gacha;
                if (!gachaSettings.gacha_list) {
                    // 古い形式のデータを新しい形式に変換して保存
                    const channelId = settings.channel_id || "default";
                    settings.feature_settings.gacha = {
                        ...gachaSettings,
                        gacha_list: [{
                            gacha_id: channelId,
                            name: `デフォルトガチャ (${channelId})`, // チャンネルIDを名前に追加
                            enabled: gachaSettings.enabled ?? false,
                            items: gachaSettings.items || [],
                            messages: gachaSettings.messages || {},
                            media: gachaSettings.media || {}
                        }]
                    };
                }
            }
            
            response = await aws.updateFeatureSettings(id, settings.feature_settings);
        
        } else {
            console.error("Invalid section specified:", section);
            return NextResponse.json({ error: "Invalid section" }, { status: 400 });
        }

        console.log("Update Response:", JSON.stringify(response, null, 2)); // 更新結果ログ

        return NextResponse.json({
            success: true,
            data: response
        });
    } catch (error) {
        console.error('API Error:', error); // エラーログ
        return NextResponse.json(
            { 
                error: 'Internal server error',
                details: error.message
            },
            { status: 500 }
        );
    }
}

export async function DELETE(request, { params }) {
    const { id } = params;
    const { searchParams } = new URL(request.url);
    const gachaId = searchParams.get('gachaId');

    console.log("Delete request received for gacha ID:", gachaId, "in server:", id);

    // セッションチェック
    const session = await getServerSession(authOptions);
    if (!session) {
        return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    try {
        const aws = new AWSWrapper();
        const serverData = await aws.getServerData(id);

        if (!serverData.settings?.feature_settings?.gacha?.gacha_list) {
            return NextResponse.json({ error: "Gacha settings not found" }, { status: 404 });
        }

        // ガチャリストから指定されたガチャを除外
        const updatedGachaList = serverData.settings.feature_settings.gacha.gacha_list
            .filter(gacha => gacha.gacha_id !== gachaId);

        // 更新されたガチャリストで設定を更新
        serverData.settings.feature_settings.gacha.gacha_list = updatedGachaList;
        
        await aws.updateFeatureSettings(id, serverData.settings.feature_settings);

        return NextResponse.json({
            success: true,
            message: "Gacha deleted successfully"
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