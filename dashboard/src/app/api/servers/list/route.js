// app/api/servers/list/route.js
import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { AWSWrapper } from "@/utils/aws";
import { authOptions } from "../../auth/[...nextauth]/route";

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export async function GET() {
  const session = await getServerSession(authOptions);
  
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    // Discord APIからユーザーのサーバー一覧を取得（レートリミット対応）
    const fetchDiscordServers = async (retryCount = 0) => {
      const response = await fetch("https://discord.com/api/v10/users/@me/guilds", {
        headers: {
          Authorization: `Bearer ${session.accessToken}`,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        
        // レートリミットの場合
        if (error.retry_after && retryCount < 3) {
          console.log(`Rate limited, waiting ${error.retry_after}s before retry...`);
          // retry_afterは秒単位なのでミリ秒に変換
          await sleep(error.retry_after * 1000);
          return fetchDiscordServers(retryCount + 1);
        }

        console.error("Discord API Error:", error);
        throw new Error(error.message || "Failed to fetch Discord servers");
      }

      return response.json();
    };

    const userGuilds = await fetchDiscordServers();
    
    // ボットが導入されているサーバー一覧を取得
    const aws = new AWSWrapper();
    const botServers = await aws.getAllServerIds();

    // 両方に存在するサーバーのみをフィルタリング
    const availableServers = userGuilds.filter(guild => 
      botServers.includes(guild.id) && 
      (BigInt(guild.permissions) & BigInt(0x8)) === BigInt(0x8)  // 管理者権限チェック
    );

    return NextResponse.json({ 
      servers: availableServers.map(guild => ({
        id: guild.id,
        name: guild.name,
        icon: guild.icon,
      }))
    });

  } catch (error) {
    console.error("Server list error:", error);
    return NextResponse.json(
      { error: error.message || "Failed to fetch servers" },
      { status: 500 }
    );
  }
}