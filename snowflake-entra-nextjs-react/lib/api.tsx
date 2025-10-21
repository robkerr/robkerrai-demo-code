import { appInsights } from '@/components/appInsights';

export async function get_query(token: string): Promise<string> {
        return "SELECT PRODUCT, STATUS, REGION, SEGMENT, AMOUNT_USD FROM DW.PUBLIC.FORECAST"
}
