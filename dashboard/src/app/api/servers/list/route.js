// app/api/servers/list/route.js
import { getServerSession } from "next-auth";
import { NextResponse } from "next/server";
import { AWSWrapper } from "@/utils/aws";
import { authOptions } from "../../auth/[...nextauth]/route";

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Discord APIからユーザーのサーバー一覧を取得（レートリミット対応）
const fetchDiscordServers = async (session, retryCount = 0) => {
  const response = await fetch("https://discord.com/api/v10/users/@me/guilds", {
    headers: {
      Authorization: `Bearer ${session.accessToken}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    
    if (error.retry_after && retryCount < 3) {
      console.log(`Rate limited, waiting ${error.retry_after}s before retry...`);
      await sleep(error.retry_after * 1000);
      return fetchDiscordServers(session, retryCount + 1);
    }

    console.error("Discord API Error:", error);
    throw new Error(error.message || "Failed to fetch Discord servers");
  }

  return response.json();
};

export async function GET() {
  const session = await getServerSession(authOptions);
  console.log("Session data:", {
    accessToken: session?.accessToken ? "exists" : "missing",
    user: session?.user
  });
  
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const userGuilds = await fetchDiscordServers(session);
    console.log("Discord Guilds:", userGuilds);

    const aws = new AWSWrapper();
    const botServers = await aws.getAllServerIds();
    console.log("Bot Server IDs:", botServers);

    // 権限チェックの詳細をログ出力
    const availableServers = userGuilds.filter(guild => {
      const isInBotServers = botServers.includes(guild.id);
      const hasAdminPermission = (BigInt(guild.permissions) & BigInt(0x8)) === BigInt(0x8);
      
      console.log(`Server ${guild.name} (${guild.id}):`, {
        isInBotServers,
        hasAdminPermission,
        permissions: guild.permissions
      });
      
      return isInBotServers && hasAdminPermission;
    });

    console.log("Final available servers:", availableServers);

    return NextResponse.json({ 
      servers: availableServers.map(guild => ({
        id: guild.id,
        name: guild.name,
        icon: guild.icon,
      }))
    });

  } catch (error) {
    console.error("Detailed error:", {
      message: error.message,
      stack: error.stack
    });
    return NextResponse.json(
      { error: error.message || "Failed to fetch servers" },
      { status: 500 }
    );
  }
}