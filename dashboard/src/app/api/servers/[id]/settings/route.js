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
        console.log("Fetching server data from AWS..."); // AWSデータ取得ログ
        const serverData = await aws.getServerData(id);

        // AWSデータ詳細ログ
        console.log("AWS Server Data Response:", JSON.stringify(serverData, null, 2));

        // サーバーデータのチェックと補完
        if (!serverData.settings.feature_settings) {
            console.warn("Feature settings missing. Applying defaults...");
            serverData.settings.feature_settings = {
                battle: {
                    enabled: false,
                    points_per_kill: 0,
                    winner_points: 0,
                    start_delay_minutes: 0
                },
                gacha: {
                    enabled: false,
                    items: [],
                    messages: {
                        setup: 'Default setup message',
                        daily: 'Default daily message',
                        win: 'Default win message',
                        custom_messages: {}
                    },
                    media: {
                        setup_image: 'https://default.setup.image/url',
                        banner_gif: 'https://default.banner.gif/url'
                    }
                },
                fortune: {
                    enabled: false
                }
            };
        }

        // Gacha設定補完
        if (serverData.settings.feature_settings.gacha) {
            const gachaSettings = serverData.settings.feature_settings.gacha;

            console.log("Before Gacha Completion:", JSON.stringify(gachaSettings, null, 2)); // 補完前ログ

            // messages と media の補完処理
            gachaSettings.messages = gachaSettings.messages || {
                setup: 'Default setup message',
                daily: 'Default daily message',
                win: 'Default win message',
                custom_messages: {}
            };

            gachaSettings.media = gachaSettings.media || {
                setup_image: 'https://default.setup.image/url',
                banner_gif: 'https://default.banner.gif/url'
            };

            console.log("After Gacha Completion:", JSON.stringify(gachaSettings, null, 2)); // 補完後ログ
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
            
            // ガチャ設定の補完処理を追加
            if (settings.feature_settings.gacha) {
                settings.feature_settings.gacha = {
                    ...settings.feature_settings.gacha,
                    messages: settings.feature_settings.gacha.messages || {
                        setup: 'Default setup message',
                        daily: 'Default daily message',
                        win: 'Default win message',
                        custom_messages: {}
                    },
                    media: settings.feature_settings.gacha.media || {
                        setup_image: '',
                        banner_gif: ''
                    }
                };
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
