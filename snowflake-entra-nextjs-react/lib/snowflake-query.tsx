import { appInsights } from '@/components/appInsights';
import type { RowData, SnowflakeResponse } from "@/lib/types";

export async function snowflakeQuery(sql_statement: string, token: string): Promise<SnowflakeResponse> {
    try {
        const snowflakeInstance = process.env.NEXT_PUBLIC_SNOWFLAKE_INSTANCE;
        const snowflakeDB = process.env.NEXT_PUBLIC_SNOWFLAKE_DB;
        const snowflakeSchema = process.env.NEXT_PUBLIC_SNOWFLAKE_SCHEMA;
        const snowflakeWarehouse = process.env.NEXT_PUBLIC_SNOWFLAKE_WAREHOUSE;
        const snowflakeRole = process.env.NEXT_PUBLIC_SNOWFLAKE_ROLE;

        const url =`https://${snowflakeInstance}.snowflakecomputing.com/api/v2/statements`;

        appInsights.trackEvent({ name: `Snowflake query executing: ${url}`});

        const response = await fetch(url, {
            method: 'POST',
            headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
            },
            body: JSON.stringify({
                "statement": sql_statement,
                "timeout": 60,
                "database": `${snowflakeDB}`,
                "schema": `${snowflakeSchema}`,
                "warehouse": `${snowflakeWarehouse}`,
                "role": `${snowflakeRole}`
              })
        });

        const response_json = await response.json();

        if (response.status != 200) {
            appInsights.trackEvent({ name: `Snowflake query FAILED: ${response_json["message"] ?? null}`});
            return {
                success: false,
                status: response.status,
                sql_status: response_json["code"] ?? null,
                error: response_json["message"] ?? null,
                headings: null,
                data: null
            };
        } else {
            appInsights.trackEvent({ name: `Snowflake query SUCCESS: ${response_json["code"] ?? null}`});
            return {
                success: true,
                status: response.status,
                sql_status: response_json["code"] ?? null,
                error: null,
                headings: response_json["resultSetMetaData"] && response_json["resultSetMetaData"]["rowType"]
                    ? response_json["resultSetMetaData"]["rowType"].map((col: unknown) => (col as { name: string }).name) as string[]
                    : null,
                data: response_json["data"] as RowData[] || null,
            };
        }
    } catch (err) {
        appInsights.trackEvent({ name: `Snowflake query EXCEPTION: ${err}`});
        console.error("call failed:", err);
        let errorMessage: string;
        if (err instanceof Error) {
            errorMessage = err.message;
        } else if (typeof err === 'string') {
            errorMessage = err;
        } else {
            errorMessage = 'Unknown error';
        }
        return {
            success: false,
            status: -1,
            sql_status: null,
            error: errorMessage,
            headings: null,
            data: null
        };
    }
}
