// src/utils/aws.js
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import {
    DynamoDBDocumentClient,
    GetCommand,
    QueryCommand,
    ScanCommand,
    UpdateCommand,
    PutCommand
} from "@aws-sdk/lib-dynamodb";

export class AWSWrapper {
    constructor() {
        this.client = new DynamoDBClient({
            region: 'ap-northeast-1',
            credentials: {
                accessKeyId: process.env.AWS_ACCESS_KEY_ID,
                secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
            },
        });
        this.docClient = DynamoDBDocumentClient.from(this.client);
    }

    async getServerSettings(serverId) {
        try {
            const command = new GetCommand({
                TableName: 'server_settings',
                Key: {
                    server_id: serverId
                }
            });
            const response = await this.docClient.send(command);

            // デフォルトの設定構造
            const defaultSettings = {
                server_id: serverId,
                global_settings: {
                    point_unit: 'ポイント',
                    timezone: 'Asia/Tokyo',
                    language: 'ja'
                },
                feature_settings: {
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
                },
                version: 1,
                last_modified: new Date().toISOString()
            };

            if (!response.Item) {
                return defaultSettings;
            }

            // 入れ子になった構造を修正
            const feature_settings = response.Item.feature_settings?.feature_settings ||
                response.Item.feature_settings ||
                defaultSettings.feature_settings;

            // 正規化された構造を返す
            const settings = {
                ...defaultSettings,
                ...response.Item,
                feature_settings: {
                    ...defaultSettings.feature_settings,
                    ...feature_settings
                }
            };

            // global_settings が feature_settings の中にある場合は削除
            if (settings.feature_settings.global_settings) {
                delete settings.feature_settings.global_settings;
            }

            console.log('Normalized Server Settings:', settings);
            console.log("Normalized Feature Settings:", JSON.stringify(feature_settings, null, 2));
            console.log("Normalized Server Settings:", JSON.stringify(settings, null, 2));

            return settings;
        } catch (error) {
            console.error("Error getting server settings:", error);
            throw error;
        }
    }

    async getServerRankings(serverId, limit = 10) {
        try {
            const command = new QueryCommand({
                TableName: 'discord_users',
                IndexName: 'ServerIndex',
                KeyConditionExpression: 'server_id = :sid',
                ExpressionAttributeValues: {
                    ':sid': serverId
                },
                Limit: limit
            });
            const response = await this.docClient.send(command);
            return response.Items;
        } catch (error) {
            console.error("Error getting server rankings:", error);
            throw error;
        }
    }

    async getServerData(serverId) {
        try {
            const [settings, rankings] = await Promise.all([
                this.getServerSettings(serverId),
                this.getServerRankings(serverId)
            ]);

            return {
                settings,
                rankings: rankings.sort((a, b) =>
                    (b.points?.total || 0) - (a.points?.total || 0)
                )
            };
        } catch (error) {
            console.error("Error getting server data:", error);
            throw error;
        }
    }

    // 既存のAWSWrapperクラスに追加
    async getAllServerIds() {
        try {
            const command = new ScanCommand({
                TableName: "server_settings",
                ProjectionExpression: "server_id"
            });

            const response = await this.docClient.send(command);
            return response.Items.map(item => item.server_id);
        } catch (error) {
            console.error("Error getting all server IDs:", error);
            throw error;
        }
    }

    // サーバー設定の更新
    async updateServerSettings(serverId, settings) {
        try {
            const command = new UpdateCommand({
                TableName: 'server_settings',
                Key: {
                    server_id: serverId
                },
                UpdateExpression: 'SET global_settings = :gs, version = :v, last_modified = :lm',
                ExpressionAttributeValues: {
                    ':gs': settings.global_settings,
                    ':v': settings.version || 1,
                    ':lm': new Date().toISOString()
                },
                ReturnValues: 'ALL_NEW'
            });

            const response = await this.docClient.send(command);
            return response.Attributes;
        } catch (error) {
            console.error("Error updating server settings:", error);
            throw error;
        }
    }

    // 機能設定の更新
    async updateFeatureSettings(serverId, featureSettings) {
        try {
            const command = new UpdateCommand({
                TableName: 'server_settings',
                Key: {
                    server_id: serverId
                },
                UpdateExpression: 'SET feature_settings = :fs, version = :v, last_modified = :lm',
                ExpressionAttributeValues: {
                    ':fs': featureSettings,
                    ':v': featureSettings.version || 1,
                    ':lm': new Date().toISOString()
                },
                ReturnValues: 'ALL_NEW'
            });

            const response = await this.docClient.send(command);
            return response.Attributes;
        } catch (error) {
            console.error("Error updating feature settings:", error);
            throw error;
        }
    }

    // ユーザーポイントの更新
    async updateUserPoints(serverId, userId, points) {
        try {
            const command = new UpdateCommand({
                TableName: 'discord_users',
                Key: {
                    server_id: serverId,
                    user_id: userId
                },
                UpdateExpression: 'SET points = :p, version = :v, last_modified = :lm',
                ExpressionAttributeValues: {
                    ':p': points,
                    ':v': points.version || 1,
                    ':lm': new Date().toISOString()
                },
                ReturnValues: 'ALL_NEW'
            });

            const response = await this.docClient.send(command);
            return response.Attributes;
        } catch (error) {
            console.error("Error updating user points:", error);
            throw error;
        }
    }

    // バッチ更新処理（CSVインポート用）
    async batchUpdateSettings(serverId, settings) {
        try {
            const command = new PutCommand({
                TableName: 'server_settings',
                Item: {
                    ...settings,
                    server_id: serverId,
                    version: settings.version || 1,
                    last_modified: new Date().toISOString()
                }
            });

            const response = await this.docClient.send(command);
            return response;
        } catch (error) {
            console.error("Error batch updating settings:", error);
            throw error;
        }
    }

    // 履歴の保存（監査ログ用）
    async saveAuditLog(serverId, action, data, userId) {
        try {
            const command = new PutCommand({
                TableName: 'audit_logs',
                Item: {
                    server_id: serverId,
                    timestamp: new Date().toISOString(),
                    action,
                    data,
                    user_id: userId
                }
            });

            const response = await this.docClient.send(command);
            return response;
        } catch (error) {
            console.error("Error saving audit log:", error);
            throw error;
        }
    }
}

export default AWSWrapper;