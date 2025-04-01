# 常量定义
FEISHU_HOST = "https://open.feishu.cn"


TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
BITABLE_RECORDS = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records"

# 查询记录文档：https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/search
BITABLE_RECORDS_SEARCH = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/search"
BITABLE_RECORD = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/:record_id"

# 批量获取记录 https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/batch_get
BATCH_RECORDS = "https://open.feishu.cn/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_get"


# 列出字段 https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/update
TABLES_FIELDS = '/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields/:field_id'