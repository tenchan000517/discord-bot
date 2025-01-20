import { NextResponse } from 'next/server';
import { AWSWrapper } from '@/utils/aws';
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";

// キャッシュ管理
const userCache = new Map();
const cacheExpiry = new Map();
const CACHE_DURATION_MS = 60 * 60 * 1000; // 1時間

// キャッシュからユーザー情報を取得、またはDiscord APIを呼び出し
async function getCachedUserInfo(userId, serverId) {
    const cacheKey = `${serverId}-${userId}`;
    const now = Date.now();

    // 有効期限の確認
    if (cacheExpiry.has(cacheKey) && cacheExpiry.get(cacheKey) < now) {
        console.log(`Cache expired for user: ${cacheKey}`);
        userCache.delete(cacheKey);
        cacheExpiry.delete(cacheKey);
    }

    // キャッシュがあれば利用
    if (userCache.has(cacheKey)) {
        console.log(`Cache hit for user: ${cacheKey}`);
        return userCache.get(cacheKey);
    }

    // Discord APIからデータを取得
    console.log(`Fetching user info for: ${cacheKey}`);
    const userResponse = await fetch(
        `https://discord.com/api/v10/guilds/${serverId}/members/${userId}`,
        {
            headers: {
                Authorization: `Bot ${process.env.DISCORD_BOT_TOKEN}`,
            },
        }
    );

    if (userResponse.ok) {
        const member = await userResponse.json();
        const userData = {
            displayName: member.nick || member.user?.username,
            avatar: member.user?.avatar,
        };

        // キャッシュに保存
        userCache.set(cacheKey, userData);
        cacheExpiry.set(cacheKey, now + CACHE_DURATION_MS);
        return userData;
    }

    console.warn(`Failed to fetch user info for: ${cacheKey}`);
    return null; // フォールバック
}

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
        console.log('Initial Server Data:', serverData);

        // Gacha設定の補完
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
            const cachedUserData = await getCachedUserInfo(user.user_id, id);
            return {
                ...user,
                displayName: cachedUserData?.displayName || cachedUserData?.username || user.displayName, // usernameを優先
                avatar: cachedUserData?.avatar || user.avatar,
            };
        });

        const enhancedRankings = await Promise.all(userPromises);
        // console.log('Enhanced Rankings:', enhancedRankings);

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
