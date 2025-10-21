

export type VerifyLoginResult = {
    success: boolean;
    message: string;
    displayName: string;
};
export interface RowData {
    [key: string]: string | number | boolean | null | undefined | object | Array<unknown>;
}

export type SnowflakeResponse = {
    success: boolean;
    status: number;
    sql_status: string | null;
    error: string | null;
    headings: string[] | null;
    data: RowData[] | null;
};

export interface ScrollableDataTableProps {
    headings: string[];
    data: RowData[];
    className?: string;
}
